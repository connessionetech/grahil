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
from oneadmin.communications import PubSubHub, RPCGateway, Pinger
#from oneadmin.modules.filesystem import FileManager
from oneadmin.core.grahil_core import ModuleRegistry
from oneadmin.core.constants import *
from oneadmin.core.components import ActionDispatcher, CommunicationHub
from oneadmin.core.constants import ACTION_DISPATCHER_MODULE, PROACTIVE_CLIENT_TYPE, REACTIVE_CLIENT_TYPE, CHANNEL_WEBSOCKET_RPC, CHANNEL_CHAT_BOT, SMTP_MAILER_MODULE, CHANNEL_SMTP_MAILER, CHANNEL_MQTT, SCRIPT_RUNNER_MODULE
from oneadmin.core.event import EventType, ArbitraryDataEvent
from oneadmin.abstracts import IModule, IMQTTClient, IScriptRunner, IMailer, ILogMonitor, ISystemMonitor, IReactionEngine, IEventHandler, IEventDispatcher, IntentProvider
from oneadmin.urls import get_url_patterns
from oneadmin.abstracts import IntentProvider


import logging
import tornado
import os, json, sys
from tornado import autoreload
from typing import Text, List, Dict
from oneadmin.exceptions import ConfigurationLoadError
from settings import __BASE_PACKAGE__, __MODULES__PACKAGE__, settings
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
                
            
            
            ''' Initializing pinger module used for sending keep-alive heartbeat to socket connections'''
            pinger_conf = modules[PINGER_MODULE]
            pinger = Pinger(pinger_conf["conf"])
            pinger.eventhandler = self.handle_event
            pinger.start()       
                 
            '''
            Register `pinger` module
            '''
            self.modules.registerModule(PINGER_MODULE, pinger);
            
            
            ''' -------------------------------'''
                        
            root_path = os.path.dirname(os.path.realpath(sys.argv[0]))
            package_path = os.path.join(root_path, __BASE_PACKAGE__)
            modules_path = os.path.join(package_path, __MODULES__PACKAGE__)
            json_files:List = [pos_json for pos_json in os.listdir(modules_path) if pos_json.endswith('.json')]
            module_configs:List = []
            
            for mod_json in json_files:
                                
                conf_path = os.path.join(modules_path, mod_json)
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
            
            
            for sorted_config in sorted_module_configs:
                module_name = __BASE_PACKAGE__ + "." + __MODULES__PACKAGE__ + "." + sorted_config["name"]
                module_class_name = sorted_config["klass"]
                self.logger.info("preparing module %s", module_name)
                mod = __import__(module_name, fromlist=[module_class_name])
                klass = getattr(mod, module_class_name)
                mod_instance:IModule = klass(sorted_config["conf"])
                mod_instance.eventhandler = self.handle_event
                
                if isinstance(mod_instance, IEventHandler):
                    listener_modules.append(mod_instance)
                
                if isinstance(mod_instance, IntentProvider):
                    actionable_modules.append(mod_instance)
                
                mod_instance.initialize()
                
            
            
            ''' Attach event listener modules'''
            
            for listener_mod in  listener_modules:
                self.__pubsubhub.addEventListener(listener_mod)
                
                
            
            ''' Assign intent request handler to all intent providers '''
            
            for actionable_mod in  actionable_modules:
                actionable_mod.intenthandler = self.handle_intent_request
                
            
            ''' -------------------------------'''
            
            
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
        
        modules = self.__config["modules"]
        
            
        
        target_delegate_config = modules["target_delegate"]
        delegate = self.modules.getModule("target_delegate");
        process_management_declaration = {}
        if delegate != None:
            process_management_declaration = {
                "installed": delegate.isTargetInstalled(),
                "running": delegate.is_proc_running(),
                "stopping": delegate.is_proc_stopping(),
                "starting": delegate.is_proc_starting(),
                "can_start": True,
                "can_stop": True,
            }
        
        
        
        # Declare system monitoring
        stats_config = modules["sysmon"]        
        sysmon_declaration = {}       
        if stats_config != None:
            sysmon_declaration = {
                "enabled": stats_config["enabled"],
                "new_stats_interval": stats_config["conf"]["snapshot_interval_seconds"],
                "topics": "/stats"
            }
            
        
            
        
        # Declare log monitoring
        log_monitor_config = modules["log_monitor"]
        logmon = self.modules.getModule("log monitor");
        logmon_declaration = {} 
        if logmon != None:
            logmon_declaration = {
                "enabled": log_monitor_config["enabled"],
                "renderer": "fixed_limit_text_area"
            }
            
        
        
        # Declare file management
        file_manager_config = modules["file_manager"]
        filemanager = self.modules.getModule("file_manager");
        file_management_declaration = {} 
        if logmon != None:
            file_management_declaration = {
                "enabled": file_manager_config["enabled"],
                "max_upload_size": file_manager_config["conf"]["max_upload_size"],
                "max_parallel_uploads": file_manager_config["conf"]["max_parallel_uploads"],
                "allowed_read_extensions": file_manager_config["conf"]["allowed_read_extensions"],
                "allowed_write_extensions": file_manager_config["conf"]["allowed_write_extensions"],
                "can_read": True,
                "can_write": True,
                "can_browse": False,
                "renderer": None
            }
            
        
            
        # Define system wide capabilities
        capabilities = {
            "services":{
                "process_control":process_management_declaration,
                "system":{
                    "monitoring":sysmon_declaration,
                    "diagnostic": None,
                },
                "log_management":{
                    "monitoring" : logmon_declaration
                },
                "file_management":file_management_declaration
            }
        }
        
        
        return capabilities
    
    
    
    
    def addwatchfiles(self, *paths):
        for p in paths:
            autoreload.watch(os.path.abspath(p))
    
    
    
    
    async def handleDelegateEvents(self, event):
        self.logger.debug("Event received from delegate")
        await self.__pubsubhub.publish_event(event)
        pass   
    
    
  
    '''
    Handles arbitrary events from all modules
    ''' 
    async def handle_event(self, event:EventType):
        self.logger.debug("handle_event for " + str(event["name"]))
        await self.__pubsubhub.publish_event_type(event) 
        pass
    
    
    
    '''
    Handles action requests from all modules
    ''' 
    async def handle_intent_request(self, source:IntentProvider, intent:Text, args:Dict, event:EventType=None):
        self.logger.debug("handle_actionable intent for " + str(source))
        await self.action_dispatcher.handle_request(source, intent, args, event)
        pass
    
   
    
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

