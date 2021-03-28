'''
This file is part of `Grahil` 
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

from oneadmin.responsebuilder import buildDataEvent
from oneadmin.utilities import buildTopicPath
from oneadmin.utilities import getLogFileKey
from oneadmin.communications import PubSubHub
#from oneadmin.modules.filesystem import FileManager
from oneadmin.core.grahil_core import ModuleRegistry
from oneadmin.core.constants import *
from oneadmin.core.components import ActionDispatcher, CommunicationHub
from oneadmin.core.constants import ACTION_DISPATCHER_MODULE, PROACTIVE_CLIENT_TYPE, REACTIVE_CLIENT_TYPE, CHANNEL_CHAT_BOT, SMTP_MAILER_MODULE, CHANNEL_SMTP_MAILER, CHANNEL_MQTT, SCRIPT_RUNNER_MODULE, LOG_MANAGER_MODULE
from oneadmin.core.event import EventType, ArbitraryDataEvent
from oneadmin.abstracts import IModule, IMQTTClient, IScriptRunner, IMailer, ILogMonitor, ISystemMonitor, IReactionEngine, IEventHandler, IEventDispatcher, IntentProvider, TargetProcess
from oneadmin.urls import get_url_patterns
from oneadmin.abstracts import IntentProvider
from oneadmin.core.constants import TOPIC_LOGMONITORING
from oneadmin.core.intent import INTENT_PREFIX
from oneadmin.core.action import ACTION_PREFIX
from oneadmin.core.event import StatsGeneratedEvent, EVENT_STATS_GENERATED

import logging
import tornado
import os, json, sys
from tornado import autoreload
from typing import Text, List, Dict
from oneadmin.exceptions import ConfigurationLoadError
from settings import __BASE_PACKAGE__, __MODULES__PACKAGE__, __MODULES__CONF_PACKAGE__, settings
from builtins import issubclass





class TornadoApplication(tornado.web.Application):

    def __init__(self, conf):
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__config = conf
        self.__system_stats = None
        self.__clients = {}
        self.__module_registry = ModuleRegistry()
        
        modules = conf["modules"]
        
        
        try:
            self.__filemanager = None
            self.__pubsubhub = None
            self.__action__dispatcher = None
            self.__communication_hub = CommunicationHub()  
            
            
            
            ''' Initializing pubsub module '''
            pubsub_conf = modules[PUBSUBHUB_MODULE]
            self.__pubsubhub:PubSubHub = PubSubHub(pubsub_conf["conf"])
            self.__pubsubhub.activate_message_flush()
            
            
            if self.__pubsubhub != None:
                self.modules.registerModule(PUBSUBHUB_MODULE, self.__pubsubhub) 
           
            
            
            root_path = os.path.dirname(os.path.realpath(sys.argv[0]))
            package_path = os.path.join(root_path, __BASE_PACKAGE__)
            modules_path = os.path.join(package_path, __MODULES__PACKAGE__)
            modules_conf_path = os.path.join(modules_path, __MODULES__CONF_PACKAGE__)
            json_files:List = [pos_json for pos_json in os.listdir(modules_conf_path) if pos_json.endswith('.json')]
            module_configs:List = []
            
            for mod_json in json_files:
                                
                conf_path = os.path.join(modules_conf_path, mod_json)
                config = self.load_module_config(conf_path)
                
                if not "enabled" in config or config["enabled"] == False:
                    continue
                
                if not "order" in config:
                    config["order"] = 0
                
                config["name"] = os.path.splitext(mod_json)[0]
                module_configs.append(config)
                
                
            
            ''' sorting module configs by load order '''
            sorted_module_configs = sorted(module_configs, key = lambda i: i['order'])
            
            
            listener_modules:List = []
            actionable_modules:List = []
            target_delegates:List = []
            module_url_patterns:List = []
            logs_to_monitor:List = []
            intent_actions:Dict = {}
            
            
            for sorted_config in sorted_module_configs:
                
                try:
                
                    module_name = __BASE_PACKAGE__ + "." + __MODULES__PACKAGE__ + "." + sorted_config["name"]
                    module_class_name = sorted_config["klass"]
                    self.logger.info("preparing module %s", module_name)
                    mod = __import__(module_name, fromlist=[module_class_name])
                    klass = getattr(mod, module_class_name)
                    mod_instance:IModule = klass(sorted_config["conf"])
                    mod_id = mod_instance.getname()
                    mod_instance.eventhandler = self.handle_event
                    
                    if isinstance(mod_instance, IEventHandler):
                        listener_modules.append(mod_instance)
                    
                    if isinstance(mod_instance, IntentProvider):
                        actionable_modules.append(mod_instance)
                    
                    if isinstance(mod_instance, TargetProcess):
                        target_delegates.append(mod_instance)
                        
                        logs:List = mod_instance.getLogFiles()
                        logs_to_monitor.extend(logs)
                        
                        
                    ''' Custom intent and action definitions '''
                    
                    custom_intents:List = mod_instance.supported_intents()
                    for intent_name in custom_intents:
                        try:
                            action_name = str(intent_name).replace(INTENT_PREFIX, ACTION_PREFIX)
                            action = mod_instance.action_from_name(action_name)
                        
                            if action:
                                intent_actions[intent_name] = action
                                self.logger.debug("Collecting intent by name" + intent_name + " for action " + action_name)
                            else:
                                raise TypeError("'action' for intent " + intent_name + " was None, where object of type 'Action' was expected") 
                   
                        except TypeError as te:
                            self.logger.warn(str(te))
                            pass
                        
                        
                    
                    patterns:List = mod_instance.get_url_patterns()
                    if len(patterns)>0:
                        module_url_patterns.extend(patterns)
                    
                    mod_instance.initialize()
                    self.modules.registerModule(mod_id, mod_instance)
                
                except Exception as e:
                    
                    self.logger.error("Error initializing module " + str(mod_instance) + ".Cause : " + str(e))                    
                  
                
            
            
            ''' Assign intent request handler to all eligible modules '''
            
            for actionable_mod in  actionable_modules:
                actionable_mod.intenthandler = self.handle_intent_request
                
                
            
            ''' Attach event listener to eligible modules'''
            
            for listener_mod in  listener_modules:
                self.__pubsubhub.addEventListener(listener_mod)
                
                
            
            ''' Register log files for4 monitoring '''
                
            tornado.ioloop.IOLoop.current().spawn_callback(self.register_logs_for_monitoring, logs_to_monitor)
            
            
            
            ''' Initializing action dispatcher '''
            
            action_config = modules[ACTION_DISPATCHER_MODULE]
            if action_config != None and action_config["enabled"] == True:
                self.__action__dispatcher = ActionDispatcher(self.modules, action_config["conf"])
                for intent_name, action in intent_actions.items():
                    self.__action__dispatcher.registerActionforIntent(intent_name, action)
                    self.logger.debug("Registered intent by name" + intent_name + " for action " + action_name)
            
            del intent_actions

            
            
            ''' Proceed with server startup '''
            
            server_config = conf["server"]

                
            # Special settings for debugging and hot reload
            settings["debug"] = server_config["debug_mode"]        
            settings["autoreload"] = server_config["hot_reload"]
            
            # Watch configuration files
            self.addwatchfiles(settings["app_configuration"])
            self.addwatchfiles(settings["users_configuration"])
            
            # runtime enabling of endpoints 
            endpoint_rest_api_config = None
            endpoint_ws_config = None
            endpoint_rest_support = False
            endpoint_ws_support = False  
            
            if "api" in server_config:
                endpoint_rest_api_config = server_config["api"]
                if endpoint_rest_api_config and endpoint_rest_api_config["enabled"] == True:
                    endpoint_rest_support = True
                
            
            if "ws" in server_config:
                endpoint_ws_config = server_config["ws"]
                if endpoint_ws_config and endpoint_ws_config["enabled"] == True:
                    endpoint_ws_support = True
                

            patterns = get_url_patterns(endpoint_rest_support, endpoint_ws_support)  
            patterns.extend(module_url_patterns)

                  
            tornado.web.Application.__init__(self, patterns, **settings)
        
        except Exception as e:
            
            self.logger.error("Oops! an error occurred initializing application.%s", str(e))

    
    
    
    
    
    def load_module_config(self, json_data_file):
        
        try:
            self.logger.info("Loading " + json_data_file)
            
            if os.path.exists(json_data_file):
                with open(json_data_file, 'r+') as json_data:
                    return json.load(json_data)
            else:
                raise FileNotFoundError("File : " + json_data_file + " does not exist.")
        
        except Exception as e:
            err = "Unable to load configuration file " + json_data_file + ".cause" + str(e)
            self.logger.error(err)
            raise ConfigurationLoadError(err)
        

        
        
    '''
        Gets system wide capabilities
    '''
    def get_system_capabilities(self):
        return {}
    
    
    
    
    def addwatchfiles(self, *paths):
        for p in paths:
            autoreload.watch(os.path.abspath(p))
            
            
            
    
    
    async def register_logs_for_monitoring(self, logfiles:List) ->None:
        
        if self.modules.hasModule(LOG_MANAGER_MODULE):
            for log_file in  logfiles:
                await self.handle_log_monitoring_request(log_file)
                
                
            
            
    
    '''
    Handles dynamic request for log monitoring
    ''' 
    async def handle_log_monitoring_request(self, logfile):
        
        if self.modules.hasModule(LOG_MANAGER_MODULE):
            try:
                logmon:ILogMonitor = self.modules.getModule(LOG_MANAGER_MODULE)
                log_key = getLogFileKey(logfile)
                log__topic_path = buildTopicPath(TOPIC_LOGMONITORING, log_key)
                logmon.register_log_file({
                    "name": log_key, "topic_path": log__topic_path, "log_file_path": logfile
                })
                
                self.__pubsubhub.createChannel({"name":log__topic_path, "type": "subscription", "queue_size":1, "max_users":0})
            
            except Exception as e:
                self.logger.error("Oops! an error occurred registering log for monitoring.%s", str(e))
    
    
    
    
    '''
    async def handleDelegateEvents(self, event):
        self.logger.debug("Event received from delegate")
        await self.__pubsubhub.publish_event(event)
    '''
    
    
  
    
    '''
    Handles arbitrary events from all modules.
    ''' 
    async def handle_event(self, event:EventType):
        self.logger.debug("handle_event for " + str(event["name"]))
        
        ''' event data aggregation is a good case for data filter or data plugins '''
        if event["name"] == EVENT_STATS_GENERATED:
            modules:List = self.modules.getModules()
            for mod in modules:
                if isinstance(mod, TargetProcess):
                        alias_name = mod.getAlias()
                        alias_stats = await mod.getTargetStats()
                        event["data"]["target"] = {} if event["data"]["target"] == None else event["data"]["target"] 
                        event["data"]["target"][alias_name] = alias_stats
        
        await self.__pubsubhub.publish_event_type(event)
    
    
    
    
    '''
    Handles action requests from all modules
    ''' 
    async def handle_intent_request(self, source:IntentProvider, intent:Text, args:Dict, event:EventType=None):
        self.logger.debug("handle_actionable intent for " + str(source))
        return await self.action_dispatcher.handle_request(source, intent, args, event)
    
   
    
    @property
    def totalclients(self):
        return len(self.__clients.keys())
    
    
    @property
    def clients(self):
        return self.__clients;  
    
    
    def registerClient(self, client):
        self.__clients[client.id] = client
        pass
    
    def unregisterClient(self, client):
        if client.id in self.__clients:
            del self.__clients[client.id]
        pass
        
    @property
    def configuration(self):
        return self.__config
    
    @configuration.setter
    def configuration(self, config):
        self.__config = config
        
    
    @property    
    def modules(self):
        return self.__module_registry
    
    
    @property    
    def action_dispatcher(self):
        return self.__action__dispatcher

    
    '''
    Returns aggregated stats object - snapshot
    '''    
    def getAggregatedStats(self):
        return self.__system_stats
    
    
    def startTarget(self):
        pass
    
    def stopTarget(self):
        pass

