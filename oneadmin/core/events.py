'''
Created on 25-Nov-2020

@author: root

List of supported system (built-in) events

'''

from typing import Dict, Text, Any, List, Optional, Union
from builtins import int

EventType = Dict[Text, Any]


# noinspection PyPep8Naming
def StatsGenerated(
    text: Optional[Text],
    parse_data: Optional[Dict[Text, Any]] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "event": "system",
        "timestamp": timestamp,
        "text": text,
        "parse_data": parse_data,
    }
    
    

# noinspection PyPep8Naming
def LogStatementGenerated(
    topic: Optional[Text],
    parse_data: Optional[Dict[Text, Any]] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "event": "system",
        "timestamp": timestamp,
        "text": text,
        "parse_data": parse_data,
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