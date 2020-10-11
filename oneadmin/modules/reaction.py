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
import types
import os
from pathlib import Path
from aiofile.aio import AIOFile
from tornado.ioloop import IOLoop
import json
from oneadmin.exceptions import FileSystemOperationError, RulesError
from oneadmin.modules.reactions.standard_reactions import http_reaction
from oneadmin.abstracts import Notifyable
import importlib
import inspect
import time
import asyncio
from oneadmin.modules.reactions.filesystem_reactions import write_log
from datetime import datetime
from croniter.croniter import croniter
from apscheduler.schedulers.tornado import TornadoScheduler
from reactions.filesystem_reactions import copy_file



class ReactionEngine(Notifyable):
    
    

    def __init__(self, conf, modules):
        '''
        Constructor
        '''
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
        self.__system__modules = modules
        self.__evaluator__modules={}
        self.__reaction__modules={}  
        self.__topics_of_intertest = set()
        self.__task_scheduler = TornadoScheduler()
            
        
        if modules.hasModule("file_manager"):
            self.file_manager = modules.getModule("file_manager")
            
        self._initialize()
        
    
    
    def _initialize(self):
        self.__rules = {}
        self.__events = Queue(maxsize=50)
        self.__task_scheduler.start();        
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__loadRules)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__index_evaluators)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__index_reactions)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__event_processor)
        
    
    
    def __register_timed_reaction(self, rule):
        
        try:
            time_object = rule["trigger"]["on-time-object"]
            if 'recurring' not in time_object or  time_object["recurring"] == False:            
                date_time_str = time_object["expression"]
                self.__task_scheduler.add_job(self.__respondToTimedEvent, 'date', run_date=date_time_str, args=[rule])
            else:    
                cron_str = time_object["expression"]
                if croniter.is_valid(cron_str):
                    self.task_scheduler.scheduleTaskByCronExpersssion(time_object, self.__respondToTimedEvent, rule)
                else:
                    raise Exception("Invalid cron expression " + str(cron_str))
        except Exception as e:  
                self.logger.error("Error registering timed event. " + str(e))
                
    
    
    def hello(self):
        print("hello")
        
        
        
    @property
    def system_modules(self):
        return self.__system__modules
    
    
    
    @system_modules.setter
    def system_modules(self, provider):
        self.__system__modules = provider
        
    
    '''
        Processes events from queue
    '''
    async def __event_processor(self):
        while True:
            try:
                event = await self.__events.get()
                tornado.ioloop.IOLoop.current().spawn_callback(self.process_event_with_rules, event)
                self.__events.task_done()
            except Exception as e:  
                self.logger.error("Error processing event. " + str(e))
        pass
    
    
    
    '''
        Process event against each applicable rule
    '''
    async def process_event_with_rules(self, event):
        
        for ruleid, rule in self.__rules.items():
            if self.__canReactTo(rule, event):
                self.logger.info("Processing event %s for rule %s", str(event), ruleid)
                tornado.ioloop.IOLoop.current().spawn_callback(self.__respondToEvent, rule, event)



    async def __index_evaluators(self):
        
        self.logger.debug("Loading evaluators")
        
        try:
            path = os.path.join(os.path.dirname(__file__), "evaluators")

            self.logger.debug("listing evaluators directory %s", path)
            if os.path.exists(path):
                files = await IOLoop.current().run_in_executor(
                    None,
                    self.__list_directory_async, str(path)
                    ) 
                
                for name in files:
                    listing_path = Path(os.path.join(str(path), name))
                    if not listing_path.is_dir() and name != "__init__.py":
                        await IOLoop.current().run_in_executor(
                                None,
                                self.__import_module, name, str(listing_path), "evaluators"
                            ) 
            else:
                raise FileNotFoundError("File : " + path + " does not exist.")
            
        except Exception as e:
            err = "Unable to load one or more evaluator(s) " + str(e)
            self.logger.error(err)
        
        pass
    
    
    
    
    async def __index_reactions(self):            
            
        self.logger.debug("Loading reactions")
            
            
        try:
            path = os.path.join(os.path.dirname(__file__), "reactions")

            self.logger.debug("listing reactions directory %s", path)
            if os.path.exists(path):
                files = await IOLoop.current().run_in_executor(
                    None,
                    self.__list_directory_async, str(path)
                    ) 
                
                for name in files:
                    listing_path = Path(os.path.join(str(path), name))
                    if not listing_path.is_dir() and name != "__init__.py":
                        await IOLoop.current().run_in_executor(
                                None,
                                self.__import_module, name, str(listing_path), "reactions"
                            ) 
            else:
                raise FileNotFoundError("File : " + path + " does not exist.")
            
        except Exception as e:
            err = "Unable to load one or more reaction(s) " + str(e)
            self.logger.error(err)
            
        pass
    
    
    
    
    def __import_module(self, name, path, mod_type):
        name = name.split(".", 1)[0]
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        modules = None
        if mod_type == "evaluators":
            modules = self.__evaluator__modules
        elif mod_type == "reactions":
            modules = self.__reaction__modules
        else:
            raise("Invalid module type requested")
        
        
        if not name in modules:
            modules[name] = {}
            
            funcs = set()
            all_functions = inspect.getmembers(mod, inspect.isfunction)
            for func in all_functions:
                funcs.add(func[0])
            
            modules[name]["module"] = mod
            modules[name]["methods"] = funcs
            


    '''
        Loads reaction rules from filesystem
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
                        rule = await self.__readRule(listing_path)
                        
                        if rule["enabled"] != True:
                            continue
                        
                        self.registerRule(rule)
            else:
                raise FileNotFoundError("File : " + path + " does not exist.")
            
        except Exception as e:
            err = "Unable to load one or more rule(s) " + str(e)
            self.logger.error(err)
            raise RulesError(err)
    
    
    
    def create_rule(self, event, rule):
        self.registerRule(rule)
        
        
    
    def delete_rule(self, id):
        self.deregisterRule(id) 
               
        
    
    def registerRule(self, rule):
        
        try:
            
            rule["_responded_to"] = False
            
            self.__rules[rule["id"]] = rule
                            
            '''
            All {time} actions go to task scheduler
            '''
            if rule["listen-to"] == "{time}":
                self.__register_timed_reaction(rule)                                
                
            else:
                self.__topics_of_intertest.add(rule["listen-to"])
            
        except Exception as e:
            err = "Unable to register rule " + str(e)
            self.logger.error(err)
    
    
    
    def deregisterRule(self, id):
        if id in self.__rules and self.__rules[id] != None:
            del self.__rules[id]
            pass
    
    
    
    
                
    
    '''
        Reads rule data from file system for a rule file
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
        Reads and lists directory asynchronously
    '''
    def __list_directory_async(self, filepath):
        
        try:
            files = os.listdir(filepath)
            return files
        except Exception as e:    
            raise FileSystemOperationError("Unable to list path " + filepath + ".Cause " + str(e))
        pass
    
    
    
    '''
        Notifies an event to reaction engine 
    '''
    async def notifyEvent(self, event):
        
        topic = event["topic"]
        
        if topic in self.__topics_of_intertest:
            self.logger.debug("Adding event to list for processing " + str(event))
            await self.__events.put(event)
            pass     
                
            
            
                
    '''
        Determines if the reaction engine can react to an event based on rule condition 
    '''
    def __canReactTo(self, rule, event):
        
        if rule["listen-to"] == event["topic"]:
            
            if rule["trigger"]["on-payload-object"] == "*":
                return True
            elif rule["trigger"]["on-payload-object"] == "data":
                if rule["trigger"]["evaluator-func"] != None and rule["trigger"]["evaluator-func"] != "":
                    fun = rule["trigger"]["evaluator-func"]
                    func_parts = fun.split(".", 1)
                    mod_name = func_parts[0]
                    func_name = func_parts[1]
                    if mod_name in self.__evaluator__modules:
                        if "module" in self.__evaluator__modules[mod_name]:
                            module = self.__evaluator__modules[mod_name]["module"]
                            if isinstance(getattr(module, func_name), types.FunctionType):
                                toCall = getattr(module, func_name)
                                return toCall(event, rule) # must return boolean
                                pass
                            else:
                                raise ("Function " +fun + " was not found")
                            pass
                else:
                    self.logger.debug("evaluate locally and return boolean expression")
                    
                    if rule["trigger"]["using-condition"] == "equals":
                        if rule["trigger"]["on-content"] == "*":
                            return True
                        else:
                            return event["data"] == rule["trigger"]["on-content"]
                    elif rule["trigger"]["using-condition"] == "contains":
                        return str(event["data"]).find(str(rule["trigger"]["on-content"])) >= 0
                    else:
                        raise ("No evaluating condition found")
                pass
            
        return False
    
    
    
    
    '''
        Determines and executes appropriate reaction(s) to an event
    '''
    async def __respondToEvent(self, rule, event, auxdata=None):
        
        response_mode = rule["response"]["action"]
        response_fun = None if "reaction-func" not in rule["response"]  or  rule["response"]["reaction-func"] == 'null' else rule["response"]["reaction-func"]
        response_fun_params = None if "reaction-params" not in rule["response"]  or  rule["response"]["reaction-params"] == 'null' else rule["response"]["reaction-params"]
        
        
        if 'nonce' in rule["response"]:
            if rule["response"]["nonce"] == True: 
                if rule["_responded_to"] == False:
                    rule["_responded_to"] = True
                else:    
                    return
        else:
            rule["response"]["nonce"] = False
        
        
        if response_mode == "method":
            
            self.logger.debug("Call method")
            sys_module = False
            
            if '.' in response_fun:
                func_parts = response_fun.split(".", 1)
                mod_name = func_parts[0]
                func_name = func_parts[1]
                
                if mod_name in self.__reaction__modules:
                    if "module" in self.__reaction__modules[mod_name]:
                        module = self.__reaction__modules[mod_name]["module"]
                        if isinstance(getattr(module, func_name), types.FunctionType):
                            func = getattr(module, func_name)
                            funparams = self.__detokenize(response_fun_params)
                            await self.arbitrary_method_reaction(rule["id"], func, event, funparams)
                        else:
                            self.logger.error("Function " + response_fun + " was not found")
                    else:
                        self.logger.error("Module " + mod_name + " was not found")                 
            else:
                self.logger.error("Module not defined for function")
                
            
        elif response_mode == "delegate":
            self.logger.debug("Call delegate")
                        
            if self.__system__modules.hasModule('target_delegate'):
                await self.delegate_method_reaction(rule["id"], event, response_fun_params) 
            else:
                self.logger.info("Delegate if unavailable. Reaction call will be skipped for rule %s", rule["id"])
        
        elif response_mode == "http":
            
            self.logger.info("Call http handler")
            
            url = response_fun_params["url"]
            method = response_fun_params["method"]
            queryparams = response_fun_params["queryparams"]
            post_event_data = response_fun_params["post_event_data"]
            
            if post_event_data == True:
                await http_reaction(rule["id"], url, method, queryparams, event)
            else:
                await http_reaction(rule["id"], url, method, queryparams)
                        
        elif rule["response"]["action"] == "log_record":
            
            self.logger.debug("Call log_record handler")
            if self.file_manager is not None:
                await write_log(rule["id"], self.file_manager, response_fun_params, event)
            
        elif rule["response"]["action"] == "copy_file":
            
            self.logger.debug("Call copyfile handler")
            if self.file_manager is not None:
                await copy_file(rule["id"], self.file_manager, response_fun_params, event)
                
        
        elif rule["response"]["action"] == "create_rule":
            
            self.logger.debug("Call create_rule handler")
            new_rule = rule["response"]["reaction-params"]["rule-data"]
            self.registerRule(new_rule)
            
        
        elif rule["response"]["action"] == "delete_rule":
            
            self.logger.debug("Call create_rule handler")
            rule_id = rule["response"]["reaction-params"]["rule-data"]["id"]
            self.deregisterRule(rule_id)
                
        else:
            raise ("Invalid reaction type " + rule["response"]["action"])
        pass
        
    
    
    async def __respondToTimedEvent(self, rule, auxdata=None):
        await self.__respondToEvent(rule, "Scheduled", auxdata)
        pass
    
    
    '''
        Reaction to event via method call
    '''
    async def arbitrary_method_reaction(self, ruleid, func, event, exec_params):
        try:
            await func(event, exec_params)
        except Exception as e:
            self.logger.error("Error in method reaction for rule %s : %s ", ruleid, e)
        pass
    
    
    
    '''
        Reaction to event via method call on delegate
    '''
    async def delegate_method_reaction(self, ruleid, event, rparams=None):
        try:
            if self.__system__modules.hasModule('target_delegate'):
                delegate = self.__system__modules.getModule("target_delegate")
                await delegate.on_reaction(ruleid, event, rparams)
        except Exception as e:
            self.logger.error("Error in delegate method reaction for rule %s : %s ", ruleid, e)
        pass
    
        