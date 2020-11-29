'''
Created on 25-Nov-2020

@author: root
'''
from version import __version__
from typing import List 
from typing import Text
from oneadmin.core import grahil_types

from tornado.concurrent import asyncio
from core.constants import TARGET_DELEGATE_MODULE, FILE_MANAGER_MODULE,\
    SYSTEM_MODULE, PUBSUBHUB_MODULE

ACTION_PREFIX = "action_"

ACTION_GET_SOFTWARE_VERSION_NAME = ACTION_PREFIX + "get_software_version"

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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        return {}
    
    
    
    '''
    spits out string name of action
    '''
    def __str__(self) -> Text:
        return "Action('{}')".format(self.name())
    



'''
Returns instances of builtin actions
'''
def builtin_actions() -> List[Action]:
    return [ActionGetSoftwareVersion(), ActionRebootSystem(), ActionGetSystemTime(), ActionForceGarbageCollection(), 
            ActionGetSystemStats(), ActionGetMemoryStats(), ActionGetCPUStats(), ActionStartLogRecording(), ActionStopLogRecording(),
            ActionCreateFolder(), ActionDeleteFolder(), ActionDeleteFile(), ActionCopyFile(), ActionMoveFile(), ActionDownloadFile(),
            ActionBrowseFileSystem(), ActionFulfillTargetRequest(), ActionStartTarget(), ActionStopTarget(), ActionRestartTarget(), 
            ActionSubcribeChannel(), ActionUnSubcribeChannel(), ActionCreateChannel(), ActionRemoveChannel(), ActionPublishChannel(), 
            ActionRunDiagonitics()]




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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        return {"data": __version__}
    



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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass
    
    
    
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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass
    

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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass
    
    
    
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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass
    
    


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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass



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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass




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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass



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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass




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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass




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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass




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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass





class ActionFulfillTargetRequest(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_INVOKE_ON_TARGET_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
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
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass




class ActionCreateChannel(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_CREATE_CHANNEL_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass     
    
    



class ActionRemoveChannel(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_REMOVE_CHANNEL_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass
    
    


class ActionRunDiagonitics(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_RUN_DIAGNOSTICS_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass     
    
    

class ActionStartLogRecording(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_START_LOG_RECORDING_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass  




class ActionStopLogRecording(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_STOP_LOG_RECORDING_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass  
    


class ActionStartTarget(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_START_TARGET_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass  
    




class ActionStopTarget(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_STOP_TARGET_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass  




class ActionRestartTarget(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_RESTART_TARGET_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass
    
    
    
class ActionSubcribeChannel(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_SUBSCRIBE_CHANNEL_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass  




class ActionUnSubcribeChannel(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_UNSUBSCRIBE_CHANNEL_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        pass  



