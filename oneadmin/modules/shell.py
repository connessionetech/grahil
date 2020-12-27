'''
Created on 23-Dec-2020

@author: root
'''
import tornado
import os
from tornado.concurrent import Future
from tornado.process import Subprocess
from typing import Text, List, Dict, Callable
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
from tornado.ioloop import IOLoop



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
        '''
        Returns a list of executable script names
        
                Parameters:
                        None
        
                Returns:
                        _names (set): A list of executable script names
        '''
        _names = self.__scripts.keys()
        return _names
    
        
        
    
    def script_files_from_future(self, future:Future)->None:
        '''
        Sets executable scripts data from external provider via future object
        
                Parameters:
                        future (Future): A Future object that provides executable scripts information
        
                Returns:
                        None
        '''
        
        try:
            
            self.logger.debug("Setting scripts data from `Future`")
            
            files = future.result()
            
            for file in files:
                self.__scripts[file["name"]] = file["path"]
                #tornado.ioloop.IOLoop.current().spawn_callback(self.start_script, file["name"])
             
             
        except Exception as e:
            self.logger.error("Failed to fetch list of executable scripts. Cause: " + str(e))
                
        
    
    
    @property
    def on_scripts(self) -> Dict:
        '''
        Getter for executable script data
    
                Parameters:
                        None
    
                Returns:
                        _scripts (Dict): A dictionary object representing data of executable scripts available to this module
        '''
        _scripts = self.__scripts
        return _scripts
    
    
    
    
    
    @on_scripts.setter
    def on_scripts(self, files:Dict) -> None:
        '''
        Setter for executable script data
    
                Parameters:
                        files (Dict): A dictionary object representing data of executable scripts  
    
                Returns:
                        None
        '''
        self.__scripts = files    
    
    
    
       
    
    
    def start_script(self, name:str, args:str = None)->Text:
        '''
        Starts script execution by script name
    
                Parameters:
                        name (str): Name of the script to be executed. Name must include extension
                        args (str): A comma separated string of argument needed for the script to be executed 
    
                Returns:
                        uuid (str): Unique id of the runnable script that was started
        '''
        
        runnable = None
        err = None
        
        try:
            if name not in self.__scripts.keys():
                raise LookupError()
            
            runnable = Runnable({"name":name, "path":self.__scripts[name]}, self.__conf["max_execution_time_seconds"])
            runnable.update_handler = self.on_execution_update
            runnable.start(args)  
            
            uuid = runnable.uuid
            return uuid
            
        except Exception as e:
            err = e
            self.logger.error("Error terminating process gracefully %s", str(e))
            raise RunnableScriptError(str(e))
        finally:
            
            if not err:
                self.__running_scripts[runnable.uuid] = runnable
    
    
    
    
    
    
    def stop_script(self, script_id:str)->None:
        '''
        Stop script execution by generated script id
    
                Parameters:
                        script_id (str): ID if the running script
    
                Returns:
                        None
        '''
        
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
                
                
    
    
    
    async def __script_execution_cleanup(self, script_id):
        """ Cleans up script from reference """
        runnable = self.__running_scripts[script_id]
        del runnable
        del self.__running_scripts[script_id]
        pass
    
    
    
    
    
    async def on_execution_update(self, eventname:str, script_id:str, data:str = {})->None:
        """ Async handler for script execution states. This method is called by all executing scripts to notify change of state. """
        
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

    def __init__(self, script, max_execution_time=60):
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
        self.__max_execution_time = max_execution_time
    
    
    
    
    def is_running(self) ->bool:
        """ Checks to see if script is running. Returns true if script is running, otherwise false """
        return self.__running
    
    
    
    
    @property
    def update_handler(self)->Callable:
        """ Returns the status update handler function for this runnable instance. """
        return self.__update_handler
    
    
    
    
    @update_handler.setter
    def update_handler(self, files) ->None:
        """ Sets the status update handler for this runnable instance. State changes are sent to this method. """
        self.__update_handler = files
    
    
    
    
    
    def start(self, args:str)->None:
        """ Starts script execution process   """
        
        parameters:List = []
        
        if args:
            args.strip()
            parameters = args.split(",")            
        
        cmd:List = ["bash", self.__script_path]
        cmd.extend(parameters)
        
        self.__process = Subprocess(cmd, stdout=Subprocess.STREAM, stderr=Subprocess.STREAM)
        IOLoop.current().call_later(self.__max_execution_time, self.__auto_terminate)
        self.__process.set_exit_callback(self.__process_closed)
        tornado.ioloop.IOLoop.current().spawn_callback(self._run)
    
    
    
    
    
    def __auto_terminate(self)->None:
        """ Check and terminate script if not already terminated. """
        if self.is_running():
            self.stop()
        pass
    
    
    
    
    
    @property
    def uuid(self):
        """ Returns the script id for this runnable instance """
        return self.__id
    
    
    
    
    async def _run(self):    
        
        """ Captures script output in a loop, till the script executes and handles any abnormal exit accordingly. """
        
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
            
        
        
    
    
    def stop(self)->None:
        """ Stops script execution process. """
        try:
            if self.__running:
                pid = self.__process.pid
                os.kill(pid, signal.SIGTERM)
        except Exception as e:
            self.logger.error("Error terminating process gracefully %s", str(e))
        
        finally:
            tornado.ioloop.IOLoop.current().spawn_callback(self.__process_closed)
            
    
    
    
    
    async def __process_closed(self, param=None):
        """ handles Subprocess exit / execution termination. """
        if self.__running:
            self.__running = False
            if self.__update_handler:
                await self.__update_handler(EVENT_SCRIPT_EXECUTION_STOP, self.uuid)
        pass