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

EVENT_STATS_ERROR = "stats_error"

EVENT_LOG_LINE_READ = "log_line"

EVENT_LOG_CHUNK_READ = "log_chunk"

EVENT_LOG_ERROR = "log_error"

EVENT_PING_GENERATED = "ping_generated"

EVENT_TEXT_NOTIFICATION = "text_notification"

EVENT_TEXT_DATA_NOTIFICATION = "text_data_notification"

EVENT_DATA_NOTIFICATION = "data_notification"


'''

EVENTS

'''


EventType = Dict[Text, Any]


# noinspection PyPep8Naming
def StatsGeneratedEvent(
    topic: Optional[Text],
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
    topic: Optional[Text],
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
    topic: Optional[Text],
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
    topic: Optional[Text],
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
def LogErrorEvent(
    topic: Optional[Text],
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
    topic: Optional[Text],
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
    topic: Optional[Text],
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
    topic: Optional[Text],
    message: Text,
    data: Optional[Dict[Text, Any]] = None,
    code: int,
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