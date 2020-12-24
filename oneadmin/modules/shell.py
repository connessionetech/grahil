'''
Created on 23-Dec-2020

@author: root
'''
import tornado
import os
from tornado.concurrent import Future
from tornado.process import Subprocess
from typing import Text
import signal
from abstracts import IEventDispatcher
import subprocess
from tornado.iostream import StreamClosedError
import logging
from smalluuid.smalluuid import SmallUUID
from core.event import EVENT_SCRIPT_EXECUTION_STOP,\
    EVENT_SCRIPT_EXECUTION_START, EVENT_SCRIPT_EXECUTION_PROGRESS,\
    ScriptExecutionEvent
from core.constants import TOPIC_SCRIPTS
from utilities import build_script_topic_path


class ScriptRunner(IEventDispatcher):
    '''
    classdocs
    '''


    def __init__(self, conf=None):
        '''
        Constructor
        '''
        
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.__conf = conf
        self.__scripts = {}
        self.__running_scripts = {}
        tornado.ioloop.IOLoop.current().spawn_callback(self.__initialize)
        pass
        
    
    
    def __initialize(self):
        pass    
    
    
    
    @property
    def script_names(self):
        return self.__scripts.keys()
    
        
        
    
    def script_files_from_future(self, future:Future):
        
        try:
            files = future.result()
            
            for file in files:
                self.__scripts[file["name"]] = file["path"]
                #tornado.ioloop.IOLoop.current().spawn_callback(self.start_script, file["name"])
             
             
        except Exception as e:
            self.logger.error("Failed to fetch list of executable scripts. Cause: " + str(e))
                
        
    
    @property
    def on_scripts(self):
        return self.__scripts
    
    
    
    @on_scripts.setter
    def on_scripts(self, files):
        self.__scripts = files    
    
    
    
    
    def start_script(self, name):
        
        runnable = None
        err = None
        
        try:
            if name not in self.__scripts.keys():
                raise LookupError()
            
            runnable = Runnable({"name":name, "path":self.__scripts[name]})
            runnable.update_handler = self.on_execution_update
            runnable.start()  
            
            return runnable.uuid
            
        except Exception as e:
            err = e
            self.logger.error("Error terminating process gracefully %s", str(e))
        
        finally:
            
            if not err:
                self.__running_scripts[runnable.uuid] = runnable
    
    
    
    
    
    def stop_script(self, script_id, force=False)->Text:
        
        runnable = None
        err = None
        
        try:
            if not script_id in self.__running_scripts.keys():
                raise LookupError()
            
            runnable = self.__running_scripts[script_id]
            runnable.update_handler = None
            runnable.stop()
            
        except Exception as e:
            err = e
            self.logger.error("Error terminating process gracefully %s", str(e))
        
        finally:
            
            if not err:
                del self.__running_scripts[script_id]
                
                
    async def on_execution_update(self, eventname:str, script_id:str, data:str = {})->None:
        topic =  build_script_topic_path(TOPIC_SCRIPTS, script_id)
        await self.dispatchevent(ScriptExecutionEvent(eventname, topic, data={"output": data}))
        pass
    



class Runnable(object):
    
    '''
    classdocs
    '''

    def __init__(self, script=None):
        '''
        Constructor
        '''
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.__id = SmallUUID().hex
        self.__script_name = script["name"]
        self.__script_path = script["path"]
        self.__process:Subprocess = None     
        self.__running = False
        self.__update_handler = None
    
    
    
    @property
    def update_handler(self):
        return self.__update_handler
    
    
    
    @update_handler.setter
    def update_handler(self, files):
        self.__update_handler = files
    
    
    
    
    def start(self):
        cmd = ["bash", self.__script_path]
        self.__process = Subprocess(cmd, stdout=Subprocess.STREAM, stderr=Subprocess.STREAM)
        self.__process.set_exit_callback(self.__process_closed)
        tornado.ioloop.IOLoop.current().spawn_callback(self._run)
    
    
    
    @property
    def uuid(self):
        return self.__id
    
    
    
    async def _run(self):        
        try:
            while True:

                line = await self.__process.stdout.read_until(b"\n")
                line_str:str = line.decode("utf-8")
                self.logger.debug(line_str)
                                
                if not self.__running:
                    self.__running = True
                    if self.__update_handler:
                        await self.__update_handler(EVENT_SCRIPT_EXECUTION_START, self.uuid)      
            
                
                if self.__update_handler:
                    await self.__update_handler(EVENT_SCRIPT_EXECUTION_PROGRESS, self.uuid, line)
                
        except StreamClosedError as se:
            self.logger.debug("Stream closed")
            await self.__process_closed()
                    
        except Exception as e:                
            self.logger.error("Error terminating process gracefully %s", str(e))
            await self.__process_closed()
        
    
    
    
    
    def stop(self):
        try:
            if self.__running:
                pid = self.__process.pid
                os.kill(pid, signal.SIGTERM)
        except Exception as e:
            self.logger.error("Error terminating process gracefully %s", str(e))
        
        finally:
            tornado.ioloop.IOLoop.current().spawn_callback(self.__process_closed)
            
    
    
    
    
    
    async def __process_closed(self, param=None):
        if self.__running:
            self.__running = False
            if self.__update_handler:
                await self.__update_handler(EVENT_SCRIPT_EXECUTION_STOP, self.uuid)
        pass