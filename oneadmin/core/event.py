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

import datetime
from typing import Dict, Text, Any, List, Optional, Union
from builtins import int



'''

EVENT CONSTANTS

'''


EVENT_ANY = "*"

EVENT_STATS_DATA = "stats_generated"

EVENT_SCRIPT_EXECUTION_START = "script_execution_started"

EVENT_SCRIPT_EXECUTION_STOP = "script_execution_stopped"

EVENT_SCRIPT_EXECUTION_PROGRESS = "script_execution_progress"

EVENT_LOG_LINE_READ = "log_line_generated"

EVENT_LOG_CHUNK_READ = "log_chunk_generated"

EVENT_LOG_RECORDING_START = "log_record_start"

EVENT_LOG_RECORDING_STOP = "log_record_stop"

EVENT_PING_GENERATED = "ping_generated"

EVENT_TEXT_NOTIFICATION = "text_notification"

EVENT_TEXT_DATA_NOTIFICATION = "text_data_notification"

EVENT_DATA_NOTIFICATION = "data_notification"

EVENT_ARBITRARY_DATA = "arbitrary_data"

EVENT_TELEMETRY_DATA = "telemetry_data"

EVENT_KEY = "__event__"


'''

EVENTS

'''


EventType = Dict[Text, Any]




def is_valid_event(evt):
    
    if "name" in evt and "type" in evt and "topic" in evt:
        return True
    
    return False


def utc_timestamp():
    return int(datetime.datetime.utcnow().timestamp() * 1000)




# noinspection PyPep8Naming
def StatsDataEvent(
    topic: Text,
    data: Optional[Dict[Text, Any]] = None,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_STATS_DATA,
        "type": "event",
        "state": "data",
        "topic": topic,
        "data": data,
        "note": note,
        "timestamp": utc_timestamp() if timestamp == None else timestamp
    }
    
    

# noinspection PyPep8Naming
def StatsErrorEvent(
    topic: Text,
    error: Text,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_STATS_DATA,
        "type": "event",
        "state": "error",
        "topic": topic,
        "data": {"message": str(error, 'utf-8')},
        "timestamp": utc_timestamp() if timestamp == None else timestamp
    }



# noinspection PyPep8Naming
def LogErrorEvent(
    topic: Text,
    logkey: Text,
    error: Text,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_LOG_LINE_READ,
        "type": "event",
        "state": "error", 
        "topic": topic,
        "data": {"name":logkey, "message": str(error, 'utf-8')},
        "note": note,
        "timestamp": utc_timestamp() if timestamp == None else timestamp
    }
    
    
    

# noinspection PyPep8Naming
def LogEvent(
    topic: Text,    
    logkey: Text,
    logdata: Text,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_LOG_LINE_READ,
        "type": "event",
        "state": "data", 
        "topic": topic,        
        "data": {"name":logkey, "log": str(logdata, 'utf-8')},
        "note": note,
        "timestamp": utc_timestamp() if timestamp == None else timestamp
    }

    
    

# noinspection PyPep8Naming
def LogChunkEvent(
    topic: Text,
    logkey: Text,
    chunk: Text,    
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_LOG_CHUNK_READ,
        "type": "event",
        "state": "data",
        "topic": topic,
        "data": {"name":logkey, "chunk": chunk},
        "note": note,
        "timestamp": utc_timestamp() if timestamp == None else timestamp
    }
    
    


# noinspection PyPep8Naming
def StartLogRecordingEvent(
    topic: Text,
    data: Optional[Dict[Text, Any]] = None,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_LOG_RECORDING_START,
        "type": "event",
        "topic": topic,
        "data": data,
        "note": note,
        "timestamp": utc_timestamp() if timestamp == None else timestamp
    }

    
    

# noinspection PyPep8Naming
def ScriptExecutionEvent(
    name: Text,    
    topic: Text,
    output: Text = None,    
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": name,
        "type": "event",
        "topic": topic,
        "data": {"output": str(output, 'utf-8')},
        "note": note,
        "timestamp": utc_timestamp() if timestamp == None else timestamp
    }




# noinspection PyPep8Naming
def TelemetryDataEvent(
    topic: Text,
    data: Optional[Dict[Text, Any]] = None,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_TELEMETRY_DATA,
        "type": "event",
        "topic": topic,
        "data": data,
        "note": note,
        "timestamp": utc_timestamp() if timestamp == None else timestamp
    }





# noinspection PyPep8Naming
def StopLogRecordingEvent(
    topic: Text,
    data: Optional[Dict[Text, Any]] = None,
    note: Optional[Text] = None,
    timestamp: Optional[float] = None,
) -> EventType:
    return {
        "name": EVENT_LOG_RECORDING_STOP,
        "type": "event",
        "topic": topic,
        "data": data,
        "note": note,
        "timestamp": utc_timestamp() if timestamp == None else timestamp
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
        "state": "data",
        "topic": topic,
        "data": data,
        "note": note,
        "timestamp": utc_timestamp() if timestamp == None else timestamp
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
        "timestamp": utc_timestamp() if timestamp == None else timestamp
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
        "timestamp": utc_timestamp() if timestamp == None else timestamp
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
        "timestamp": utc_timestamp() if timestamp == None else timestamp
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
        "timestamp": utc_timestamp() if timestamp == None else timestamp
    }