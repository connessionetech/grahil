'''
This file is part of `Reactivity` 
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

import asyncio
import ntpath
import os
import imghdr
import json



def isVideoPath(obj):
    pass


def isImagePath(obj):
    
    try:
        if imghdr.what(str(obj)) != None:
            return True
        return False
    except Exception as e:
        return False


def isJSON(obj):
    try:
        json_object = json.loads(str(obj))
    except ValueError as e:
        return False
    return True


def hasFunction(obj, methodname):
    invert_op = getattr(obj, methodname, None)
    return True if callable(invert_op) else False


def buildTopicPath(topic, subtopic):
    return topic + "/" + subtopic


def getLogFileKey(path):
    return str(path_leaf(path))


def path_leaf(path):
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)
    

''' builds log writer rule dynamically '''        
def buildLogWriterRule(id, topic, filepath):
    name = path_leaf(filepath)
    output_path = os.path.join(os.path.dirname(filepath),  "ondemand-" + id)
    return {
        "id": id,
        "description": "Rule for log recording " + name,
        "listen-to": ""+ topic + "",
        "enabled": True,
        "trigger":{
            "on-payload-object": "data",
            "on-content": "*",
            "using-condition": "equals",
            "evaluator-func": None
        },
        "response":{
            "action": "start_log_record",
            "reaction-func": "standard_reactions.write_log",
            "reaction-params": {
                "filepath": "" + output_path + ""
            }
        }    
    }
    pass