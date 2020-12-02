'''
Created on 25-Nov-2020

@author: root

List of supported system (built-in) events

'''

from typing import Dict, Text, Any, List, Optional, Union
from builtins import int

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
        "name": "stats_generated",
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
        "name": "stats_error",
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
        "name": "log_line",
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
        "name": "log_chunk",
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
        "name": "log_error",
        "type": "error",
        "topic": topic,
        "data": data,
        "meta": meta,
        "message": message,
        "timestamp": timestamp
    }
    
    
# noinspection PyPep8Naming
def SimpleNotificationEvent(
    message: Text,
    code: int,
    category: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "event": "notification",
        "message": msg,
        "code": code,
        "category": category,
        "timestamp": timestamp
    }
    


# noinspection PyPep8Naming
def DataNotificationEvent(
    message: Text,
    code: int,
    data: Optional[object] = None,
    category: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "event": "data_notification",
        "message": msg,
        "code": code,
        "data": data,
        "category": category,
        "timestamp": timestamp
    }
    
    
# noinspection PyPep8Naming
def DataEvent(
    data: object,
    category: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "event": "data",
        "data": data,
        "category": category,
        "timestamp": timestamp
    }