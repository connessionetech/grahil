'''
This file is part of `Reactivity` 
Copyright 2018 Connessione Technologies

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from tornado.queues import Queue
import logging
import sys
import tornado
import os
from pathlib import Path
from aiofile.aio import AIOFile
from tornado.ioloop import IOLoop
import json
from oneadmin.exceptions import FileSystemOperationError, RulesError
from oneadmin.abstracts import IEventHandler
import asyncio
from datetime import datetime
from croniter.croniter import croniter
from apscheduler.schedulers.tornado import TornadoScheduler
from apscheduler.triggers.cron import CronTrigger
from abstracts import IEventDispatcher, IReactionEngine
from core.event import EventType, EVENT_STATS_GENERATED, EVENT_ANY,\
    EVENT_LOG_RECORDING_START, EVENT_LOG_RECORDING_STOP
from core.constants import TOPIC_ANY
from core.rules import ReactionRule, TimeTrigger, PayloadTrigger, RuleExecutionEvaluator, get_evaluator_by_name, RuleResponse, RuleState
from builtins import str
from core.components import ActionDispatcher



class ReactionEngine(IEventDispatcher, IEventHandler, IReactionEngine):
    
    

    def __init__(self, conf, action_dispatcher:ActionDispatcher=None):
        '''
        Constructor
        '''
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf          
        self.__topics_of_intertest = {}
        self.__rules = {}
        self.__events = Queue()
        self.__action_dispatcher = action_dispatcher
        self.__task_scheduler = TornadoScheduler()

        tornado.ioloop.IOLoop.current().spawn_callback(self.__initialize)
        
        
    
    
    def __initialize(self):
        
        if "topics_of_interest" in self.__conf:
            self.set_topics_of_interests(self.__conf["topics_of_interest"])
        
        if "events_of_interest" in self.__conf:
            self.set_events_of_interests(self.__conf["events_of_interest"])
        
        self.__task_scheduler.start()
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__loadRules)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__event_processor)
        
   
    
    
    '''
    Overridden to handle events subscribed to
    '''
    async def handleEvent(self, event:EventType):
        self.logger.debug(event["name"] + " received")
        await self.__events.put(event)
        pass
    
    

    '''
        Registers a time-rule
    '''    
    def __register_timed_reaction(self, rule:ReactionRule) ->None:
        
        try:
            trigger:TimeTrigger = rule.trigger
            
            if not trigger.recurring:            
                date_time_str:Text = trigger.time_expression
                self.__task_scheduler.add_job(self.__respondToTimedEvent, 'date', run_date=date_time_str, args=[rule])
            else:    
                cron_str:Text = trigger.time_expression
                if croniter.is_valid(cron_str):
                    trigger = CronTrigger.from_crontab(cron_str)
                    self.__task_scheduler.add_job(self.__respondToTimedEvent, trigger, args=[rule])
                else:
                    raise Exception("Invalid cron expression " + str(cron_str))
        except Exception as e:  
                self.logger.error("Error registering timed event. " + str(e))
    
        
    
    
    @property
    def action_dispatcher(self):
        return self.__action_dispatcher
    
    
    
    @action_dispatcher.setter
    def action_dispatcher(self, _dispatcher):
        self.__action_dispatcher = _dispatcher
    
    
    
    '''
        Processes events from queue
    '''
    async def __event_processor(self):
        while True:
            try:
                event:EventType = await self.__events.get()
                # always process events in parallel
                tornado.ioloop.IOLoop.current().spawn_callback(self.process_event_with_rules, event) 
            except Exception as e:  
                err = "Error processing event" + str(e)
                self.logger.error(err)
            finally:
                self.__events.task_done()
        pass
    
    
    
    '''
        Process event against each applicable rule
    '''
    async def process_event_with_rules(self, event:EventType):
        
        
        try:
        
            if event["name"] == EVENT_LOG_RECORDING_START:
                rule_data = event["data"]
                rule = self._parse_rule(rule_data)
                self.register_rule(rule)
                
            elif event["name"] == EVENT_LOG_RECORDING_STOP:
                rule_data = event["data"]
                self.deregister_rule(rule_data["id"])
            
            
            
            for ruleid, rule in self.__rules.items():
                if rule.is_applicable(event):
                    
                    evaluator:RuleExecutionEvaluator = rule.trigger.evaluator
                    
                    if evaluator:
                        evaluator.evaluate(event)
                    
                    self.logger.info("Processing event %s for rule %s", str(event), ruleid)
                    # always process multiple rules for 6the event in parallel
                    tornado.ioloop.IOLoop.current().spawn_callback(self.__respondToEvent, rule, event)
         
        except Exception as e:
            
            err = "Error processing event" + str(e)
            self.logger.error(err)
                


    '''
        Loads reaction rules from filesystem (v2.0)
    '''
    async def __loadRules(self):
        
        self.logger.debug("Loading rules")
        
        try:
            path = os.path.join(os.path.dirname(__file__), "rules")

            self.logger.debug("listing rules directory %s", path)
            if os.path.exists(path):
                files = await IOLoop.current().run_in_executor(
                    None,
                    self.__list_directory_async, str(path)
                    ) 
                
                for name in files:
                    listing_path = Path(os.path.join(str(path), name))
                    if not listing_path.is_dir():
                        rule_data = await self.__readRule(listing_path)
                        
                        if rule_data["enabled"] != True:
                            continue
                        
                        rule = self._parse_rule(rule_data)                        
                        self.register_rule(rule)
            else:
                raise FileNotFoundError("File : " + path + " does not exist.")
            
        except Exception as e:
            err = "Unable to load one or more rule(s) " + str(e)
            self.logger.error(err)
            raise RulesError(err)
        
        
    
    '''
    Parses rule data into  ReactionRule objects (v2.0)
    '''
    def _parse_rule(self, rule_data:dict) ->ReactionRule:
        
        rule:ReactionRule = ReactionRule()
        rule.id = rule_data["id"]
        rule.description = rule_data["description"]
        rule.enabled = rule_data["enabled"]
        rule.target_topic = rule_data["listen-to"]
        
        if "on-event" in rule_data:
                rule.target_event = rule_data["on-event"]
        
        trigger:Trigger = None
        trigger_evaluator:RuleExecutionEvaluator = None                      
        
        if "on-time-object" in rule_data["trigger"]:
            trigger = TimeTrigger()
            trigger.time_expression = rule_data["trigger"]["on-time-object"]["using-expression"]
            trigger.recurring = rule_data["trigger"]["on-time-object"]["recurring"]
            
        elif "on-payload-object" in rule_data["trigger"]:
            trigger = PayloadTrigger()
            trigger.payload_object_key = rule_data["trigger"]["on-payload-object"]["key"]
            trigger.expected_content = rule_data["trigger"]["on-payload-object"]["on-content"]
            trigger.condition_clause = rule_data["trigger"]["on-payload-object"]["on-condition"]
        
        else:
            raise ValueError("Unknown rule type")
        
        rule.trigger = trigger                        
        
        if "evaluator" in rule_data["trigger"]:
            evaluator_name = rule_data["trigger"]["evaluator"]
            if evaluator_name != None:
                trigger.evaluator = get_evaluator_by_name(evaluator_name.lower())
                                   
        response = RuleResponse()
        
        if not "intent" in rule_data["response"]:
            raise AttributeError("Rule response must have an `Intent`!")
        
        response.intent = rule_data["response"]["intent"]
        
        if "nonce" in rule_data["response"]:
            response.nonce = rule_data["response"]["nonce"]
        
        if "parameters" in rule_data["response"]:    
            response.parameters = rule_data["response"]["parameters"]
            
        
        rule.response = response
        
        return rule

        
    
    
    '''
        Check to see if rule exists by id (v2.0)
    '''     
    def has_rule(self, id:str)->bool:
        if id in self.__rules and self.__rules[id] != None:
            return True
        return False
            
        
                            
    '''
        Register rules for specified topic of interest (v2.0)
    '''    
    def register_rule(self, rule:ReactionRule) ->None:
        
        try:
            if isinstance(rule.trigger, TimeTrigger):
                self.__register_timed_reaction(rule)                                
                
            elif isinstance(rule.trigger, PayloadTrigger):
                
                num_rules_for_topic = 0
                
                if rule not in self.__topics_of_intertest:
                    num_rules_for_topic = 1
                    self.__topics_of_intertest[rule.target_topic] = {"num_rules": num_rules_for_topic} #Count how many rules for same topic
                else:
                    num_rules_for_topic = self.__topics_of_intertest[rule.target_topic]["num_rules"]
                    num_rules_for_topic = num_rules_for_topic + 1
                    self.__topics_of_intertest[rule.target_topic] = {"num_rules": num_rules_for_topic}
                    
                self.logger.info("Total rules for topic " + rule.target_topic + " = "  + str(num_rules_for_topic))  
            
            else:
                raise RulesError("Invalid rule " + str(rule))
            
            self.__rules[rule.id] = rule             
        
        except Exception as e:
            err = "Unable to register rule " + str(e)
            self.logger.error(err)
        
        finally:
            self.logger.info("Total topics " + str(len(self.__topics_of_intertest)))  
    
    
    
    '''
        Delete rule and topic of interest (v2.0)
    '''
    def deregister_rule(self, id:str)->None:
        if id in self.__rules and self.__rules[id] != None:
            try:
                rule:ReactionRule = self.__rules[id]
                
                num_rules_for_topic = self.__topics_of_intertest[rule.target_topic]["num_rules"]
                num_rules_for_topic = 0 if num_rules_for_topic <= 0 else num_rules_for_topic - 1
                
                if num_rules_for_topic == 0:
                    del self.__topics_of_intertest[rule.target_topic]
                else:
                    self.__topics_of_intertest[rule.target_topic]["num_rules"] = num_rules_for_topic
                
                self.logger.info("Total rules for topic " + rule.target_topic + " = "  + str(num_rules_for_topic))
            
            except Exception as e:
                err = "Unable to register rule " + str(e)
                self.logger.error(err)
        
            finally:
                del self.__rules[id]
                self.logger.info("Total topics " + str(len(self.__topics_of_intertest)))  
    
            
    
                
    
    '''
        Reads rule data from file system for a rule file (v2.0)
    '''
    async def __readRule(self, filepath):        
        
        file = Path(filepath)
        path = file.absolute()
        
        if file.exists():            
            if file.is_file():
                try:
                    async with AIOFile(str(path), "r") as afp:
                        content = await afp.read()
                        rule = json.loads(content)
                        return rule
                except:
                    raise FileSystemOperationError(sys.exc_info()[0] + "Could not read file " + filepath)
                finally:
                    pass
            else:
                raise FileSystemOperationError("Not a file " + str(filepath))
        else:
            raise FileNotFoundError("Invalid path " + path + " or file " + str(filepath) + " not found")
        
        pass
        
    
    
    
    '''
        Reads and lists directory asynchronously (to be moved to filemanager)
    '''
    def __list_directory_async(self, filepath):
        
        try:
            files = os.listdir(filepath)
            return files
        except Exception as e:    
            raise FileSystemOperationError("Unable to list path " + filepath + ".Cause " + str(e))
        pass
    
    
    
    
    '''
        Determines and executes appropriate reaction(s) to an event (v2.0)
    '''
    async def __respondToEvent(self, rule:ReactionRule, event:EventType, timed=False):
        
        response:RuleResponse =  rule.response
        
        try:
            if rule.state != RuleState.READY:
                raise RulesError("Rule cannot be eligible for execution")
            
            await self.__action_dispatcher.handle_request(None, response.intent, response.parameters, event)            
            
            if response.nonce:
                rule.state = RuleState.DONE
        
        except RulesError as e:
            return
        except Exception as e:
            self.logger.error("Error responding to event rule %s, Cause : %s ", rule.id, str(e))
        pass
        
        
    
    
    async def __respondToTimedEvent(self, rule:ReactionRule):
        await self.__respondToEvent(rule, None, timed=True)
        pass   
        