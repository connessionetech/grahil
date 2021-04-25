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

from oneadmin.core import grahil_types
from oneadmin.core.constants import *
from oneadmin.core.event import EventType, StartLogRecordingEvent, StopLogRecordingEvent
from oneadmin.core.constants import SMTP_MAILER_MODULE, TOPIC_LOG_ACTIONS, FILE_MANAGER_MODULE, LOG_MANAGER_MODULE
from oneadmin.core.abstracts import IntentProvider, IMailer, IScriptRunner, ILogMonitor, TargetProcess
from oneadmin.core.utilities import buildLogWriterRule
from oneadmin.exceptions import RulesError
from oneadmin.security.decorators import authorize__action
from oneadmin.version import __version__

import urllib
import logging
import json
from tornado.concurrent import asyncio
from typing import Text, Dict, List,NamedTuple
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError, MissingArgumentError





logger = logging.getLogger(__name__)    


ACTION_PREFIX = "action_"

ACTION_TEST_NAME = ACTION_PREFIX + "test"

ACTION_GET_SOFTWARE_VERSION_NAME = ACTION_PREFIX + "get_software_version"

ACTION_HTTP_GET_NAME = ACTION_PREFIX + "http_get"

ACTION_UPDATE_SOFTWARE_NAME = ACTION_PREFIX + "update_software"

ACTION_REBOOT_SYSTEM_NAME = ACTION_PREFIX + "reboot_system"

ACTION_GET_SYSTEM_TIME_NAME = ACTION_PREFIX + "get_system_time"

ACTION_FORCE_GARBAGE_COLLECTION_NAME = ACTION_PREFIX + "force_garbage_collection"

ACTION_GET_SYSTEM_STATS_NAME = ACTION_PREFIX + "get_system_stats"

ACTION_GET_MEMORY_STATS_NAME = ACTION_PREFIX + "get_memory_stats"

ACTION_GET_CPU_STATS_NAME = ACTION_PREFIX + "get_cpu_stats"

ACTION_START_LOG_RECORDING_NAME = ACTION_PREFIX + "start_log_recording"

ACTION_STOP_LOG_RECORDING_NAME = ACTION_PREFIX + "stop_log_recording"

ACTION_START_SCRIPT_EXECUTION_NAME = ACTION_PREFIX + "start_script_execution"

ACTION_STOP_SCRIPT_EXECUTION_NAME = ACTION_PREFIX + "stop_script_execution"

ACTION_CREATE_FOLDER_NAME = ACTION_PREFIX + "create_folder"

ACTION_DELETE_FOLDER_NAME = ACTION_PREFIX + "delete_folder"

ACTION_DELETE_FILE_NAME = ACTION_PREFIX + "delete_file"

ACTION_COPY_FILE_NAME = ACTION_PREFIX + "copy_file"

ACTION_READ_FILE_NAME = ACTION_PREFIX + "read_file"

ACTION_MOVE_FILE_NAME = ACTION_PREFIX + "move_file"

ACTION_DOWNLOAD_FILE_NAME = ACTION_PREFIX + "download_file"

ACTION_BROWSE_FILE_SYSTEM_NAME = ACTION_PREFIX + "browse_fs"

ACTION_INVOKE_ON_TARGET_NAME = ACTION_PREFIX + "fulfill_target_request"

ACTION_RESTART_TARGET_NAME = ACTION_PREFIX + "restart_target"

ACTION_STOP_TARGET_NAME = ACTION_PREFIX + "stop_target"

ACTION_START_TARGET_NAME = ACTION_PREFIX + "start_target"

ACTION_SUBSCRIBE_CHANNEL_NAME = ACTION_PREFIX + "subscribe_channel"

ACTION_UNSUBSCRIBE_CHANNEL_NAME = ACTION_PREFIX + "unsubscribe_channel"

ACTION_REMOVE_CHANNEL_NAME = ACTION_PREFIX + "remove_channel"

ACTION_CREATE_CHANNEL_NAME = ACTION_PREFIX + "create_channel"

ACTION_PUBLISH_CHANNEL_NAME = ACTION_PREFIX + "publish_channel"

ACTION_RUN_DIAGNOSTICS_NAME = ACTION_PREFIX + "run_diagnostics"

ACTION_SEND_MAIL_NAME = ACTION_PREFIX + "send_mail"

ACTION_WRITE_LOG_CHUNKS_NAME = ACTION_PREFIX + "write_log_chunks"

ACTION_LIST_LOGS_NAME = ACTION_PREFIX + "list_logs"

ACTION_BOT_NOTIFY_NAME = ACTION_PREFIX + "bot_notify"




class ActionResponse(NamedTuple):
    data:object = None
    events:List[EventType] = []
    pass



class Action(object):
    '''
    classdocs
    '''
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        raise NotImplementedError
    
    
    
    '''
    Declares whether the action is asynchronous or synchronous
    '''
    def is_async(self) -> bool:
        return True
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        return ActionResponse()
    
    
    
    '''
    spits out string name of action
    '''
    def __str__(self) -> Text:
        return "Action('{}')".format(self.name())
    



'''
Returns instances of builtin actions
'''
def builtin_actions() -> List[Action]:
    return [ActionGetSoftwareVersion(), ActionRebootSystem(), ActionGetSystemTime(), 
            ActionForceGarbageCollection(), ActionGetSystemStats(), ActionGetMemoryStats(), 
            ActionGetCPUStats(), ActionStartLogRecording(), ActionStopLogRecording(),
            ActionCreateFolder(), ActionDeleteFolder(), ActionDeleteFile(), ActionCopyFile(), 
            ActionMoveFile(), ActionDownloadFile(), ActionBrowseFileSystem(), ActionFulfillTargetRequest(), 
            ActionStartTarget(), ActionStopTarget(), ActionRestartTarget(), 
            ActionSubcribeChannel(), ActionUnSubcribeChannel(), ActionCreateChannel(), 
            ActionRemoveChannel(), ActionPublishChannel(), ActionRunDiagonitics(), ActionUnUpdateSoftwre(), 
            ActionHttpGet(), ActionSendMail(), ActionStartScriptExecution(), ActionStopScriptExecution(),
            ActionTest(), ActionWriteLogChunks(), ActionBotNotify(), ActionListLogs()]




def builtin_action_names() -> List[Text]:
    return [a.name() for a in builtin_actions()]




def action_from_name(name:Text) -> Action:
    defaults = {a.name(): a for a in builtin_actions()}
    if name in defaults:
        return defaults.get(name)
    
    return None




'''
Retreives grahil version
'''
class ActionGetSoftwareVersion(Action):


    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_GET_SOFTWARE_VERSION_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __sysmon = None
        if modules.hasModule(SYSTEM_MODULE):
                __sysmon = modules.getModule(SYSTEM_MODULE)
                __ver = __sysmon.get_version()
                return ActionResponse(data = __ver, events=[])
        else:
                raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        pass
         
    
    



'''
Reboots system [ needs admin rights to the python script ]
'''
class ActionRebootSystem(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_REBOOT_SYSTEM_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __sysmon = None
        
        if modules.hasModule(SYSTEM_MODULE):
            __sysmon = modules.getModule(SYSTEM_MODULE)
            result =  __sysmon.rebootSystem()
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        pass
        
         



'''
Triggers garbage collector on python
'''
class ActionForceGarbageCollection(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_FORCE_GARBAGE_COLLECTION_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __sysmon = None
        
        if modules.hasModule("sysmon"):
            __sysmon = modules.getModule("sysmon")        
            __sysmon.force_gc()
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`sysmon` module does not exist")
        
    
    
    
'''
Retreives system time
'''
class ActionGetSystemTime(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_GET_SYSTEM_TIME_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __sysmon = None
        
        if modules.hasModule(SYSTEM_MODULE):
            __sysmon = modules.getModule(SYSTEM_MODULE) 
            result =  __sysmon.get_system_time()
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        pass       
 
 
 
 
'''
Retreives system stats
'''
class ActionGetSystemStats(Action):
    
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_GET_SYSTEM_STATS_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __sysmon = None
        
        if modules.hasModule(SYSTEM_MODULE):
            __sysmon = modules.getModule(SYSTEM_MODULE)        
            result =  __sysmon.get_last_system_stats_snapshot()
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        
    

'''
Retreives memory stats
'''
class ActionGetMemoryStats(Action):
    
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_GET_MEMORY_STATS_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __sysmon = None
        
        if modules.hasModule(SYSTEM_MODULE):
            __sysmon = modules.getModule(SYSTEM_MODULE)
            result =  __sysmon.get_memory_stats()
            await asyncio.sleep(.5)
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
    
    
    
'''
Retreives cpu stats
'''
class ActionGetCPUStats(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_GET_CPU_STATS_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __sysmon = None
        
        if modules.hasModule(SYSTEM_MODULE):
            __sysmon = modules.getModule(SYSTEM_MODULE)        
            result =  __sysmon.get_cpu_stats()
            await asyncio.sleep(.5)
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        
    
    


'''
Deletes a file
'''
class ActionDeleteFile(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_DELETE_FILE_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __filemanager = None
        
        if modules.hasModule(FILE_MANAGER_MODULE):
            __filemanager = modules.getModule(FILE_MANAGER_MODULE)
            path = str(params["source"])
            result = await __filemanager.deleteFile(path)
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+FILE_MANAGER_MODULE+"` module does not exist")        



'''
Moves a file
'''
class ActionMoveFile(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_MOVE_FILE_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __filemanager = None
        
        if modules.hasModule(FILE_MANAGER_MODULE):
            __filemanager = modules.getModule(FILE_MANAGER_MODULE)
            src = params["source"]
            dest = params["destination"]
            result = await __filemanager.moveFile(src, dest)
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+FILE_MANAGER_MODULE+"` module does not exist")




'''
Copies a file
'''
class ActionCopyFile(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_COPY_FILE_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __filemanager = None
        
        if modules.hasModule(FILE_MANAGER_MODULE):
            __filemanager = modules.getModule(FILE_MANAGER_MODULE)
            src = params["source"]
            dest = params["destination"]
            result = await __filemanager.copyFile(src, dest)
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+FILE_MANAGER_MODULE+"` module does not exist")
        


'''
Copies a file
'''
class ActionReadFile(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_READ_FILE_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __filemanager = None
        
        if modules.hasModule(FILE_MANAGER_MODULE):
            __filemanager = modules.getModule(FILE_MANAGER_MODULE)
            src = params["source"]
            result = await __filemanager.readFile(src)
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+FILE_MANAGER_MODULE+"` module does not exist")



'''
Downloads a file
'''
class ActionDownloadFile(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_DOWNLOAD_FILE_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        raise NotImplementedError()
        return ActionResponse(data = None, events=[])




'''
Downloads a file
'''
class ActionCreateFolder(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_CREATE_FOLDER_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __filemanager = None
        
        if modules.hasModule(FILE_MANAGER_MODULE):
            __filemanager = modules.getModule(FILE_MANAGER_MODULE)
            path = params["path"]
            dirname = params["name"]
            result = await __filemanager.create_directory(path, dirname)
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+FILE_MANAGER_MODULE+"` module does not exist")




'''
Downloads a file
'''
class ActionDeleteFolder(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_DELETE_FOLDER_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        if modules.hasModule(FILE_MANAGER_MODULE):
            __filemanager = modules.getModule(FILE_MANAGER_MODULE)
            path = params["path"]
            dirname = params["name"]
            result = await __filemanager.remove_folder(path, dirname)
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+FILE_MANAGER_MODULE+"` module does not exist")




'''
Browser filesystem content
'''
class ActionBrowseFileSystem(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_BROWSE_FILE_SYSTEM_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __filemanager = None
        
        if modules.hasModule(FILE_MANAGER_MODULE):
            __filemanager = modules.getModule(FILE_MANAGER_MODULE)
            handler = params["handler"]
            path = str(params["path"])
            result = await __filemanager.browse_content(path)
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`FileManager` module does not exist")





class ActionFulfillTargetRequest(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_INVOKE_ON_TARGET_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __delegate = None
        
        if modules.hasModule(TARGET_DELEGATE_MODULE):
            __delegate = modules.getModule(TARGET_DELEGATE_MODULE)
            if(len(params)<1):
                raise Exception("Minimum of one parameter is required for this method call")            
            command = params["command"]
            del params["command"]
            result =  await __delegate.fulfillRequest(command, params)
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+TARGET_DELEGATE_MODULE+"` module does not exist")
        pass
        
    
    


class ActionPublishChannel(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_PUBLISH_CHANNEL_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __pubsubhub = None
        
        if modules.hasModule(PUBSUBHUB_MODULE):
            __pubsubhub = modules.getModule(PUBSUBHUB_MODULE)
            handler = params["handler"] 
            topicname = params["topic"]  
            message = params["message"]        
            __pubsubhub.publish(topicname, message, handler)
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`"+PUBSUBHUB_MODULE+"` module does not exist")




class ActionCreateChannel(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_CREATE_CHANNEL_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __pubsubhub = None
        
        if modules.hasModule(PUBSUBHUB_MODULE):
            __pubsubhub = modules.getModule(PUBSUBHUB_MODULE)
            channel_info = params["channel_info"]  
            __pubsubhub.createChannel(channel_info)
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`"+PUBSUBHUB_MODULE+"` module does not exist")
        
    
    

class ActionRemoveChannel(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_REMOVE_CHANNEL_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __pubsubhub = None
        
        if modules.hasModule(PUBSUBHUB_MODULE):
            __pubsubhub = modules.getModule(PUBSUBHUB_MODULE)
            channel_name = params["topic"]        
            __pubsubhub.removeChannel(channel_name)
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`"+PUBSUBHUB_MODULE+"` module does not exist")
        
    
    


class ActionRunDiagonitics(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_RUN_DIAGNOSTICS_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        raise NotImplementedError()
        return ActionResponse(data = None, events=[])
    
    

class ActionStartLogRecording(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_START_LOG_RECORDING_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __logmon = None
        
        if modules.hasModule(LOG_MANAGER_MODULE):
            __logmon = modules.getModule(LOG_MANAGER_MODULE)
            handler = params["handler"]
            log_name = params["name"] # log name
            log_info = __logmon.get_log_info(log_name)
            
            if hasattr(handler, 'id') and "logrecordings" in handler.liveactions:
                rule_id = handler.id + '-' + log_name
                
                if rule_id in handler.liveactions['logrecordings']:
                    raise LookupError("log recording is already active for this log")
                
                topic_path = log_info["topic_path"]
                topic_path = topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in topic_path else topic_path
                filepath = log_info["log_file_path"]
                rule = buildLogWriterRule(rule_id, topic_path, filepath) #Dynamic rule generation
                
                # tell logmon to enable chunk generation
                __logmon.enable_chunk_generation(log_name)
                
                # store reference on client handler
                handler.liveactions['logrecordings'].add(rule_id) 
                event = StartLogRecordingEvent(topic=TOPIC_LOG_ACTIONS, data=rule)
                return ActionResponse(data = rule_id, events=[event])
        else:
            raise ModuleNotFoundError("`"+LOG_MANAGER_MODULE+"` module does not exist")
        
        




class ActionStopLogRecording(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_STOP_LOG_RECORDING_NAME
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __logmon = None
        
        if modules.hasModule(LOG_MANAGER_MODULE):
            __logmon = modules.getModule(LOG_MANAGER_MODULE)
            handler = params["handler"]
            
            if hasattr(handler, 'id'):
                rule_id:str = params["rule_id"]
                log_name:str = rule_id.replace(handler.id + "-", "")
                log_info = __logmon.get_log_info(log_name)
                topic_path = log_info["topic_path"]
                topic_path = topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in topic_path else topic_path
                filepath = log_info["log_file_path"]
                
                if rule_id not in handler.liveactions['logrecordings']:
                    raise LookupError("There is no log recording active for this log.")
                
                # We dont tell logmon to disable chunk generation because theer might be others who still want chunk generation
                #__logmon.disable_chunk_generation(log_name)
                
                # remove reference on client handler
                handler.liveactions['logrecordings'].remove(rule_id) 
                rule = buildLogWriterRule(rule_id, topic_path, filepath)
                
            event = StopLogRecordingEvent(topic=TOPIC_LOG_ACTIONS, data=rule)
            return ActionResponse(data = rule_id, events=[event])
        
        else:
            raise ModuleNotFoundError("`"+LOG_MANAGER_MODULE+"` module does not exist")
        



class ActionWriteLogChunks(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_WRITE_LOG_CHUNKS_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __filenamanger = None
        
        if modules.hasModule(FILE_MANAGER_MODULE):
            __filenamanger = modules.getModule(FILE_MANAGER_MODULE)
            chunks = params["__event__"]["data"]["content"]
            path = params["destination"]
            await __filenamanger.write_file_stream(path, chunks)
            #event = StartLogRecordingEvent(topic=TOPIC_LOG_ACTIONS, data=rule)
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`"+FILE_MANAGER_MODULE+"` module does not exist")
            



class ActionStartTarget(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_START_TARGET_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        
        if "module" not in  params:
            raise MissingArgumentError("Module name not provided")
        
        mod = params["module"]
        
        if modules.hasModule(mod):
            module_instance = modules.getModule(mod)
            
            if module_instance != None and isinstance(module_instance, TargetProcess):
                await module_instance.start_proc()
                return ActionResponse(data = None, events=[])
            else:
                raise TypeError("`"+mod+"` module is not a target process handler")
            
        else:
            raise ModuleNotFoundError("`"+mod+"` module does not exist")
        
    




class ActionStopTarget(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_STOP_TARGET_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        if "module" not in  params:
            raise MissingArgumentError("Module name not provided")
        
        mod = params["module"]
        
        if modules.hasModule(mod):
            module_instance = modules.getModule(mod)
            
            if module_instance != None and isinstance(module_instance, TargetProcess):
                await module_instance.stop_proc()
                return ActionResponse(data = None, events=[])
            else:
                raise TypeError("`"+mod+"` module is not a target process handler")
            
        else:
            raise ModuleNotFoundError("`"+mod+"` module does not exist")



class ActionRestartTarget(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_RESTART_TARGET_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        if "module" not in  params:
            raise MissingArgumentError("Module name not provided")
        
        mod = params["module"]
        
        if modules.hasModule(mod):
            module_instance = modules.getModule(mod)
            
            if module_instance != None and isinstance(module_instance, TargetProcess):
                await module_instance.restart_proc()
                return ActionResponse(data = None, events=[])
            else:
                raise TypeError("`"+mod+"` module is not a target process handler")
            
        else:
            raise ModuleNotFoundError("`"+mod+"` module does not exist")
        
        
    
    
    
class ActionSubcribeChannel(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_SUBSCRIBE_CHANNEL_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __pubsubhub = None
        
        if modules.hasModule(PUBSUBHUB_MODULE):
            __pubsubhub = modules.getModule(PUBSUBHUB_MODULE)
        
        if(__pubsubhub != None):
            handler = params["handler"]
            topic = params["topic"]
            # finalparams = params.copy() 
            #if(len(finalparams)>1):
            #    finalparams = finalparams[2:]
            __pubsubhub.subscribe(topic, handler)
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`"+PUBSUBHUB_MODULE+"` module does not exist")
        




class ActionUnSubcribeChannel(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_UNSUBSCRIBE_CHANNEL_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        __pubsubhub = None
        
        if modules.hasModule("pubsub"):
            __pubsubhub = modules.getModule("pubsub")
            handler = params["handler"]
            topic = params["topic"]       
            __pubsubhub.unsubscribe(topic, handler)
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`PubSub` module does not exist")
        
        



class ActionUnUpdateSoftwre(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_UPDATE_SOFTWARE_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        pass
        




class ActionHttpGet(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_HTTP_GET_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        
        url = params["url"]
        queryparams = params["queryparams"]
        querystring = urllib.parse.urlencode(queryparams)
        method = "GET"                
        
        http_client = AsyncHTTPClient()        
        url = url + querystring
        response = await http_client.fetch(url, method=method, headers=None)
        logger.debug("response = %s", str(response))
        if response.code == 200:
            result = str(response.body, 'utf-8')
            return ActionResponse(data = result, events=[])
        raise HTTPError("Unable to make request to url " + url)




class ActionSendMail(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_SEND_MAIL_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        
        if "subject" in params:
            subject = params["subject"]
        elif "__event__" in params:
            subject = "Event notification for " + params["__event__"]["name"]
        else:
            subject = "Send mail action!"
            
        
        if "content" in params:
            content = params["content"]
        elif "__event__" in params:
            content = "Event data for " + params["__event__"]["name"]
            content = content + "\n\r"
            content = "Event data for " + json.dumps(params["__event__"]["data"])
        else:
            content = "Send mail action content"
            content = content + "\n\r"
            if params != None:
                content = "Data " + json.dumps(params)
            else:
                content = " No content"
                
        
        __mailer:IMailer = None
        
        if modules.hasModule(SMTP_MAILER_MODULE):
            __mailer = modules.getModule(SMTP_MAILER_MODULE)
            if(__mailer != None):
                result = await __mailer.send_mail(subject, content)
                return ActionResponse(data = result, events=[])
            else:
                raise ModuleNotFoundError("`"+SMTP_MAILER_MODULE+"` module does not exist")
        else:
            raise ModuleNotFoundError("`"+SMTP_MAILER_MODULE+"` module does not exist")





class ActionStartScriptExecution(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_START_SCRIPT_EXECUTION_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        
        __script_runner = None
        __script_name = None
        __script_params = None
        
        
        if "name" in params:
            __script_name = params["name"]
        else:
            raise AttributeError("missing script name")
        
        
        if "args" in params:
            __script_params:str = str(params["args"])
        
        
        if modules.hasModule(SCRIPT_RUNNER_MODULE):
            __script_runner:IScriptRunner = modules.getModule(SCRIPT_RUNNER_MODULE)
            script_id = __script_runner.start_script(__script_name, __script_params)
            return ActionResponse(data = script_id, events=[])
        else:
            raise ModuleNotFoundError("`"+SCRIPT_RUNNER_MODULE+"` module does not exist")
        
        pass




class ActionStopScriptExecution(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_STOP_SCRIPT_EXECUTION_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __script_runner = None
        
        if "script_id" in params:
            __script_id = params["script_id"]
        else:
            raise AttributeError("missing script name")
        
        
        if modules.hasModule(SCRIPT_RUNNER_MODULE):
            __script_runner:IScriptRunner = modules.getModule(SCRIPT_RUNNER_MODULE)
            __script_runner.stop_script(__script_id)
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`"+SCRIPT_RUNNER_MODULE+"` module does not exist")
        pass
    



class ActionBotNotify(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_BOT_NOTIFY_NAME
    
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        service_bot = None
        
        if modules.hasModule("service_bot"):
            service_bot = modules.getModule("service_bot")
            
            message:Text = None
            if "message" in params:
                message = params["message"]
            elif "__event__" in params and "message" in params["__event__"]["data"]:
                message = params["__event__"]["data"]["message"]
            
            if message != None:            
                await service_bot.send_notification(message)
            else:
                logger.warn("nothing to send")
                
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`service_bot` module does not exist")
        pass





class ActionListLogs(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_LIST_LOGS_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        
        __logmon = None
        
        if modules.hasModule(LOG_MANAGER_MODULE):
            __logmon:ILogMonitor = modules.getModule(LOG_MANAGER_MODULE)
            result = __logmon.get_log_targets()
            return ActionResponse(data = result, events=[])
        else:
            raise ModuleNotFoundError("`"+LOG_MANAGER_MODULE+"` module does not exist")
        pass 





class ActionTest(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_TEST_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    @authorize__action(requiredrole="admin")
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        return ActionResponse(data = None, events=[])     