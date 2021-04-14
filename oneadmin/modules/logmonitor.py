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

from oneadmin.abstracts import IModule, ILogMonitor
from oneadmin.core.event import LogLineEvent, LogErrorEvent, LogChunkEvent
from oneadmin.utilities import buildTopicPath
from oneadmin.core.constants import TOPIC_LOGMONITORING

import logging
import tornado
import collections
from tornado.process import Subprocess
from tornado.concurrent import asyncio
from sys import platform
from pathlib import Path
from typing import Dict, Text


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
    
    
    
    
    def register_static_log_targets(self)->None:
        
        ''' 
        Register static log targets of target 
        '''
        
        static_log_targets = self.__conf["static_targets"]
        if static_log_targets != None:
            for log_target in static_log_targets: 
                if log_target["enabled"] == True:
                    
                    if not log_target["topic_path"]:
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
                log_topic_path = log_topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in log_topic_path else log_topic_path
                await self.dispatchevent(LogChunkEvent(log_topic_path, data={"content": q.copy()}, meta={"log_name": logname}))
                self.__log_store[logname].clear()
                self.__log_store[logname] = None
                self.__log_store[logname] = collections.deque([], self.__conf["max_messages_chunks"])                    
        
        except Exception as e:
            
            err = "An error occurred in processing log chunks " + str(e)
            self.logger.warning(err)
            
            log_topic_path = log_topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in log_topic_path else log_topic_path 
            await self.dispatchevent(LogErrorEvent(log_topic_path, message=err, meta={"log_name": logname}))
            
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
                    self.logger.debug("nothing to show")
                    await asyncio.sleep(.2)
                else:
                    await self.dispatchevent(LogLineEvent(log_topic_path, data={"output": str(line, 'utf-8')}, meta={"log_name": logname}))
                        
                    ''' Collect log lines in a queue till  it reaches queue size limit'''    
                    q = self.__log_store[logname];
                    q.append(line)
                    
                    ''' max_messages_chunks < 100 causes bug while writing log '''
                    if len(q)>=self.__conf["max_messages_chunks"] :
                        log_topic_path = log_topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in log_topic_path else log_topic_path
                        await self.dispatchevent(LogChunkEvent(log_topic_path, data={"content": q.copy()}, meta={"log_name": logname}))
                        self.__log_store[logname].clear()
                        self.__log_store[logname] = None
                        self.__log_store[logname] = collections.deque([], self.__conf["max_messages_chunks"]) 
        
        except Exception as e:
            
            err = "An error occurred in monitoring log." + str(e)
            self.logger.warning(err)
            
            await self.dispatchevent(LogErrorEvent(log_topic_path, message=err, meta={"log_name": logname}))
            
            if logname in self.__log_files:
                await self._retry(logname)
            else:
                self.logger.warning("Log was de-registered from monitoring")            
        pass
    
    
    
    
    async def _retry(self, logname):
        wait_time = self.__conf["retry_time_gap_seconds"]
        self.logger.debug("Trying after %s seconds..", wait_time)
        await asyncio.sleep(wait_time)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__tail, logname)
        pass
    