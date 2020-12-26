'''
Created on 23-Dec-2020

@author: root
'''
import tornado
import os
from tornado.concurrent import Future
from tornado.process import Subprocess
from typing import Text, List, Dict
import signal
from abstracts import IEventDispatcher, IScriptRunner
from tornado.iostream import StreamClosedError
import logging
from smalluuid.smalluuid import SmallUUID
from core.event import EVENT_SCRIPT_EXECUTION_STOP,\
    EVENT_SCRIPT_EXECUTION_START, EVENT_SCRIPT_EXECUTION_PROGRESS,\
    ScriptExecutionEvent
from core.constants import TOPIC_SCRIPTS
from utilities import build_script_topic_path
from exceptions import RunnableScriptError



class ScriptRunner(IEventDispatcher, IScriptRunner):
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
        pass
        
        
    
    
    '''
    Returns indexed script names
    '''
    @property
    def script_names(self):
        return self.__scripts.keys()
    
        
        
    
    '''
    Sets executable scripts data from external provider via future object
    '''
    def script_files_from_future(self, future:Future):
        
        try:
            
            self.logger.debug("Setting scripts data from `Future`")
            
            files = future.result()
            
            for file in files:
                self.__scripts[file["name"]] = file["path"]
                #tornado.ioloop.IOLoop.current().spawn_callback(self.start_script, file["name"])
             
             
        except Exception as e:
            self.logger.error("Failed to fetch list of executable scripts. Cause: " + str(e))
                
        
    
    
    '''
    Getter for executable script data
    '''
    @property
    def on_scripts(self):
        return self.__scripts
    
    
    
    
    
    '''
    Setter for executable script data
    '''
    @on_scripts.setter
    def on_scripts(self, files):
        self.__scripts = files    
    
    
    
    
    
    
    
    '''
    Starts script execution by script name
    '''
    def start_script(self, name, args:str = None)->Text:
        
        runnable = None
        err = None
        
        try:
            if name not in self.__scripts.keys():
                raise LookupError()
            
            runnable = Runnable({"name":name, "path":self.__scripts[name]})
            runnable.update_handler = self.on_execution_update
            runnable.start(args)  
            
            return runnable.uuid
            
        except Exception as e:
            err = e
            self.logger.error("Error terminating process gracefully %s", str(e))
            raise RunnableScriptError(str(e))
        finally:
            
            if not err:
                self.__running_scripts[runnable.uuid] = runnable
    
    
    
    
    
    
    '''
    Stop script execution by generated script id
    '''
    def stop_script(self, script_id)->None:
        
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
            raise RunnableScriptError(str(e))
        
        finally:
            
            if not err:
                tornado.ioloop.IOLoop.current().spawn_callback(self.__script_execution_cleanup, script_id)
                
                
    
    
    
    
    '''
    Cleans up script from reference
    '''
    async def __script_execution_cleanup(self, script_id):
        runnable = self.__running_scripts[script_id]
        del runnable
        del self.__running_scripts[script_id]
        pass
                
    
    
    
    
    
    '''
    Async handler for script execution states
    '''                 
    async def on_execution_update(self, eventname:str, script_id:str, data:str = {})->None:
        
        try:
            topic =  build_script_topic_path(TOPIC_SCRIPTS, script_id)
            await self.dispatchevent(ScriptExecutionEvent(eventname, topic, data={"output": data}))
        
        except Exception as e:
            err = e
            self.logger.error("Error terminating process gracefully %s", str(e))
        
        finally:
            if eventname == EVENT_SCRIPT_EXECUTION_STOP:
                await self.__script_execution_cleanup(script_id)
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
        self.__update_handler = None     
        self.__running = False    
    
    
    
    '''
    Checks to see if script is running
    '''
    def is_running(self):
        return self.__running
    
    
    
    '''
    Returns the status update handler for this runnable instance 
    '''
    @property
    def update_handler(self):
        return self.__update_handler
    
    
    
    
    '''
    Sets the status update handler for this runnable instance 
    '''
    @update_handler.setter
    def update_handler(self, files):
        self.__update_handler = files
    
    
    
    
    '''
    Starts script execution process  
    '''
    def start(self, args:str)->None:
        
        parameters:List = []
        
        if args:
            args.strip()
            parameters = args.split(",")            
        
        cmd:List = ["bash", self.__script_path]
        cmd.extend(parameters)
        
        self.__process = Subprocess(cmd, stdout=Subprocess.STREAM, stderr=Subprocess.STREAM)
        self.__process.set_exit_callback(self.__process_closed)
        tornado.ioloop.IOLoop.current().spawn_callback(self._run)
    
    
    
    
    '''
    Returns the script id for this runnable instance 
    '''
    @property
    def uuid(self):
        return self.__id
    
    
    
    
    '''
    Captures script output in a loop, till the script executes and handles any abnormal exit accordingly  
    '''
    async def _run(self):    
        
        error = None
            
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
                    await self.__update_handler(EVENT_SCRIPT_EXECUTION_PROGRESS, self.uuid, line_str)
                
        except StreamClosedError as se:
            error = se
            self.logger.error("Stream closed")
                    
        except Exception as e:   
            error = e             
            self.logger.error("Error terminating process gracefully %s", str(e))            
        
        finally:            
            if error:
                await self.__process_closed()
            
        
    
    
    
    
    '''
    Stops script execution process  
    '''
    def stop(self)->None:
        try:
            if self.__running:
                pid = self.__process.pid
                os.kill(pid, signal.SIGTERM)
        except Exception as e:
            self.logger.error("Error terminating process gracefully %s", str(e))
        
        finally:
            tornado.ioloop.IOLoop.current().spawn_callback(self.__process_closed)
            
    
    
    
    
    '''
    handles Subprocess exit / execution termination
    ''' 
    async def __process_closed(self, param=None):
        if self.__running:
            self.__running = False
            if self.__update_handler:
                await self.__update_handler(EVENT_SCRIPT_EXECUTION_STOP, self.uuid)
        pass