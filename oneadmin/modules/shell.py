'''
Created on 23-Dec-2020

@author: root
'''
import tornado
import os
from tornado.concurrent import Future
from tornado.process import Subprocess
import signal
from abstracts import IEventDispatcher
import subprocess
from tornado.iostream import StreamClosedError
import logging


class ScriptRunner(object):
    '''
    classdocs
    '''


    def __init__(self, conf=None):
        '''
        Constructor
        '''
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.__conf = conf
        self.__scripts = {}
        tornado.ioloop.IOLoop.current().spawn_callback(self.__initialize)
        pass
        
    
    
    def __initialize(self):
        pass    
    
    
    
    @property
    def script_files(self):
        return self.__scripts
    
    
    
    @script_files.setter
    def script_files(self, files):
        self.__scripts = files
    
    
    
    @property
    def script_names(self):
        return self.__scripts.keys()
    
        
        
    
    def script_files_from_future(self, future:Future):
        
        try:
            files = future.result()
            
            for file in files:
                self.__scripts[file["name"]] = file["path"]
                tornado.ioloop.IOLoop.current().spawn_callback(self.start_script, file)
             
             
        except Exception as e:
            self.logger.error("Failed to fetch list of executable scripts. Cause: " + str(e))
                
        
    
    @property
    def on_script_data(self):
        return self.__scripts
    
    
    
    @on_script_data.setter
    def on_script_data(self, files):
        self.__scripts = files    
    
    
    
    def start_script(self, script):
        
        r = Runnable(script)
        r.start()
        
        pass
    
    
    
    def stop_script(self, script_id, force=False):
        pass  
    



class Runnable(IEventDispatcher):
    
    '''
    classdocs
    '''

    def __init__(self, script=None):
        '''
        Constructor
        '''
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.__script_name = script["name"]
        self.__script_path = script["path"]
        self.__process:Subprocess = None     
        self.__running = False
    
    
    
    def start(self):
        cmd = ["bash", self.__script_path]
        self.__process = Subprocess(cmd, stdout=Subprocess.STREAM, stderr=Subprocess.STREAM)
        self.__process.set_exit_callback(self.__process_closed)
        tornado.ioloop.IOLoop.current().spawn_callback(self._run)
    
    
    
    async def _run(self):        
        try:
            while True:
                self.__running = True
                line = await self.__process.stdout.read_until(b"\n")
                line_str:str = line.decode("utf-8")
                self.logger.info(line_str)
                
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
            
    
    
    async def __process_closed(self, param=None):
        self.__running = False
        pass