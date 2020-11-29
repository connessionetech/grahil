'''
Created on 29-Nov-2020

@author: root
'''

from typing import List 
from typing import Text
from core import grahil_types


'''
Intent name constants
'''

INTENT_REBOOT_SYSTEM_NAME = "intent_reboot_system"

INTENT_GET_SYSTEM_TIME_NAME = "intent_get_system_time"

INTENT_FORCE_GARBAGE_COLLECTION_NAME = "intent_force_garbage_collection"

INTENT_GET_SYSTEM_STATS_NAME = "intent_get_system_stats"

INTENT_GET_MEMORY_STATS_NAME = "intent_get_memory_stats"

INTENT_GET_CPU_STATS_NAME = "intent_get_cpu_stats"

INTENT_START_LOG_RECORDING_NAME = "intent_start_log_recording"

INTENT_STOP_LOG_RECORDING_NAME = "intent_stop_log_recording"

INTENT_CREATE_FOLDER_NAME = "intent_create_folder"

INTENT_DELETE_FOLDER_NAME = "intent_delete_folder"

INTENT_DELETE_FILE_NAME = "intent_delete_file"

INTENT_COPY_FILE_NAME = "intent_copy_file"

INTENT_MOVE_FILE_NAME = "intent_move_file"

INTENT_DOWNLOAD_FILE_NAME = "intent_download_file"

INTENT_BROWSE_FILE_SYSTEM_NAME = "intent_browse_fs"

INTENT_INVOKE_ON_TARGET_NAME = "intent_fulfill_target_request"

INTENT_RESTART_TARGET_NAME = "intent_restart_target"

INTENT_STOP_TARGET_NAME = "intent_stop_target"

INTENT_START_TARGET_NAME = "intent_start_target"

INTENT_SUBSCRIBE_CHANNEL_NAME = "intent_subscribe_channel"

INTENT_UNSUBSCRIBE_CHANNEL_NAME = "intent_unsubscribe_channel"

INTENT_REMOVE_CHANNEL_NAME = "intent_remove_channel"

INTENT_CREATE_CHANNEL_NAME = "intent_create_channel"

INTENT_PUBLISH_CHANNEL_NAME = "intent_publish_channel"

INTENT_RUN_DIAGNOSTICS_NAME = "intent_run_diagnostics"

INTENT_EXECUTE_HTTP_CALL_NAME = "intent_execute_http_call"





def builtin_intents() -> List[Text]:
    return [INTENT_REBOOT_SYSTEM_NAME, INTENT_GET_SYSTEM_TIME_NAME, INTENT_FORCE_GARBAGE_COLLECTION_NAME, INTENT_GET_SYSTEM_STATS_NAME, INTENT_GET_MEMORY_STATS_NAME, INTENT_GET_CPU_STATS_NAME, 
            INTENT_START_LOG_RECORDING_NAME, INTENT_STOP_LOG_RECORDING_NAME, INTENT_CREATE_FOLDER_NAME, INTENT_DELETE_FOLDER_NAME, INTENT_DELETE_FILE_NAME, INTENT_COPY_FILE_NAME, INTENT_MOVE_FILE_NAME, 
            INTENT_DOWNLOAD_FILE_NAME, INTENT_BROWSE_FILE_SYSTEM_NAME, INTENT_INVOKE_ON_TARGET_NAME, INTENT_RESTART_TARGET_NAME, INTENT_STOP_TARGET_NAME, INTENT_START_TARGET_NAME, INTENT_SUBSCRIBE_CHANNEL_NAME, 
            INTENT_UNSUBSCRIBE_CHANNEL_NAME, INTENT_REMOVE_CHANNEL_NAME, INTENT_CREATE_CHANNEL_NAME, INTENT_PUBLISH_CHANNEL_NAME, INTENT_RUN_DIAGNOSTICS_NAME, INTENT_EXECUTE_HTTP_CALL_NAME]

    


def str_to_intent(command:str):
    
    if not command.startswith("intent_"):
        return "intent_" + command
    



def is_valid_intent(command:str):
    
    if command in builtin_intents():
        return True
    
    return False
    
