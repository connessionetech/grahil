'''
Created on 25-Nov-2020

@author: root
'''
from version import __version__
from typing import Text, Dict, List,NamedTuple
from oneadmin.core import grahil_types
from tornado.concurrent import asyncio


from tornado.concurrent import asyncio
from oneadmin.core.constants import *
from core.event import EventType
from abstracts import IntentProvider
from utilities import buildLogWriterRule
from exceptions import RulesError
    


ACTION_PREFIX = "action_"

ACTION_GET_SOFTWARE_VERSION_NAME = ACTION_PREFIX + "get_software_version"

ACTION_UPDATE_SOFTWARE_NAME = ACTION_PREFIX + "update_software"

ACTION_REBOOT_SYSTEM_NAME = ACTION_PREFIX + "reboot_system"

ACTION_GET_SYSTEM_TIME_NAME = ACTION_PREFIX + "get_system_time"

ACTION_FORCE_GARBAGE_COLLECTION_NAME = ACTION_PREFIX + "force_garbage_collection"

ACTION_GET_SYSTEM_STATS_NAME = ACTION_PREFIX + "get_system_stats"

ACTION_GET_MEMORY_STATS_NAME = ACTION_PREFIX + "get_memory_stats"

ACTION_GET_CPU_STATS_NAME = ACTION_PREFIX + "get_cpu_stats"

ACTION_START_LOG_RECORDING_NAME = ACTION_PREFIX + "start_log_recording"

ACTION_STOP_LOG_RECORDING_NAME = ACTION_PREFIX + "stop_log_recording"

ACTION_CREATE_FOLDER_NAME = ACTION_PREFIX + "create_folder"

ACTION_DELETE_FOLDER_NAME = ACTION_PREFIX + "delete_folder"

ACTION_DELETE_FILE_NAME = ACTION_PREFIX + "delete_file"

ACTION_COPY_FILE_NAME = ACTION_PREFIX + "copy_file"

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
            ActionRemoveChannel(), ActionPublishChannel(), ActionRunDiagonitics(), ActionUnUpdateSoftwre()]




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
                __ver = __sysmon.getVersion()
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
        
        raise ValueError("testing")
        
        __sysmon = None
        
        if modules.hasModule(SYSTEM_MODULE):
            __sysmon = modules.getModule(SYSTEM_MODULE) 
            result =  __sysmon.getSystemTime()
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
            result =  __sysmon.getLastSystemStats()
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
            result =  __sysmon.getMemorytats()
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
            result =  __sysmon.getCPUStats()
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
            handler = params[0]
            path = str(params[1])
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
        
        if self.__rulesmanager is not None:
            log_name = params["name"] # log name
            log_info = __logmon.getLogInfo(log_name)
            
            if hasattr(handler, 'id'):
                rule_id = handler.id + '-' + log_name
                topic_path = log_info["topic_path"]                
                topic_path = topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in topic_path else topic_path
                filepath = log_info["log_file_path"]
                    
                rule = buildLogWriterRule(rule_id, topic_path, filepath)
                if self.__rulesmanager.hasRule(rule_id):
                    raise RulesError('Rule for id ' + rule_id + 'already exists')
                else:
                    self.__rulesmanager.registerRule(rule)
                    handler.liveactions['logrecordings'].add(rule_id) # store reference on client WebSocket handler
                    return ActionResponse(data = rule_id, events=[])
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
        
        handler = params["handler"]
                
        if self.__rulesmanager is not None:
            rule_id = params[1]
            if hasattr(handler, 'id'):                                
                if self.__rulesmanager.hasRule(rule_id):
                    self.__rulesmanager.deregisterRule(rule_id)
                    if rule_id in handler.liveactions['logrecordings']:
                        handler.liveactions['logrecordings'].remove(rule_id) # remove reference on client WebSocket handler
                        return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("No rules manager assigned")
            



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
        
        if modules.hasModule(TARGET_DELEGATE_MODULE):
            __delegate = modules.getModule(TARGET_DELEGATE_MODULE)
            await __delegate.start_proc()
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`"+TARGET_DELEGATE_MODULE+"` module does not exist")
        
    




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
        if modules.hasModule(TARGET_DELEGATE_MODULE):
            __delegate = modules.getModule(TARGET_DELEGATE_MODULE)
            await __delegate.stop_proc()
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`"+TARGET_DELEGATE_MODULE+"` module does not exist")



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
        
        __delegate = None
        if modules.hasModule(TARGET_DELEGATE_MODULE):
            __delegate = modules.getModule(TARGET_DELEGATE_MODULE)
            await __delegate.restart_proc()
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`"+TARGET_DELEGATE_MODULE+"` module does not exist")
        
    
    
    
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
        __sysmon = None
        
        if modules.hasModule(FILE_MANAGER_MODULE):
            __file_manager = modules.getModule(FILE_MANAGER_MODULE)
            if(__file_manager != None):
                __updater_script = await __file_manager.get_updater_script()
            
                if modules.hasModule(SYSTEM_MODULE):
                    __sysmon = modules.getModule(SYSTEM_MODULE)
                    if(__sysmon != None):
                        return __sysmon.schedule__update(__updater_script)
                else:
                    raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        else:
                    raise ModuleNotFoundError("`"+FILE_MANAGER_MODULE+"` module does not exist")
