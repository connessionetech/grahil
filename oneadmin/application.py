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

from oneadmin.urls import url_patterns
from oneadmin.responsebuilder import buildDataEvent
from oneadmin.utilities import buildTopicPath
from oneadmin.utilities import getLogFileKey
from oneadmin.communications import PubSubHub, RPCGateway, Pinger
from oneadmin.modules.filesystem import FileManager
from oneadmin.core.grahil_core import ModuleRegistry
from oneadmin.core.constants import *
from oneadmin.core.components import ActionDispatcher, CommunicationHub
from oneadmin.core.constants import ACTION_DISPATCHER_MODULE, PROACTIVE_CLIENT_TYPE, REACTIVE_CLIENT_TYPE, CHANNEL_WEBSOCKET_RPC, CHANNEL_CHAT_BOT, SMTP_MAILER_MODULE, CHANNEL_SMTP_MAILER, CHANNEL_MQTT, SCRIPT_RUNNER_MODULE
from oneadmin.core.event import EventType, ArbitraryDataEvent
from oneadmin.abstracts import IMQTTClient, IScriptRunner, IMailer, ILogMonitor, ISystemMonitor, IReactionEngine

import logging
import tornado
import urllib.request
import os
import socket
import asyncio

from requests.api import get
from settings import settings
from tornado import autoreload
from typing import Text




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
                
                
            
            ''' Initializing action executor '''
            action_config = modules[ACTION_DISPATCHER_MODULE]
            if action_config != None and action_config["enabled"] == True:
                self.__action__dispatcher = ActionDispatcher(self.modules, action_config["conf"])
                
                
                
            ''' Initializing pinger module used for sending keep-alive heartbeat to socket connections'''
            pinger_conf = modules[PINGER_MODULE]
            pinger = Pinger(pinger_conf["conf"])
            pinger.eventhandler = self.handle_event
            pinger.start()       
                 
            '''
            Register `pinger` module
            '''
            self.modules.registerModule(PINGER_MODULE, pinger);
            
            
            
            ''' Conditional instantiation of file manager '''
            # Register filemanager module
            filemanager_config = modules[FILE_MANAGER_MODULE]
            if filemanager_config != None and filemanager_config["enabled"] == True:
                
                accessible_paths = []
                
                ''' Get static declared accessible paths from configuration '''
                accessible_static_paths = filemanager_config["conf"]["accessible_paths"]
                for accessible_static_path in accessible_static_paths:
                    accessible_paths.append(accessible_static_path)
                
                self.__filemanager = FileManager(filemanager_config["conf"], accessible_paths)
                self.__filemanager.eventhandler = self.handle_event
                
                '''
                Register `file_manager` module
                '''
                self.modules.registerModule(FILE_MANAGER_MODULE, self.__filemanager)
            
            
            
            ''' Conditional instantiation of {target} handler '''
            delegate_conf = modules[TARGET_DELEGATE_MODULE];
            if delegate_conf != None and delegate_conf["enabled"] == True:
                module_name = delegate_conf["module"]
                class_name = delegate_conf["klass"]
                
                try:
                    mod = __import__(module_name, fromlist=[class_name])
                    klass = getattr(mod, class_name)
                    self.__delegate = klass(delegate_conf["conf"])
                    
                    if self.__delegate is not None:
                        self.__delegate.eventcallback = self.handleDelegateEvents
                        self.__delegate.eventhandler = self.handle_event
                except ImportError as de:
                    self.logger.warn("Module by name %s was not found and will not be loaded", module_name)
                
                '''
                Register `target_delegate` module
                '''
                if self.__delegate != None:
                    self.modules.registerModule(TARGET_DELEGATE_MODULE, self.__delegate);
                    

            

            # Register log monitor module
            log_monitor_config = modules[LOG_MANAGER_MODULE]
            if log_monitor_config != None and log_monitor_config["enabled"] == True:
                logmon_module_name = log_monitor_config["module"]
                logmon_class_name = log_monitor_config["klass"]
                mod = __import__(logmon_module_name, fromlist=[logmon_class_name])
                klass = getattr(mod, logmon_class_name)
                logmonitor:ILogMonitor = klass(log_monitor_config["conf"])
                logmonitor.eventhandler = self.handle_event
                    
                try:
                    
                    ''' 
                    Register dynamic log targets of target 
                    '''
                    
                    dynamic_log_targets = []
                    for log_target in dynamic_log_targets:
                        
                        log_key = getLogFileKey(log_target)
                        log__topic_path = buildTopicPath(PubSubHub.LOGMONITORING, log_key)
                        logmonitor.register_log_file({
                            "name": log_key, "topic_path": log__topic_path, "log_file_path": log_target
                        })
                        
                        # Register channel per log
                        channel_info = {}
                        channel_info["name"] = log__topic_path  
                        channel_info['type'] = "subscription"
                        channel_info["queue_size"] = 1
                        channel_info["max_users"]  = 0
                        self.__pubsubhub.createChannel(channel_info)
                    
                    
                    ''' 
                    Register static log targets of target 
                    '''
                    
                    log_monitor_config["conf"]["static_targets"]
                    if log_monitor_config["conf"]["static_targets"] != None:
                        log_targets = log_monitor_config["conf"]["static_targets"]
                        for log_target in log_targets: 
                            if log_target["enabled"] == True:
                                
                                if not log_target["topic_path"]:
                                    log_target["topic_path"] = buildTopicPath(PubSubHub.LOGMONITORING, log_target["name"])
                                
                                logmonitor.register_log_file(log_target)
    
                
                except Exception as le:
                    self.logger.error("Error processing log monitor configuration. %s", str(le))
                            
                        
                '''
                Register `log monitor` module
                '''
                self.modules.registerModule(LOG_MANAGER_MODULE, logmonitor);
            
            
            
            system_mod_config = modules[SYSTEM_MODULE]
            if system_mod_config != None and system_mod_config["enabled"] == True:
                sysmon_module_name = system_mod_config["module"]
                sysmon_class_name = system_mod_config["klass"]
                mod = __import__(sysmon_module_name, fromlist=[sysmon_class_name])
                klass = getattr(mod, sysmon_class_name)
                sysmon:ISystemMonitor = klass(system_mod_config["conf"], self.modules)
                sysmon.eventhandler = self.handle_event
                sysmon.start_monitor()
            
            
                '''
                Register `sysmon` module
                '''
                self.modules.registerModule(SYSTEM_MODULE, sysmon)
            
                    
        
            ''' Reaction engine -> to send commands to reaction engine use pubsub '''
            # Register reaction engine
            
            reaction_engine_conf = modules[REACTION_ENGINE_MODULE];
            if reaction_engine_conf["enabled"] == True:
                reaction_module_name = reaction_engine_conf["module"]
                reaction_class_name = reaction_engine_conf["klass"]
                mod = __import__(reaction_module_name, fromlist=[reaction_class_name])
                klass = getattr(mod, reaction_class_name)
                reaction_engine:IReactionEngine = klass(reaction_engine_conf["conf"], self.__action__dispatcher)
                reaction_engine.eventhandler = self.handle_event
                self.__pubsubhub.addEventListener(reaction_engine)
            
            
            
            
            ''' Bot -> to send commands to bot use pubsub '''
            
            bot_config =  modules[BOT_SERVICE_MODULE]
            if bot_config != None and bot_config["enabled"] == True:
                bot_module_name = bot_config["module"]
                bot_class_name = bot_config["klass"]
                
                nlp_engine = None
            
                try:
                    
                    try:
                        nlp_module_name = bot_config["nlp"]["module"]
                        nlp_module_config = bot_config["nlp"]["conf"]
                        nlp_class_name = bot_config["nlp"]["klass"]
                        nlp_mod = __import__(nlp_module_name, fromlist=[nlp_class_name])
                        nlp_klass = getattr(nlp_mod, nlp_class_name)
                        nlp_engine = nlp_klass(self.__filemanager, nlp_module_config)
                    except ImportError as be:
                        self.logger.warn("Module by name " + nlp_module_name + " was not found and will not be loaded")
                    
                    
                    mod = __import__(bot_module_name, fromlist=[bot_class_name])
                    klass = getattr(mod, bot_class_name)
                    service_bot = klass(bot_config, self.__action__dispatcher, nlp_engine)
                    service_bot.eventhandler = self.handle_event
                    self.__pubsubhub.addEventListener(service_bot)
                    
                    # Register `servicebot` module'
                    self.modules.registerModule(BOT_SERVICE_MODULE, service_bot)
                    
                    '''
                    Register communication interface with communication hub
                    ''' 
                    self.__communication_hub.register_interface(CHANNEL_CHAT_BOT, PROACTIVE_CLIENT_TYPE, service_bot)
                
                except ImportError as be:
                    self.logger.warn("Module by name " + bot_module_name + " was not found and will not be loaded")
                        
        
        
                
            ''' Registering RPC engine for Webclients '''
            # Initializing rpc gateway
            rpc_gateway_conf = modules[RPC_GATEWAY_MODULE]
            self.__rpc_gateway = RPCGateway(rpc_gateway_conf["conf"], self.__action__dispatcher)
            
            '''
            Register `rpc gateway` module
            '''
            self.modules.registerModule(RPC_GATEWAY_MODULE, self.__rpc_gateway)
            
            '''
            Register communication interface with communication hub
            '''
            self.__communication_hub.register_interface(CHANNEL_WEBSOCKET_RPC, REACTIVE_CLIENT_TYPE, self.__rpc_gateway)
            
            
            
            '''
            Register `mqtt gateway` module
            '''
            
            mqtt_gateway_conf = modules[MQTT_GATEWAY_MODULE]
            if mqtt_gateway_conf != None and mqtt_gateway_conf["enabled"] == True:
                mqtt_module_name = mqtt_gateway_conf["module"]
                mqtt_class_name = mqtt_gateway_conf["klass"]
                mod = __import__(mqtt_module_name, fromlist=[mqtt_class_name])
                klass = getattr(mod, mqtt_class_name)
                mqtt_gateway:IMQTTClient = klass(mqtt_gateway_conf["conf"], self.__action__dispatcher)
                mqtt_gateway.on_data_handler = self.on_telemetry_data
                
                
                '''
                Register `rpc gateway` module
                '''
                self.modules.registerModule(MQTT_GATEWAY_MODULE, mqtt_gateway)
                
                '''
                Register communication interface with communication hub
                '''
                self.__communication_hub.register_interface(CHANNEL_MQTT, PROACTIVE_CLIENT_TYPE, mqtt_gateway)
            
            
            
            '''
            Register `smtp mailer` module
            '''
                
            smtp_mailer_conf = modules[SMTP_MAILER_MODULE]
            if smtp_mailer_conf != None and smtp_mailer_conf["enabled"] == True:
                smtp_module_name = smtp_mailer_conf["module"]
                smtp_class_name = smtp_mailer_conf["klass"]
                mod = __import__(smtp_module_name, fromlist=[smtp_class_name])
                klass = getattr(mod, smtp_class_name)
                smtp_mailer:IMailer = klass(smtp_mailer_conf["conf"])
                
                self.modules.registerModule(SMTP_MAILER_MODULE, smtp_mailer)
                
                '''
                Register communication interface with communication hub
                '''
                self.__communication_hub.register_interface(CHANNEL_SMTP_MAILER, PROACTIVE_CLIENT_TYPE, smtp_mailer)
                
               
               
               
            '''
            Register `script_runner` module
            '''
                   
            script_runner_conf = modules[SCRIPT_RUNNER_MODULE] 
            if script_runner_conf != None and script_runner_conf["enabled"] == True:
                script_runner_module_name = script_runner_conf["module"]
                script_runner_class_name = script_runner_conf["klass"]
                mod = __import__(script_runner_module_name, fromlist=[script_runner_class_name])
                klass = getattr(mod, script_runner_class_name)
                script_runner:IScriptRunner = klass(script_runner_conf["conf"])
                script_runner.eventhandler = self.handle_event
                self.__filemanager.list_files(script_runner.script_files_from_future, script_runner_conf["conf"]["script_folder"], script_runner_conf["conf"]["file_types"])
                
                self.modules.registerModule(SCRIPT_RUNNER_MODULE, script_runner)
                
                
                
                
            # Special settings for debugging and hot reload
            settings["debug"] = conf["server"]["debug_mode"]        
            settings["autoreload"] = conf["server"]["hot_reload"]
            
            # Watch configuration files
            self.addwatchfiles(settings["app_configuration"])
            self.addwatchfiles(settings["users_configuration"])
        
        
            tornado.web.Application.__init__(self, url_patterns, **settings)

        
        except Exception as e:
            
            self.logger.error("Oops! an error occurred initializing application.%s", str(e))
        
        

        
        
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
        self.logger.info("handle_event for " + str(event["name"]))
        await self.__pubsubhub.publish_event_type(event) 
        pass
    
    
    
    '''
    Handles events from telemetry channel if available
    ''' 
    async def on_telemetry_data(self, topic:Text, data:dict)->None:
        event:EventType = ArbitraryDataEvent(topic, data)
        await self.handle_event(event) 
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

