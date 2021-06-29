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

from oneadmin.core.abstracts import IModule, ILogMonitor, LoggingHandler, IntentProvider
from oneadmin.core.event import LogEvent, LogErrorEvent, LogChunkEvent
from oneadmin.core.utilities import buildTopicPath
from oneadmin.core.constants import TOPIC_LOGMONITORING, LOG_MANAGER_MODULE, FILE_MANAGER_MODULE
from oneadmin.responsebuilder import formatSuccessResponse, formatErrorResponse
from oneadmin.core.constants import LOG_MANAGER_MODULE, FILE_MANAGER_MODULE
from oneadmin.core.action import Action, ActionResponse, ACTION_PREFIX
from oneadmin.core.intent import INTENT_PREFIX
from oneadmin.core import grahil_types

from settings import settings


import tornado
import logging
import collections
import json

from datetime import datetime


from tornado.process import Subprocess
from tornado.concurrent import asyncio
from sys import platform
from pathlib import Path
from typing import Dict, List, Text
from tornado.web import url




class LogMonitor(IModule, ILogMonitor):
    '''
    classdocs
    '''
    
    NAME = "log_monitor"
    

    def __init__(self, conf):
        '''
        Constructor
        '''
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
        self.__log_files = {}
        self.__log_store = {}            
        pass 
    
    
    
    def getname(self) ->Text:
        return LogMonitor.NAME 
    
    
    
    
    def initialize(self)->None:
        self.logger.info("Module init")
        self.register_static_log_targets()
        pass 
    

    
    def valid_configuration(self, conf:Dict) ->bool:
        return True 
    
    
    def get_url_patterns(self)->List:
        return [ url(r"/log/download/([^/]+)", LogDownloadHandler) ]
    
    
    
    def register_static_log_targets(self)->None:
        
        ''' 
        Register static log targets of target 
        '''
        
        static_log_targets = self.__conf["static_targets"]
        if static_log_targets != None:
            for log_target in static_log_targets: 
                if log_target["enabled"] == True:
                    
                    if "topic_path" not in log_target:
                        log_target["topic_path"] = buildTopicPath(TOPIC_LOGMONITORING, log_target["name"])
                    
                    self.register_log_file(log_target)
                    
     
     
    
    '''
    Returns list of available log targets with their subscription paths
    '''
    def get_log_targets(self):
        targets = []
        
        for name, log_info in self.__log_files.items():
            targets.append({"name": name, "topic": log_info["topic_path"]})
        
        return targets              
    
    
    
    
    '''
    Register new log file for monitoring
    '''
    def register_log_file(self, log_info:Dict) -> None:
        
        name = log_info["name"]
        if not name in self.__log_files:
            self.__log_files[name] = log_info
            self.__log_store[name] = collections.deque([], self.__conf["max_messages_chunks"])
            tornado.ioloop.IOLoop.current().spawn_callback(self.__tail, name)
            #tornado.ioloop.IOLoop.current().spawn_callback(self.__schedule_chunk_processing, name)    
    
    
    '''
    Deregister existing log file from monitoring
    '''
    def deregister_log_file(self, name:str):
        if name in self.__log_files:
            '''
            if "chunk_collector" in self.__log_files[name]:
                pcallback = self.__log_files[name]["chunk_collector"]
                pcallback.stop()
            ''' 
            del self.__log_files[name]
            del self.__log_store[name]
            # Stop tail
    
    
    
    def enable_chunk_generation(self, logname:str) ->None:
        """ Enable logchunk collection. call collector every few seconds """
        if "chunk_collector" not in self.__log_files[logname]:
            callback = tornado.ioloop.PeriodicCallback(lambda: self.__chunk_collector(logname), self.__conf["chunks_collector_interval"])
            self.__log_files[logname]["chunk_collector"] = callback;
            callback.start()
        
        pass
    
    
    
    def disable_chunk_generation(self, logname:str) ->None:
        """ Disables logchunk collection. """
        if "chunk_collector" in self.__log_files[logname]:
                pcallback = self.__log_files[logname]["chunk_collector"]
                pcallback.stop()
                del self.__log_files[logname]["chunk_collector"]
                
        pass
            
            
    
    '''
    Get all log file keys that are used as topic names
    '''
    def get_log_keys(self):
        return self.__log_files.keys() 
    
    
    
    
    '''
    Get all log file keys that are used as topic names
    '''
    def get_log_info(self, name:str) ->Dict:
        if name in self.__log_files:
            return self.__log_files[name]
        else:
            raise LookupError('Log info not found for log by name ' + name)
        
        
        
    def get_log_path(self, name:str) ->Text:
        if name in self.__log_files:
            log_info = self.__log_files[name]
            return log_info["log_file_path"]
        else:
            raise LookupError('Log info not found for log by name ' + name)       
        
    
    
    
    def __schedule_chunk_processing(self, logname):
        self.enable_chunk_generation(logname)
        pass
    
    
    
    async def __chunk_collector(self, logname):
        try:    
            log_info = self.__log_files[logname]
            log_topic_path = log_info["topic_path"]
            log_file_path = log_info["log_file_path"]
            log_file = Path(str(log_file_path))
            
            if not log_file.exists():
                self.deregister_log_file(logname)
                raise Exception("Log file " + str(logname) + " does not exist at location " + str(log_file.absolute()))
            
            q = self.__log_store[logname];
            
            
            if len(q)>0: 
                log_chunk_topic_path = log_topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in log_topic_path else log_topic_path
                await self.dispatchevent(LogChunkEvent(log_chunk_topic_path, logkey=logname, chunk=q.copy()))
                self.__log_store[logname].clear()
                self.__log_store[logname] = None
                self.__log_store[logname] = collections.deque([], self.__conf["max_messages_chunks"])                    
        
        except Exception as e:
            
            err = "An error occurred in processing log chunks " + str(e)
            self.logger.warning(err)
            
            log_chunk_topic_path = log_topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in log_topic_path else log_topic_path 
            await self.dispatchevent(LogErrorEvent(log_chunk_topic_path, message=err, meta={"log_name": logname}))
            
        pass
        
    
    
    
    
    async def __tail(self, logname):
        
        try:    
            log_info = self.__log_files[logname]
            log_topic_path = log_info["topic_path"]
            log_file_path = log_info["log_file_path"]
            log_file = Path(str(log_file_path))
            
            log_mon_process = None
            
            if not log_file.exists():
                self.deregister_log_file(logname)
                raise Exception("Log file " + str(logname) + " does not exist at location " + str(log_file.absolute()))
            
            if platform == "linux" or platform == "linux2" :
                log_mon_process:Subprocess = Subprocess(["tail", "-n", "1", "-f", str(log_file.absolute())], stdout=Subprocess.STREAM)
            elif platform.startswith("win"):
                log_mon_process:Subprocess = Subprocess(["Get-Content", str(log_file.absolute()), "-Tail", "1" , "-Wait", "1"], stdout=Subprocess.STREAM)
            else:
                error = "Log monitoring is not supported on " + platform
                self.deregister_log_file(logname)
                raise Exception(error)
            
            
            while True:
                
                if logname not in self.__log_files:
                    break;
                
                line = await log_mon_process.stdout.read_until(b"\n")
                
                if not line:
                    await asyncio.sleep(.2)
                else:
                    await self.dispatchevent(LogEvent(log_topic_path, logkey=logname, logdata=line))
                        
                    ''' Collect log lines in a queue till  it reaches queue size limit'''    
                    q = self.__log_store[logname];
                    q.append(line)
                    
                    ''' max_messages_chunks < 100 causes bug while writing log '''
                    if len(q)>=self.__conf["max_messages_chunks"] :
                        log_chunk_topic_path = log_topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in log_topic_path else log_topic_path
                        await self.dispatchevent(LogChunkEvent(log_chunk_topic_path, logkey=logname, chunk=q.copy()))
                        self.__log_store[logname].clear()
                        self.__log_store[logname] = None
                        self.__log_store[logname] = collections.deque([], self.__conf["max_messages_chunks"]) 
        
        except Exception as e:
            
            err = "An error occurred in monitoring log." + str(e)
            self.logger.error(err)
            
            await self.dispatchevent(LogErrorEvent(log_topic_path, logkey=logname,error=err))
            
            if logname in self.__log_files:
                await self._retry(logname)
            else:
                self.logger.error("Log was de-registered from monitoring")            
        pass
    
    
    
    
    async def _retry(self, logname):
        wait_time = self.__conf["retry_time_gap_seconds"]
        self.logger.debug("Trying after %s seconds..", wait_time)
        await asyncio.sleep(wait_time)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__tail, logname)
        pass
    
    
    
        
    '''
        Returns a list of supported actions
    '''
    def supported_actions(self) -> List[object]:
        return [ActionLogBackUp()]


    '''
        Returns a list supported of action names
    '''
    def supported_action_names(self) -> List[Text]:
        return [ACTION_LOG_BACKUP_NAME]
    
    
    
    '''
        Returns a list supported of intents
    '''
    def supported_intents(self) -> List[Text]:
        return [INTENT_LOG_BACKUP_NAME]
    
    
    
    

class LogDownloadHandler(tornado.web.RequestHandler, LoggingHandler):
    
    CHUNK_SIZE = 256 * 1024
    
    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        pass
            

    async def post(self, slug=None):
        
        modules = self.application.modules
        
       
        if slug == "static":
            try:
                logmon:ILogMonitor = modules.getModule(LOG_MANAGER_MODULE)
                logname = self.get_argument("logname", None, True)
                log_info = logmon.get_log_info(logname)
                log_path = log_info["log_file_path"]
                download_path = await self.__makeFileDownloadable(log_path)
                self.write(json.dumps(formatSuccessResponse(download_path)))
            except Exception as e:
                self.write(json.dumps(formatErrorResponse(str(e), 404)))
            finally:
                self.finish()
        elif slug == "chunked"  or slug == None:
            try:
                logmon:ILogMonitor = modules.getModule(LOG_MANAGER_MODULE)
                logname = self.get_argument("logname", None, True)
                log_info = logmon.get_log_info(logname)
                log_path = log_info["log_file_path"]
                filemanager = modules.getModule(FILE_MANAGER_MODULE)
                file_name = filemanager.path_leaf(log_path)
                self.set_header('Content-Type', 'application/octet-stream')
                self.set_header('Content-Disposition', 'attachment; filename=' + file_name)
                await self.flush()
                await self.__makeChunkedDownload(log_path)
            except Exception as e:
                self.write(json.dumps(formatErrorResponse(str(e), 404)))
            finally:  
                self.finish()
                pass
        else:
            self.finish(json.dumps(formatErrorResponse("Invalid action request", 403)))
        pass
    
    
    async def __makeFileDownloadable(self,file_path):
        modules = self.application.modules
        filemanager = modules.getModule(FILE_MANAGER_MODULE)
        static_path = settings["static_path"]
        download_path = await filemanager.make_downloadable_static(static_path, file_path)
        return settings["static_folder"] + "/" + download_path
    
    
    async def __makeChunkedDownload(self, path):
        modules = self.application.modules
        filemanager = modules.getModule(FILE_MANAGER_MODULE)
        await filemanager.download_file_async(path, LogDownloadHandler.CHUNK_SIZE, self.handle_data)
        pass
    
    
    async def handle_data(self, chunk):
        self.logger.debug("Writing chunk data")
        self.write(chunk)
        await self.flush()
        pass





# custom intents
INTENT_LOG_BACKUP_NAME = INTENT_PREFIX + "logmon_log_backup"


# custom actions
ACTION_LOG_BACKUP_NAME = ACTION_PREFIX + "logmon_log_backup"


'''
Module action demo
'''
class ActionLogBackUp(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_LOG_BACKUP_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __filemanager = None
        
        if modules.hasModule(FILE_MANAGER_MODULE):
            __filemanager = modules.getModule(FILE_MANAGER_MODULE)
            src = params["source"]
            dest = params["destination"]
            
            now = datetime.now().strftime("%m_%d_%Y__%H_%M_%S")
            dest = dest.replace("{datetime}", now) # token replacement
            
            result = await __filemanager.copyFile(src, dest)
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+FILE_MANAGER_MODULE+"` module does not exist")
        pass
