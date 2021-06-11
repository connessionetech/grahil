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
import base64
from oneadmin.core.event import DataEvent, SimpleNotificationEvent


class EventType(object):
    NOTIFICATION = "notification"
    pass



def stringToBase64(s):
    return base64.b64encode(s.encode('utf-8'))


def base64ToString(b):
    return base64.b64decode(b).decode('utf-8')



def formatSuccessMQTTResponse(requestid, data={}, code=200):
    return {
            "session-id": str(requestid),
            "type": "mqtt",
            "status": "success",
            "code": code,
            "data": data,
            "timestamp":int(datetime.datetime.utcnow().timestamp())
            }



def formatErrorMQTTResponse(requestid, message, code=400):
    return {
            "session-id": str(requestid),
            "type": "mqtt",
            "status": "error",
            "code": code,
            "message": message,
            "timestamp":int(datetime.datetime.utcnow().timestamp())
            }



def formatAckMQTTResponse(requestid, code=200):
    return {
            "session-id": str(requestid),
            "type": "mqtt",
            "status": "ack",
            "code": code,
            "timestamp":int(datetime.datetime.utcnow().timestamp())
            }



def formatSuccessRPCResponse(requestid, data, code=200):
    return {
            "requestid": str(requestid),
            "type": "rpc",
            "status": "success",
            "code": code,
            "data": data,
            "timestamp":int(datetime.datetime.utcnow().timestamp())
            }



def formatErrorRPCResponse(requestid, message, code=400):
    return {
            "requestid": str(requestid),
            "type": "rpc",
            "status": "error",
            "code": code,
            "message": message,
            "timestamp":int(datetime.datetime.utcnow().timestamp())
            }
    
def formatSuccessResponse(data, code=200):
    return {
            "status": "success",
            "code": code,
            "data": data,
            "timestamp":int(datetime.datetime.utcnow().timestamp())
            }



def formatProgressResponse(permit, data):
    return {
            "permit": permit,
            "code": 200,
            "start_time": data["start_time"],
            "end_time": data["end_time"],
            "total_bytes": data["total_bytes"],
            "uploaded_bytes": data["uploaded_bytes"],
            "timestamp":int(datetime.datetime.utcnow().timestamp())
            }


def formatErrorResponse(message, code):
    return {
            "status": "error",
            "code": code,
            "message": message,
            "timestamp":int(datetime.datetime.utcnow().timestamp())
            }



def buildSimpleNotificationEvent(topic, msg, code=4, category=None):
    return SimpleNotificationEvent(topic,msg,code)



def buildDataNotificationEvent(data, topic, msg, code=4, category=None):    
    return DataNotificationEvent(topic,code,msg,data)



def buildDataEvent(data, topic, category=None):
    return DataEvent(topic,data)



def formatSuccessBotResponse(requestid, data):
    return data
    pass




def formatErrorBotResponse(requestid, error):
    return "An error occurred "  + str(error)
    pass
