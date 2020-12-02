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

from tornado.process import Subprocess
from tornado.concurrent import asyncio
import logging
import tornado
from sys import platform
from pathlib import Path
import collections
from abstracts import IEventDispatcher
from core.events import LogLineEvent, LogErrorEvent, LogChunkEvent


class LogMonitor(IEventDispatcher):
    '''
    classdocs
    '''

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
    
    
    '''
    Register new log file for monitoring
    '''
    def registerLogFile(self, log_info):
        
        name = log_info["name"]
        if not name in self.__log_files:
            self.__log_files[name] = log_info
            self.__log_store[name] = collections.deque([], self.__conf["max_messages_chunks"])
            tornado.ioloop.IOLoop.current().spawn_callback(self.__tail, name)
            tornado.ioloop.IOLoop.current().spawn_callback(self.__schedule_chunk_processing, name)    
    
    
    '''
    Deregister existing log file from monitoring
    '''
    def deregisterLogFile(self, name):
        if name in self.__log_files:
            pcallback = self.__log_files[name]["chunk_collector"]
            pcallback.stop()
            del self.__log_files[name]
            del self.__log_store[name]
            # Stop tail
            
            
    
    '''
    Get all log file keys that are used as topic names
    '''
    def getLogFileKeys(self):
        return self.__log_files.keys() 
    
    
    
    
    '''
    Get all log file keys that are used as topic names
    '''
    def getLogInfo(self, name):
        if name in self.__log_files:
            return self.__log_files[name]
        else:
            raise LookupError('Log info not found for log by name ' + name)
        
    
    
    ''' call collector every 15 seconds '''
    def __schedule_chunk_processing(self, logname):
        callback = tornado.ioloop.PeriodicCallback(lambda: self.__chunk_collector(logname), self.__conf["chunks_collector_interval"])
        self.__log_files[logname]["chunk_collector"] = callback;
        callback.start()
        pass
    
    
    
    async def __chunk_collector(self, logname):
        try:    
            log_info = self.__log_files[logname]
            log_topic_path = log_info["topic_path"]
            log_file_path = log_info["log_file_path"]
            log_file = Path(str(log_file_path))
            
            if not log_file.exists():
                self.deregisterLogFile(logname)
                raise Exception("Log file %s does not exist at location %s ", logname,  str(log_file.absolute()))
            
            q = self.__log_store[logname];
            
            
            if len(q)>0: 
                log_topic_path = log_topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in log_topic_path else log_topic_path
                await self.dispatchevent(LogChunkEvent(log_topic_path, data=q.copy(), meta={"log_name": logname}))
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
                self.deregisterLogFile(logname)
                raise Exception("Log file %s does not exist at location %s ", logname,  str(log_file.absolute()))
            
            if platform == "linux" or platform == "linux2" :
                log_mon_process = Subprocess(["tail", "-n", "1", "-f", str(log_file.absolute())], stdout=Subprocess.STREAM)
            elif platform.startswith("win"):
                log_mon_process = Subprocess(["Get-Content", str(log_file.absolute()), "-Tail", "1" , "-Wait", "1"], stdout=Subprocess.STREAM)
            else:
                error = "Log monitoring is not supported on " + platform
                self.deregisterLogFile(logname)
                raise Exception(error)
            
            
            while True:
                
                if logname not in self.__log_files:
                    break;
                
                line = await log_mon_process.stdout.read_until(b"\n")
                if not line:
                    self.logger.debug("nothing to show")
                    await asyncio.sleep(.2)
                else:
                    
                    self.dispatchevent(LogLineEvent(log_topic_path, data=str(line, 'utf-8'), meta={"log_name": logname}))
                        
                    ''' Collect log lines in a queue till  it reaches queue size limit'''    
                    q = self.__log_store[logname];
                    q.append(line)
                    
                    ''' max_messages_chunks < 100 causes bug while writing log '''
                    if len(q)>=self.__conf["max_messages_chunks"] :
                        log_topic_path = log_topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in log_topic_path else log_topic_path
                        await self.dispatchevent(LogChunkEvent(log_topic_path, data=q.copy(), meta={"log_name": logname}))
                        
                        self.__log_store[logname].clear()
                        self.__log_store[logname] = None
                        self.__log_store[logname] = collections.deque([], self.__conf["max_messages_chunks"]) 
        
        except Exception as e:
            
            err = "An error occurred in monitoring log." + str(e)
            self.logger.warning(err)
            
            self.dispatchevent(LogErrorEvent(log_topic_path, message=err, meta={"log_name": logname}))
            
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
    