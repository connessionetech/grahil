'''
Created on 29-Nov-2020

@author: root
'''

from typing import List 
from typing import Text
from core import grahil_types


INTENT_PREFIX = "intent_"


'''
Intent name constants
'''

INTENT_TEST_NAME = INTENT_PREFIX + "test"

INTENT_GET_SOFTWARE_VERSION_NAME = INTENT_PREFIX + "get_software_version"

INTENT_HTTP_GET_NAME = INTENT_PREFIX + "http_get"

INTENT_REBOOT_SYSTEM_NAME = INTENT_PREFIX + "reboot_system"

INTENT_GET_SYSTEM_TIME_NAME = INTENT_PREFIX + "get_system_time"

INTENT_FORCE_GARBAGE_COLLECTION_NAME = INTENT_PREFIX + "force_garbage_collection"

INTENT_GET_SYSTEM_STATS_NAME = INTENT_PREFIX + "get_system_stats"

INTENT_GET_MEMORY_STATS_NAME = INTENT_PREFIX + "get_memory_stats"

INTENT_GET_CPU_STATS_NAME = INTENT_PREFIX + "get_cpu_stats"

INTENT_START_LOG_RECORDING_NAME = INTENT_PREFIX + "start_log_recording"

INTENT_STOP_LOG_RECORDING_NAME = INTENT_PREFIX + "stop_log_recording"

INTENT_START_SCRIPT_EXECUTION_NAME = INTENT_PREFIX + "start_script_execution"

INTENT_STOP_SCRIPT_EXECUTION_NAME = INTENT_PREFIX + "stop_script_execution"

INTENT_CREATE_FOLDER_NAME = INTENT_PREFIX + "create_folder"

INTENT_DELETE_FOLDER_NAME = INTENT_PREFIX + "delete_folder"

INTENT_DELETE_FILE_NAME = INTENT_PREFIX + "delete_file"

INTENT_COPY_FILE_NAME = INTENT_PREFIX + "copy_file"

INTENT_READ_FILE_NAME = INTENT_PREFIX + "read_file"

INTENT_WRITE_FILE_NAME = INTENT_PREFIX + "write_file"

INTENT_MOVE_FILE_NAME = INTENT_PREFIX + "move_file"

INTENT_DOWNLOAD_FILE_NAME = INTENT_PREFIX + "download_file"

INTENT_BROWSE_FILE_SYSTEM_NAME = INTENT_PREFIX + "browse_fs"

INTENT_INVOKE_ON_TARGET_NAME = INTENT_PREFIX + "fulfill_target_request"

INTENT_RESTART_TARGET_NAME = INTENT_PREFIX + "restart_target"

INTENT_STOP_TARGET_NAME = INTENT_PREFIX + "stop_target"

INTENT_START_TARGET_NAME = INTENT_PREFIX + "start_target"

INTENT_SUBSCRIBE_CHANNEL_NAME = INTENT_PREFIX + "subscribe_channel"

INTENT_UNSUBSCRIBE_CHANNEL_NAME = INTENT_PREFIX + "unsubscribe_channel"

INTENT_REMOVE_CHANNEL_NAME = INTENT_PREFIX + "remove_channel"

INTENT_CREATE_CHANNEL_NAME = INTENT_PREFIX + "create_channel"

INTENT_PUBLISH_CHANNEL_NAME = INTENT_PREFIX + "publish_channel"

INTENT_RUN_DIAGNOSTICS_NAME = INTENT_PREFIX + "run_diagnostics"

INTENT_SEND_MAIL_NAME = INTENT_PREFIX + "send_mail"





def built_in_intents() -> List[Text]:
    return [INTENT_REBOOT_SYSTEM_NAME, INTENT_GET_SYSTEM_TIME_NAME, INTENT_FORCE_GARBAGE_COLLECTION_NAME, INTENT_GET_SYSTEM_STATS_NAME, INTENT_GET_MEMORY_STATS_NAME, INTENT_GET_CPU_STATS_NAME, 
            INTENT_START_LOG_RECORDING_NAME, INTENT_STOP_LOG_RECORDING_NAME, INTENT_CREATE_FOLDER_NAME, INTENT_DELETE_FOLDER_NAME, INTENT_DELETE_FILE_NAME, INTENT_COPY_FILE_NAME, INTENT_MOVE_FILE_NAME, 
            INTENT_DOWNLOAD_FILE_NAME, INTENT_BROWSE_FILE_SYSTEM_NAME, INTENT_INVOKE_ON_TARGET_NAME, INTENT_RESTART_TARGET_NAME, INTENT_STOP_TARGET_NAME, INTENT_START_TARGET_NAME, INTENT_SUBSCRIBE_CHANNEL_NAME, 
            INTENT_UNSUBSCRIBE_CHANNEL_NAME, INTENT_REMOVE_CHANNEL_NAME, INTENT_CREATE_CHANNEL_NAME, INTENT_PUBLISH_CHANNEL_NAME, INTENT_RUN_DIAGNOSTICS_NAME, INTENT_GET_SOFTWARE_VERSION_NAME, INTENT_HTTP_GET_NAME,
            INTENT_SEND_MAIL_NAME, INTENT_START_SCRIPT_EXECUTION_NAME, INTENT_STOP_SCRIPT_EXECUTION_NAME]

    


def str_to_intent(command:str):
    
    if not command.startswith("intent_"):
        return "intent_" + command
    



def is_valid_intent(command:str):
    
    if command in built_in_intents():
        return True
    
    return False
    
