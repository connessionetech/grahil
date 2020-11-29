'''
Created on 25-Nov-2020

@author: root
'''
from version import __version__
from typing import List 
from typing import Text
from core import grahil_types

from tornado.concurrent import asyncio
from core.constants import TARGET_DELEGATE_MODULE, FILE_MANAGER_MODULE,\
    SYSTEM_MODULE, PUBSUBHUB_MODULE


ACTION_GET_SOFTWARE_VERSION_NAME = "action_get_software_version"

ACTION_REBOOT_SYSTEM_NAME = "action_reboot_system"

ACTION_GET_SYSTEM_TIME_NAME = "action_get_system_time"

ACTION_FORCE_GARBAGE_COLLECTION_NAME = "action_force_garbage_collection"

ACTION_GET_SYSTEM_STATS_NAME = "action_get_system_stats"

ACTION_GET_MEMORY_STATS_NAME = "action_get_memory_stats"

ACTION_GET_CPU_STATS_NAME = "action_get_cpu_stats"

ACTION_START_LOG_RECORDING_NAME = "action_start_log_recording"

ACTION_STOP_LOG_RECORDING_NAME = "action_stop_log_recording"

ACTION_CREATE_FOLDER_NAME = "action_create_folder"

ACTION_DELETE_FOLDER_NAME = "action_delete_folder"

ACTION_DELETE_FILE_NAME = "action_delete_file"

ACTION_COPY_FILE_NAME = "action_copy_file"

ACTION_MOVE_FILE_NAME = "action_move_file"

ACTION_DOWNLOAD_FILE_NAME = "action_download_file"

ACTION_BROWSE_FILE_SYSTEM_NAME = "action_browse_fs"

ACTION_INVOKE_ON_TARGET_NAME = "action_fulfill_target_request"

ACTION_RESTART_TARGET_NAME = "action_restart_target"

ACTION_STOP_TARGET_NAME = "action_stop_target"

ACTION_START_TARGET_NAME = "action_start_target"

ACTION_SUBSCRIBE_CHANNEL_NAME = "action_subscribe_channel"

ACTION_UNSUBSCRIBE_CHANNEL_NAME = "action_unsubscribe_channel"

ACTION_REMOVE_CHANNEL_NAME = "action_remove_channel"

ACTION_CREATE_CHANNEL_NAME = "action_create_channel"

ACTION_PUBLISH_CHANNEL_NAME = "action_publish_channel"

ACTION_RUN_DIAGNOSTICS_NAME = "action_run_diagnostics"

ACTION_EXECUTE_HTTP_CALL_NAME = "action_execute_http_call"





'''
Returns instances of builtin actions
'''
def builtin_actions() -> List[Action]:
    return [ActionGetSoftwareVersion(), ActionRebootSystem()]




def builtin_action_names() -> List[Text]:
    return [a.name() for a in builtin_actions()]




def action_from_name(name:Text) -> Action:
    defaults = {a.name(): a for a in builtin_actions()}
    if name in defaults:
        return defaults.get(name)
    
    return None


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
Retreives grahil version
'''
class ActionGetSoftwareVersion(Action):
    
    
    '''
    classdocs
    '''

    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_GET_SOFTWARE_VERSION
    
    
    
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
    classdocs
    '''

    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_REBOOT_SYSTEM_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        __sysmon = None
        
        if modules.hasModule(SYSTEM_MODULE):
            __sysmon = modules.getModule(SYSTEM_MODULE)
            
        if(__sysmon != None):        
            __sysmon.reboot_system()
            await asyncio.sleep(.5)
            return {"data": None}
        else:
            raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        pass



'''
Triggers garbage collector on python
'''
class ActionForceGarbageCollection(Action):
    
    
    '''
    classdocs
    '''
            
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_FORCE_GARBAGE_COLLECTION_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        
        __sysmon = None
        
        if modules.hasModule(SYSTEM_MODULE):
            __sysmon = modules.getModule(SYSTEM_MODULE)
            
        if(__sysmon != None):        
            __sysmon.force_gc()
            await asyncio.sleep(.5)
            return {"data": None}
        else:
            raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        pass
    
    
    
'''
Retreives system time
'''
class ActionGetSystemTime(Action):
    
    
    '''
    classdocs
    '''

    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_GET_SYSTEM_TIME_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        
        __sysmon = None
        
        if self.__system_modules.hasModule(SYSTEM_MODULE):
            __sysmon = self.__system_modules.getModule(SYSTEM_MODULE)
            
        if(__sysmon != None):        
            result =  __sysmon.getSystemTime()
            await asyncio.sleep(.5)
            return {"data": result}
        else:
            raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        pass
 
 
 
 
'''
Retreives system stats
'''
class ActionGetSystemStats(Action):
    
    
    '''
    classdocs
    '''

    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_GET_SYSTEM_STATS_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        
        __sysmon = None
        
        if self.__system_modules.hasModule(SYSTEM_MODULE):
            __sysmon = self.__system_modules.getModule(SYSTEM_MODULE)
            
        if(__sysmon != None):        
            result =  __sysmon.getLastSystemStats()
            await asyncio.sleep(.5)
            return {"data": result}
        else:
            raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        pass
    

'''
Retreives memory stats
'''
class ActionGetMemoryStats(Action):
    
    
    '''
    classdocs
    '''

    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_GET_MEMORY_STATS_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        
        __sysmon = None
        
        if self.__system_modules.hasModule(SYSTEM_MODULE):
            __sysmon = self.__system_modules.getModule(SYSTEM_MODULE)
            
        if(__sysmon != None):        
            result =  __sysmon.getMemorytats()
            await asyncio.sleep(.5)
            return {"data": result}
        else:
            raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        pass
    
    
    
'''
Retreives cpu stats
'''
class ActionGetCPUStats(Action):
    
    
    '''
    classdocs
    '''

    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_GET_CPU_STATS_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        
        __sysmon = None
        
        if self.__system_modules.hasModule(SYSTEM_MODULE):
            __sysmon = self.__system_modules.getModule(SYSTEM_MODULE)
            
        if(__sysmon != None):        
            result =  __sysmon.getCPUStats()
            await asyncio.sleep(.5)
            return {"data": result}
        else:
            raise ModuleNotFoundError("`"+SYSTEM_MODULE+"` module does not exist")
        pass
    
    


'''
Deletes a file
'''
class ActionDeleteFile(Action):
    
    
    '''
    classdocs
    '''

    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_DELETE_FILE_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        
        __filemanager = None
        
        if self.__system_modules.hasModule(FILE_MANAGER_MODULE):
            __filemanager = self.__system_modules.getModule(FILE_MANAGER_MODULE)
        
        if(__filemanager != None):
            handler = params[0]
            path = str(params[1])
            result = await __filemanager.deleteFile(path)
            return {"data": result}
        else:
            raise ModuleNotFoundError("`FileManager` module does not exist")
        pass



'''
Deletes a file
'''
class ActionBrowseFileSystem(Action):
    
    
    '''
    classdocs
    '''

    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_BROWSE_FILE_SYSTEM_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        
        __filemanager = None
        
        if self.__system_modules.hasModule(FILE_MANAGER_MODULE):
            __filemanager = self.__system_modules.getModule(FILE_MANAGER_MODULE)
        
        if(__filemanager != None):
            handler = params[0]
            path = str(params[1])
            result = await __filemanager.browse_content(path)
            return {"data": result}
        else:
            raise ModuleNotFoundError("`FileManager` module does not exist")
        pass




class ActionFulfillTargetRequest(Action):
    
    
    '''
    classdocs
    '''

    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_INVOKE_ON_TARGET_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        
        __delegate = None
        
        if self.__system_modules.hasModule(TARGET_DELEGATE_MODULE):
            __delegate = self.__system_modules.getModule(TARGET_DELEGATE_MODULE)
            
        if(__delegate != None):
            if(len(params)<1):
                raise Exception("Minimum of one parameter is required for this method call")
            
            handler = params[0]
            command = str(params[1])
            self.logger.debug(command)
            finalparams = params.copy()
            finalparams = finalparams[2:]
            result = await __delegate.fulfillRequest(command, finalparams)
            return {"data": result}
        else:
            raise ModuleNotFoundError("`TargetDelegate` module does not exist")
        pass
    
    

class ActionPublishChannel(Action):
    
    
    '''
    classdocs
    '''

    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_INVOKE_ON_TARGET_NAME
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, modules:grahil_types.Modules, params:dict=None) -> dict:
        
        __pubsubhub = None
        
        if self.__system_modules.hasModule(PUBSUBHUB_MODULE):
            __pubsubhub = self.__system_modules.getModule(PUBSUBHUB_MODULE)
        
            if(__pubsubhub != None):
                handler = params[0] 
                topicname = params[1]  
                message = params[2]        
                await __pubsubhub.publish(topicname, message, handler)
                return {"data": None}
            pass
    