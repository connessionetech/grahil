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

from oneadmin.urls import url_patterns
import urllib.request
from oneadmin.responsebuilder import buildDataEvent
from oneadmin.utilities import buildTopicPath
from oneadmin.utilities import getLogFileKey
from oneadmin.communications import PubSubHub, RPCGateway, Pinger

from requests.api import get
import logging
import tornado
from settings import settings
from tornado import autoreload
import os



from oneadmin.modules.filesystem import FileManager
from oneadmin.modules.logmonitor import LogMonitor
from oneadmin.modules.reaction import ReactionEngine
from oneadmin.modules.sysmonitor import SystemMonitor
from oneadmin.modules.actions import ActionExecutor
from oneadmin.core.grahil_core import ModuleRegistry
import socket
import asyncio
from oneadmin.core.constants import *
from core.components import ActionDispatcher
from core.constants import ACTION_DISPATCHER_MODULE
from core.events import EventType



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
            self.__logmonitor = None
            self.__pubsubhub = None
            self.__pinger = None
            self.__service_bot = None
            self.__reaction_engine = None
            self.__action__dispatcher = None
            self.__external_ip = None
            
            
            # Attempt to find out public ip
            while True:
                if self.__has_internet():
                    break
                
                self.logger.info("No network connection. Waiting for connection...")
                asyncio.sleep(10)
                
            
         
            # Initializing pubsub hub
            pubsub_conf = modules[PUBSUBHUB_MODULE]
            self.__pubsubhub = PubSubHub(pubsub_conf["conf"])
            self.__pubsubhub.activate_message_flush()
            
            '''
            '''
            if self.__pubsubhub != None:
                self.modules.registerModule(PUBSUBHUB_MODULE, self.__pubsubhub)
                
                
                
            ''' Initializing pinger module used for sending keep-alive heartbeat to socket connections'''
            pinger_conf = modules[PINGER_MODULE]
            self.__pinger = Pinger(pinger_conf["conf"])
            self.__pinger.callback = self.processPing
            self.__pinger.eventhandler = self.handle_event
            self.__pinger.start()       
                 
            '''
            Register `pinger` module
            '''
            self.modules.registerModule(PINGER_MODULE, self.__pinger);
            
            
            
            
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
                self.modules.registerModule(FILE_MANAGER_MODULE, self.__filemanager);
            
            
            
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
                self.__logmonitor = LogMonitor(log_monitor_config["conf"])
                self.__logmonitor.eventhandler = self.handle_event               
                    
                    
                try:
                    
                    ''' 
                    Register dynamic log targets of target 
                    '''
                    
                    dynamic_log_targets = []
                    for log_target in dynamic_log_targets:
                        
                        log_key = getLogFileKey(log_target)
                        log__topic_path = buildTopicPath(PubSubHub.LOGMONITORING, log_key)
                        self.__logmonitor.registerLogFile({
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
                    
                    log_monitor_config["static_targets"]
                    if log_monitor_config["static_targets"] != None:
                        log_targets = log_monitor_config["static_targets"]
                        for log_target in log_targets: 
                            if log_target["enabled"] == True:
                                
                                if not log_target["topic_path"]:
                                    log_target["topic_path"] = buildTopicPath(PubSubHub.LOGMONITORING, log_target["name"])
                                
                                self.__logmonitor.registerLogFile(log_target)
    
                
                except Exception as le:
                    self.logger.error("Error processing log monitor configuration. %s", str(le))
                            
                        
                '''
                Register `log monitor` module
                '''
                self.modules.registerModule(LOG_MANAGER_MODULE, self.__logmonitor);
            
            
            
            stats_config = modules[SYSTEM_MODULE]
            if stats_config != None and stats_config["enabled"] == True:
                self.__sysmon = SystemMonitor(stats_config["conf"], self.modules)
                self.__sysmon.eventhandler = self.handle_event
                self.__sysmon.start_monitor()
            
            
            '''
            Register `sysmon` module
            '''
            self.modules.registerModule(SYSTEM_MODULE, self.__sysmon);
            
                    
                
        except Exception as e:
            self.logger.error("Oops!,%s,occurred." + str(e))
        
        
        
        ''' Action executor'''
        '''
        action_config = modules[ACTION_EXECUTOR_MODULE]
        if action_config != None and action_config["enabled"] == True:
            self.__action__executor = ActionExecutor(action_config["conf"], self.modules)
        '''
        
        action_config = modules[ACTION_DISPATCHER_MODULE]
        if action_config != None and action_config["enabled"] == True:
            self.__action__dispatcher = ActionDispatcher(self.modules, action_config["conf"])
            
            
        
        ''' Reaction engine -> to send commands to reaction engine use pubsub '''
        # Register reaction engine
        '''
        reaction_engine_conf = modules[REACTION_ENGINE_MODULE];
        if reaction_engine_conf["enabled"] == True:
            self.__reaction_engine = ReactionEngine(reaction_engine_conf["conf"], self.modules)
            self.__reaction_engine.eventhandler = handle_event
                        
            # Inform pubsubhub of the reaction engine presence
            self.__pubsubhub.addNotifyable(self.__reaction_engine)
            self.__action__executor.rulesmanager = self.__reaction_engine            
        '''
        
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
                self.__service_bot = klass(bot_config, self.__action__dispatcher, nlp_engine)
                self.__service_bot.eventhandler = self.handle_event
                
                self.__pubsubhub.addNotifyable(self.__service_bot)
                
                # Register `servicebot` module'
                self.modules.registerModule(BOT_SERVICE_MODULE, self.__service_bot);
            
            except ImportError as be:
                self.logger.warn("Module by name " + bot_module_name + " was not found and will not be loaded")
                


        
        ''' Registering RPC engine for Webclients '''
        # Initializing rpc gateway
        rpc_gateway_conf = modules[RPC_GATEWAY_MODULE]
        self.__rpc_gateway = RPCGateway(rpc_gateway_conf["conf"], self.__action__dispatcher)
        
        '''
        Register `rpc_gateway` module
        '''
        self.modules.registerModule(RPC_GATEWAY_MODULE, self.__rpc_gateway)
        

        
        # Special settings for debugging and hot reload
        settings["debug"] = conf["server"]["debug_mode"]        
        settings["autoreload"] = conf["server"]["hot_reload"]
        
        # Watch configuration files
        self.addwatchfiles(settings["app_configuration"])
        self.addwatchfiles(settings["users_configuration"])
        
        
        tornado.web.Application.__init__(self, url_patterns, **settings)
        
        
    '''
        Gets system wide capabilities
    '''
    def notget_system_capabilities(self):
        
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
                "new_stats_interval": stats_config["snapshot_interval_seconds"],
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
                "max_upload_size": file_manager_config["max_upload_size"],
                "max_parallel_uploads": file_manager_config["max_parallel_uploads"],
                "allowed_read_extensions": file_manager_config["allowed_read_extensions"],
                "allowed_write_extensions": file_manager_config["allowed_write_extensions"],
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
    
    
    
    async def processPing(self, data, error):
        if error == None:
            self.logger.debug("Ping message generated for clients")
            evt = buildDataEvent({"subject":"System", "concern": "Time", "content":data}, PubSubHub.PING)
            await self.__pubsubhub.publish(PubSubHub.PING, evt)        
        pass
    
    
    
    def addwatchfiles(self, *paths):
        for p in paths:
            autoreload.watch(os.path.abspath(p))
    
    
    
    
    async def handleDelegateEvents(self, event):
        self.logger.debug("Event received from delegate")
        await self.__pubsubhub.publish_event(event)
        pass    
        
        
        
    
    async def processSystemStats(self, data, error=None):
        if(error == None):
            self.logger.debug("System stats received")
            self.__system_stats = data            
            evt = buildDataEvent({"subject":"System", "concern": "StatsGenerated", "content":self.__system_stats}, PubSubHub.SYSMONITORING)
            await self.__pubsubhub.publish(PubSubHub.SYSMONITORING, evt)
        else:
            self.logger.error("System monitor error " + str(error))
        pass
    
    
    
  
    '''
    Handles arbitrary events from all modules
    ''' 
    async def handle_event(self, event:EventType):
        self.logger.info("handle_event for " + str(event["name"]))
        await self.__pubsubhub.publish_event_type(event) 
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
    
    
    
    
    
    def __has_internet(self, host="8.8.8.8", port=53, timeout=3):
        """
        Host: 8.8.8.8 (google-public-dns-a.google.com)
        OpenPort: 53/tcp
        Service: domain (DNS/TCP)
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error as ex:
            return False
        

    
    '''
    Returns aggregated stats object - snapshot
    '''    
    def getAggregatedStats(self):
        return self.__system_stats
    
    
    def startTarget(self):
        pass
    
    def stopTarget(self):
        pass

