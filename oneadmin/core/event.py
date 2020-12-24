'''
Created on 25-Nov-2020

@author: root

List of supported system (built-in) events

'''

from typing import Dict, Text, Any, List, Optional, Union
from builtins import int



'''

EVENT CONSTANTS

'''


EVENT_STATS_GENERATED = "stats_generated"

EVENT_SCRIPT_EXECUTION_START = "script_execution_started"

EVENT_SCRIPT_EXECUTION_STOP = "script_execution_stopped"

EVENT_SCRIPT_EXECUTION_PROGRESS = "script_execution_progress"

EVENT_STATS_ERROR = "stats_error"

EVENT_LOG_LINE_READ = "log_line"

EVENT_LOG_CHUNK_READ = "log_chunk"

EVENT_LOG_RECORDING_START = "log_record_start"

EVENT_LOG_RECORDING_STOP = "log_record_stop"

EVENT_LOG_ERROR = "log_error"

EVENT_PING_GENERATED = "ping_generated"

EVENT_TEXT_NOTIFICATION = "text_notification"

EVENT_TEXT_DATA_NOTIFICATION = "text_data_notification"

EVENT_DATA_NOTIFICATION = "data_notification"

EVENT_ARBITRARY_DATA = "arbitrary_data"

EVENT_KEY = "__event__"


'''

EVENTS

'''


EventType = Dict[Text, Any]




def is_valid_event(evt):
    
    if "name" in evt and "type" in evt and "topic" in evt:
        return True
    
    return False




# noinspection PyPep8Naming
def StatsGeneratedEvent(
    topic: Text,
    data: Optional[Dict[Text, Any]] = None,    
    meta: Optional[Dict[Text, Any]] = None,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_STATS_GENERATED,
        "type": "event",
        "topic": topic,
        "data": data,
        "meta": meta,
        "note": note,
        "timestamp": timestamp
    }
    
    

# noinspection PyPep8Naming
def StatsErrorEvent(
    topic: Text,
    message: Optional[Text] = None,
    data: Optional[Dict[Text, Any]] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_STATS_ERROR,
        "type": "error",
        "topic": topic,
        "data": data,
        "message": message,
        "timestamp": timestamp
    }
    
    

# noinspection PyPep8Naming
def LogLineEvent(
    topic: Text,
    data: Optional[Dict[Text, Any]] = None,
    meta: Optional[Dict[Text, Any]] = None,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_LOG_LINE_READ,
        "type": "event",
        "topic": topic,        
        "data": data,
        "meta": meta,
        "note": note,
        "timestamp": timestamp
    }

    
    

# noinspection PyPep8Naming
def LogChunkEvent(
    topic: Text,
    data: Optional[Dict[Text, Any]] = None,    
    meta: Optional[Dict[Text, Any]] = None,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_LOG_CHUNK_READ,
        "type": "event",
        "topic": topic,
        "data": data,
        "meta": meta,
        "note": note,
        "timestamp": timestamp
    }
    
    


# noinspection PyPep8Naming
def StartLogRecordingEvent(
    topic: Text,
    data: Optional[Dict[Text, Any]] = None,    
    meta: Optional[Dict[Text, Any]] = None,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_LOG_RECORDING_START,
        "type": "event",
        "topic": topic,
        "data": data,
        "meta": meta,
        "note": note,
        "timestamp": timestamp
    }

    
    

# noinspection PyPep8Naming
def ScriptExecutionEvent(
    name: Text,    
    topic: Text,
    data: Optional[Dict[Text, Any]] = None,    
    meta: Optional[Dict[Text, Any]] = None,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": name,
        "type": "event",
        "topic": topic,
        "data": data,
        "meta": meta,
        "note": note,
        "timestamp": timestamp
    }



# noinspection PyPep8Naming
def StopLogRecordingEvent(
    topic: Text,
    data: Optional[Dict[Text, Any]] = None,    
    meta: Optional[Dict[Text, Any]] = None,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_LOG_RECORDING_STOP,
        "type": "event",
        "topic": topic,
        "data": data,
        "meta": meta,
        "note": note,
        "timestamp": timestamp
    }




# noinspection PyPep8Naming
def LogErrorEvent(
    topic: Text,
    message: Optional[Text] = None,
    data: Optional[Dict[Text, Any]] = None,
    meta: Optional[Dict[Text, Any]] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_LOG_ERROR,
        "type": "error",
        "topic": topic,
        "data": data,
        "meta": meta,
        "message": message,
        "timestamp": timestamp
    }
    
    


# noinspection PyPep8Naming
def PingEvent(
    topic: Text,
    data: Optional[Dict[Text, Any]] = None,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_PING_GENERATED,
        "type": "event",
        "topic": topic,
        "data": data,
        "note": note,
        "timestamp": timestamp
    }    

    
    
# noinspection PyPep8Naming
def SimpleTextNotificationEvent(
    topic: Text,
    message: Text,
    code: int,
    category: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_TEXT_NOTIFICATION,
        "type": "event",
        "topic": topic,
        "message": message,
        "code": code,
        "category": category,
        "timestamp": timestamp
    }
    


# noinspection PyPep8Naming
def DataNotificationEvent(
    topic: Text,
    code: int,
    message: Optional[Text],    
    data: Optional[Dict[Text, Any]] = None,
    category: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_TEXT_DATA_NOTIFICATION,
        "type": "event",
        "topic": topic,
        "message": message,
        "data": data,
        "code": code,
        "category": category,
        "timestamp": timestamp
    }
    
    
# noinspection PyPep8Naming
def DataEvent(
    topic: Optional[Text],
    data: Optional[Dict[Text, Any]] = None,
    category: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_DATA_NOTIFICATION,
        "type": "event",
        "topic": topic,
        "data": data,
        "category": category,
        "timestamp": timestamp
    }


# noinspection PyPep8Naming
def ArbitraryDataEvent(
    topic: Optional[Text],
    data: Optional[Dict[Text, Any]] = None,
    category: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_ARBITRARY_DATA,
        "type": "event",
        "topic": topic,
        "data": data,
        "category": category,
        "timestamp": timestamp
    }