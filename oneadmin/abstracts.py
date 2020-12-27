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



import os
import logging
import asyncio
from abc import abstractmethod
from builtins import int, str
from core.event import EventType
from typing import List, Text, Callable, Dict
from tornado.concurrent import Future





class IEventDispatcher(object):
    
    def __init__(self, handler:Callable=None):
        super().__init__()
        self.__eventHandler = None if handler == None else handler
        pass
    
    
    @property
    def eventhandler(self) ->Callable:
        return self.__eventHandler
    
    @eventhandler.setter
    def eventhandler(self, handler:Callable) ->None:
        self.__eventHandler = handler
        

    async def dispatchevent(self, event:EventType) -> None:
        if self.__eventHandler:
            await self.__eventHandler(event)
        pass


class TargetProcess(IEventDispatcher):
    '''
    classdocs
    '''


    def __init__(self, procname, root=None, service_path=None, invocable_namespace="do_fulfill"):
        '''
        Constructor
        '''
        self.__root=root
        self.__allowed_read_extensions = ['*']
        self.__allowed_write_extensions = ['*']
        self.__procname=procname
        self.__pid_procname=procname
        self.__service__path = service_path 
        self.__pid=None
        self.__starting_proc=False
        self.__stopping_proc=False
        self.__running_proc=False
        self.__log_paths = []
        self.__target_version = None
        self.__target_installed = False     
        self.__target_stats = None  
        self.__meta_info = {}
        self.__capabilities = {}
        self.__arbitrary_method_namespace=invocable_namespace
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__initialize()
    
    def __initialize(self):
        '''
        do init
        '''
        '''if(not os.path.isdir(self.__root)):
            ("Target location {} does not exist or is not a directory".format(self.__root))'''
    
    
    
    @property
    def eventcallback(self):
        return self.__event_callback
    
    
    @eventcallback.setter
    def eventcallback(self, fun):
        self.__event_callback = fun
    
    
    '''
        Checks to see if target is installed on the system or not
    '''
    def isTargetInstalled(self):
        return self.__target_installed
    
    
    
    '''
        Sets the installed state of target on the system or not
    '''
    def setTargetInstalled(self, installed):
        self.__target_installed = installed    
        
    '''
        Returns root path of the target
    '''
    def getRoot(self):
        return self.__root
    
    
    def getAllowedReadExtensions(self):
        return self.__allowed_read_extensions
    
    
    def setAllowedReadExtensions(self, extensions):
        if not isinstance(extensions, list):
            raise ValueError("Parameters should be of type `list`")
        self.__allowed_read_extensions = extensions
    
    
    def getAllowedWriteExtensions(self):
        return self.__allowed_write_extensions
    
    
    def setAllowedWriteExtensions(self, extensions):
        if not isinstance(extensions, list):
            raise ValueError("Parameters should be of type `list`")
        self.__allowed_write_extensions = extensions
    
    
    '''
        Returns process service file path (for systemd daemon). 
    '''
    def getServicePath(self):
        return self.__service__path
    
    
    '''
        Sets process service file path (for systemd daemon). 
    '''
    def setServicePath(self, path):
        self.__service__path = path
    
    '''
        Returns process name of the target
    '''
    def getProcName(self):
        return self.__procname   
    
    
    '''
        Returns process name for the PID representing the process
    '''
    def getPidProcName(self):
        return self.__pid_procname
    
    
    '''
        Sets process name for the PID representing the process
    '''
    def setPidProcName(self, procname):
        self.__pid_procname = procname
     
    
    '''
        Returns version of the target
    '''
    def getProcVersion(self):
        return self.__target_version
    
    
    '''
        Returns target specific stats
    '''
    def getTargetStats(self):
        return self.__target_stats
    
    
    '''
        Sets target specific stats
    '''
    def setTargetStats(self, stats):
        self.__target_stats = stats
    
    
    '''
        Process log line. This is called by log tailer.
        Original data is not changed. This is simply a hook to provide 
        log data to the TargetDelegate for analysis and consumption 
    '''
    async def processLogLine(self, line):
        await asyncio.sleep(.01)
        pass 
    
    
    def setProcVersion(self, ver):
        self.__target_version = ver
    
    '''
        Returns PID of the target
    '''
    def getTargetPid(self):
        return self.__pid 
    
    
    
    '''
        Sets target process id (PID)
    '''
    def setTargetPid(self, pid):
        self.__pid = pid
        
        
    
    '''
        Gets list of log paths for the target
    '''
    def getLogFiles(self):
        return self.__log_paths
    
    
    
    '''
        Sets list of log paths for the target
    '''
    def setLogFiles(self, log_paths):
        self.__log_paths = log_paths
        
    
    
    '''
        Checks to see if target is starting up or not.
        Returns true if running, false otherwise
    '''
    def is_proc_starting(self):
        return self.__starting_proc
    
    
    
    '''
        Sets primary log path of the target
    '''
    def set_proc_starting(self, starting):
        self.__starting_proc = starting
    
    
    '''
        Checks to see if target is stopping or not.
        Returns true if stopping, false otherwise
    '''
    def is_proc_stopping(self):
        return self.__stopping_proc
    
    
    
    '''
        Sets process stopping state
    '''
    def set_proc_stopping(self, stopping):
        self.__stopping_proc = stopping
    
    
    '''
        Checks to see if target is running or not.
        Returns true if running, false otherwise
    '''
    def is_proc_running(self):
        return self.__running_proc
    
    
    
    '''
        Sets process running state
    '''
    def set_proc_running(self, running):
        self.__running_proc = running
    
    
    '''
        Attempts to start process if not already started
    '''
    @abstractmethod
    def start_proc(self): 
        pass
    
    
    '''
        Attempts to stop process if not already stopped
    '''
    @abstractmethod
    def stop_proc(self):
        pass
    
    
    '''
        Attempts to restart process
    '''
    @abstractmethod
    def restart_proc(self):
        pass
    
    
    '''
        Checks to see if os level service is installed for the process
    '''
    def is_service_installed(self):
        if(not self.__service__path is None):
            return self._file_exists(self.__service__path)
        else:
            return False
    

    '''
        Returns any meta info about the target
    '''
    def get_target_meta(self):
        return self.__meta_info
    

    '''
        Set arbitrary target meta info about the target
    '''    
    def set_target_meta(self, meta):
        self.__meta_info = meta
        
    
    '''
        Returns declared capabilities (services provided) by the target delegate
    '''
    def get_target_capabilities(self):
        return self.__capabilities
    

    '''
        Set declared capabilities (services provided) by the target delegate
    '''    
    def set_target_capabilities(self, capabilities):
        self.__capabilities = capabilities
        
    
    '''
        Arbitrary method to accept command as string along with parameters. 
        Method should always be executed in asynchronous manner
        
        command - Command as String
        params - Parameters as dictionary
    '''
    async def fulfillRequest(self, command, params=None):
            method_name=self.__arbitrary_method_namespace + "_" + str(command)
            method=getattr(self,method_name, None)
            if(method == None or not callable(method)):
                raise Exception("Attempt to invoke invalid method %s", command)
            else:
                return await method(*params) # method(command, params)
            
            
    
    
    
    '''
        Arbitrary method to accept command as string along with parameters. 
        Method should always be executed in synchronous manner
        
        command - Command as String
        params - Parameters as dictionary
    '''
    def fulfillRequest_sync(self, command, params=None):
        method_name=self.__arbitrary_method_namespace + "_" + str(command)
        method=getattr(self,method_name, None)
        if(method == None or not callable(method)):
            raise Exception("Attempt to invoke invalid method %s", command)
        else:
            return method(*params) 
    
    
            
            

    '''
        Method to handle reaction from reaction engine
    '''
    async def on_reaction(self, ruleid, event, params=None):
        self.logger.debug("Event reaction for rule %s", ruleid)
        asyncio.sleep(.5)
        pass
    
    
    '''
        Method to run diagonistics on target
    ''' 
    def run_diagonistics(self):
        asyncio.sleep(.1)
        return None
        pass
            
    
    
    def _file_exists(self, path):
        if os.path.isfile(path):
            return True
        else:
            return False
    
    
    # Return type should be Action but for some reason it cannot be imported into this file
    def supported_actions(self) -> List[object]:
        return []



    def supported_action_names(self) -> List[Text]:
        return []
    
    
    def supported_intents(self) -> List[Text]:
        return []
    
    
    # Return type should be Action but for some reason it cannot be imported into this file
    def action_from_name(self, name:Text) -> object:
        defaults = {a.name(): a for a in self.supported_actions()}
        if name in defaults:
            return defaults.get(name)
                
        return None
    



class EventHandler(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
        self.__topics_of_interest = []
        self.__events_of_interest = []
      
    
    def get_events_of_interests(self)-> List:
        return self.__events_of_interest 
    
    
    def get_topics_of_interests(self)-> List:
        return self.__topics_of_interest        
        
        
    async def _notifyEvent(self, event:EventType):
        if event["topic"] in self.get_topics_of_interests():
            if event["name"] in self.get_events_of_interests():
                await self.handleEvent(event)
        pass
    
    
    async def handleEvent(self, event):
        pass  
    



class ServiceBot(IEventDispatcher):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
        self._initialize()
        pass
        
        
    def _initialize(self):
        self.__webhook = False
        self.__supports_webhook = False
        self.__webhook_handler_url_config = None
        self.__webhook_secret = None
        pass
    
    
    
    def is_webhook_supported(self):
        return self.__supports_webhook
    
    
    def set_webhook_supported(self, supports):
        self.__supports_webhook = bool(supports)
    
    
    def set_webhook(self, url):
        self.__webhook = url
        return False
    
    
    def get_webhook(self):
        return self.__webhook
    
    
    def get_webhook_url_config(self):
        return self.__webhook_handler_url_config
    
    
    def set_webhook_url_config(self, urlconfig):
        self.__webhook_handler_url_config = urlconfig
        


class IntentProvider(object):
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
    

    def onIntentProcessResult(self, requestid:str, result:object) -> None:
        pass


    def onIntentProcessError(self, e:object, message:str = None) -> None:
        pass
    
    

class IClientChannel(object):
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
        
        
        
class IMailer(object):
    
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
        
    
    async def send_mail(self, subject:Text, body:Text) ->None:
        raise NotImplementedError()
        pass
    



class IMQTTClient(object):
    
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
        self.__topic_data_handler = None
        
    
    async def publish_to_topic(self, topic:str, message:str, callback:Callable=None)->None:
        raise NotImplementedError()
        pass
    
    
    
    async def publish_to_topics(self, topics:List[str], message:str, callback:Callable=None)->None:
        raise NotImplementedError()
        pass
    
    
    @property
    def on_data_handler(self) ->Callable:
        return self.__topic_data_handler
    
    
    @on_data_handler.setter
    def on_data_handler(self, handler:Callable) ->None:
        self.__topic_data_handler = handler
        
        


class IScriptRunner(object):
    
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
        

    
    async def start_script(self, name) ->Text:
        raise NotImplementedError()
        pass
    
    
    
    def stop_script(self, script_id)->Text:
        raise NotImplementedError()
    
    
   
    def script_files_from_future(self, future:Future):
        raise NotImplementedError()
        pass
    


class ILogMonitor(object):
    
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
    
    
    
    def register_log_file(self, log_info:Dict):
        raise NotImplementedError()
        pass
    
    
    def deregister_log_file(self, name:str):
        raise NotImplementedError()
        pass
    
    
    def get_log_keys(self):
        raise NotImplementedError()
        pass
    
    def get_log_Info(self, name:str) ->Dict:
        raise NotImplementedError()
        pass 
    


class ISystemMonitor(object):
    
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
    
    
    
    def start_monitor(self) -> None:
        raise NotImplementedError()
        pass
    
    
    def get_cpu_stats(self, cached=False) ->Dict:
        raise NotImplementedError()
        pass
    
    
    def get_memory_stats(self, unit = "b", cached=False) ->Dict:
        raise NotImplementedError()
        pass
    
    
    def schedule__update(self, updater_script:str) ->str:
        raise NotImplementedError()
        pass
    
    
    def force_gc(self) ->None:
        raise NotImplementedError()
        pass
    
    
    def get_version(self) -> str:
        raise NotImplementedError()
        pass
    
    
    def get_last_system_stats_snapshot(self) -> Dict:
        raise NotImplementedError()
        pass
    
    
    def get_system_time(self) -> str:
        raise NotImplementedError()
        pass
    