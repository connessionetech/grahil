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
from oneadmin.modules.reaction import ReactionEngine

from requests.api import get
import logging
import tornado
from settings import settings
from tornado import autoreload
import os

from oneadmin.modules.filesystem import FileManager
from oneadmin.modules.logmonitor import LogMonitor


class ModuleRegistry(object):
    
    def __init__(self):
        
        self.__registry = {}        
        pass
    
    
    def registerModule(self, name, reference):
        if name not in self.__registry.keys():
            self.__registry[name] = reference;
        pass
    
    
    def deregisterModule(self, name):
        if name in self.__registry.keys():
            del self.__registry[name]
        pass
    
    
    def getModule(self, name):
        if name in self.__registry.keys():
            return self.__registry[name]
        else:
            return None
        pass
    
    
    def hasModule(self, name):
        if name in self.__registry.keys():
            return True
        else:
            return False


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
            self.__reaction_engine = None
            
            
            # Attempt to find out public ip
            self.__discoverHost()    
            
         
            # Initializing pubsub hub
            pubsub_conf = modules["pubsub"]
            self.__pubsubhub = PubSubHub(pubsub_conf)
            self.__pubsubhub.activate_message_flush()
            
            '''
            Register `pubsub` module
            '''
            if self.__pubsubhub != None:
                self.modules.registerModule("pubsub", self.__pubsubhub)
                
                
            # Register Pinger modules for websocket clients
            self.__pinger = Pinger(modules["pinger"])
            self.__pinger.callback = self.processPing
            self.__pinger.start()       
                 
            '''
            Register `pinger` module
            '''
            self.modules.registerModule("pinger", self.__pinger);
                        
    
            ''' Conditional instantiation of file manager '''
            # Register filemanager module
            filemanager_config = modules["file_manager"]
            if filemanager_config != None and filemanager_config["enabled"] == True:
                
                accessible_paths = []
                
                ''' Get static declared accessible paths from configuration '''
                accessible_static_paths = filemanager_config["accessible_paths"]
                for accessible_static_path in accessible_static_paths:
                    accessible_paths.append(accessible_static_path)
                
                self.__filemanager = FileManager(filemanager_config, accessible_paths)
                
                '''
                Register `file_manager` module
                '''
                self.modules.registerModule("file_manager", self.__filemanager);
            
            
            # Register log monitor module
            log_monitor_config = modules["log_monitor"]
            if log_monitor_config != None and log_monitor_config["enabled"] == True:
                self.__logmonitor = LogMonitor(log_monitor_config)
                self.__logmonitor.callback = self.processLogLine
                self.__logmonitor.chunk_callback = self.processLogChunk
                
                    
                    
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
                    
                    # Register channel
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
            self.modules.registerModule("log monitor", self.__logmonitor);        
                        
                
        except Exception as e:
            self.logger.error("Oops!,%s,occurred." + str(e))


        
        # Initializing rpc gateway
        rpc_gateway_conf = modules["rpc_gateway"]
        self.__rpc_gateway = RPCGateway(rpc_gateway_conf, self.modules)
        
        '''
        Register `rpc_gateway` module
        '''
        self.modules.registerModule("rpc_gateway", self.__rpc_gateway)
        
        
        # Register reaction engine        
        reaction_engine_conf = modules["reaction_engine"];
        if reaction_engine_conf["enabled"] == True:
            self.__reaction_engine = ReactionEngine(reaction_engine_conf, self.modules)
            
            '''
            Register `reaction_engine` module            
            self.modules.registerModule("reaction_engine", self.__reaction_engine);
            '''
            
            # Inform pubsubhub of the reaction engine presence
            self.__pubsubhub.notifyable = self.__reaction_engine

        
        
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
        
    
    async def processLogLine(self, logname, topic, data, error=None):
        if(error == None):
            self.logger.debug("Log line received")
            # topicName = buildTopicPath(PubSubHub.LOGMONITORING, logname)
            evt = buildDataEvent({"subject":"Target", "concern": "LogStatement", "content":str(data, 'utf-8')}, topic)
            await self.__pubsubhub.publish(topic, evt)
        else:
            self.logger.error("Log line error " + str(error))
        pass
    
    
    async def processLogChunk(self, logname, topic, data, error=None):
        if(error == None):
            self.logger.debug("Log chunk received")
            evt = buildDataEvent({"subject":"Target", "concern": "LogChunk", "content":data}, topic)
            await self.__pubsubhub.publish(topic, evt)    
            # await self.__filemanager.write_file_stream("/home/rajdeeprath/sample_frame.log", data)            
        else:
            self.logger.error("Log chunk error " + str(error))
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
    
    '''
    Looks up external IP using public services
    '''
    def __discoverHost(self):
        
        self.__external_ip = None
        try:
            self.__external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
            if(self.__external_ip == None):
                raise Exception("IP could not be evaluated using %s", "https://ident.me")
        except Exception as ex:
            try:
                self.logger.warn(ex)
                self.__external_ip = get('https://api.ipify.org').text
                if(self.__external_ip == None):
                    raise Exception("IP could not be evaluated using %s", "https://api.ipify.org")
            except Exception as ex1:
                self.logger.warn(ex1)

    
    '''
    Returns aggregated stats object - snapshot
    '''    
    def getAggregatedStats(self):
        return self.__system_stats
    
    
    def startTarget(self):
        pass
    
    def stopTarget(self):
        pass

