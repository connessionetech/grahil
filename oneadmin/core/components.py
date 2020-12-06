'''
Created on 29-Nov-2020

@author: root
'''

from tornado.queues import Queue
from typing import Text
from oneadmin.core.action import Action, builtin_action_names, action_from_name
from oneadmin.core.intent import INTENT_REBOOT_SYSTEM_NAME, INTENT_GET_SYSTEM_TIME_NAME, INTENT_FORCE_GARBAGE_COLLECTION_NAME, INTENT_GET_SYSTEM_STATS_NAME, INTENT_GET_MEMORY_STATS_NAME, INTENT_GET_CPU_STATS_NAME, INTENT_START_LOG_RECORDING_NAME, INTENT_STOP_LOG_RECORDING_NAME, INTENT_CREATE_FOLDER_NAME, INTENT_DELETE_FOLDER_NAME, INTENT_DELETE_FILE_NAME, INTENT_COPY_FILE_NAME, INTENT_MOVE_FILE_NAME, INTENT_DOWNLOAD_FILE_NAME, INTENT_BROWSE_FILE_SYSTEM_NAME, INTENT_INVOKE_ON_TARGET_NAME, INTENT_RESTART_TARGET_NAME, INTENT_STOP_TARGET_NAME, INTENT_START_TARGET_NAME, INTENT_SUBSCRIBE_CHANNEL_NAME, INTENT_UNSUBSCRIBE_CHANNEL_NAME, INTENT_REMOVE_CHANNEL_NAME, INTENT_CREATE_CHANNEL_NAME, INTENT_PUBLISH_CHANNEL_NAME, INTENT_RUN_DIAGNOSTICS_NAME
from core.constants import TARGET_DELEGATE_MODULE, FILE_MANAGER_MODULE,\
    SYSTEM_MODULE, PUBSUBHUB_MODULE
import logging
import tornado
from core.intent import built_in_intents, INTENT_PREFIX
from core.action import ACTION_PREFIX, ActionResponse
from core.grahil_types import Modules
from smalluuid import SmallUUID
from time import time
import json
from abstracts import IntentProvider
from builtins import str
import inspect
import copy
from core.event import EventType
from typing import List

class ActionDispatcher(object):
    '''
    classdocs
    '''


    def __init__(self, modules:Modules, conf=None):
        '''
        Constructor
        '''
    
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
        self.__modules = modules
        self.__action_book = {}
        self.__request_register = {}
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__initialize)
    pass



    def __initialize(self):
        
        # To do build intent-action map
        for intent_name in built_in_intents():
            
            try:
                action_name = str(intent_name).replace(INTENT_PREFIX, ACTION_PREFIX)
                action = action_from_name(action_name)
                
                if action:
                    self.registerActionforIntent(intent_name, action)
                    self.logger.debug("Registered intent by name" + intent_name + " for action " + action_name)
                else:
                    raise TypeError("'action' for intent " + intent_name + " was None, where object of type 'Action' was expected") 
           
            except TypeError as te:
                self.logger.warn(str(te))
                pass





    def registerActionforIntent(self, intent_name:Text, action:Action):
        
        if intent_name in self.__action_book:
            raise ValueError("intent "+intent_name+" is already registered for an action")
        
        self.__action_book[intent_name] = {"action": action, "requests": Queue(maxsize=5)} 
        tornado.ioloop.IOLoop.current().spawn_callback(self.__task_processor, intent_name)
        
        pass
    
    
    
    
    
    def registerActionByNameforIntent(self, intent_name:Text, action_name:Text):
        
        
        actions_names = builtin_action_names()
        
        if action_name not in actions_names:
            raise ValueError("Invalid action name "+action_name)
        
        if intent_name in self.__action_book:
            raise ValueError("intent "+intent_name+" is already registered for an action")
        
        action = action_from_name(action_name)
        
        self.__action_book[intent_name] =  {"action": action, "requests": Queue(maxsize=5)} # make 5 configurable
        tornado.ioloop.IOLoop.current().spawn_callback(self.__task_processor, intent_name)
        
        pass
    
    
    
    '''
        Accepts parameters and creates a request object
    '''     
    def _build_request(self, requester:IntentProvider, intent:Text, params:object):
        
        command_params = None
        
        if isinstance(params,str):
            params = json.loads(params)
        elif isinstance(params, list):
            it = iter(params)
            params = dict(zip(it, it))
        elif not isinstance(params, dict):
            raise ValueError("incompatible param type. dict is required")
            
        
        return {
            "requestid": SmallUUID().hex,
            "requester":requester,
            "intent": intent,
            "params": params,
            "timestamp": int(round(time() * 1000))
        }
        pass
    
    
    
    
    '''
        Handles intent requests from -> requesters must implement special interface to be notified of result, error or progress
    ''' 
    async def handle_request(self, requester:IntentProvider, intent:Text, params:object):
        
        intent_name = INTENT_PREFIX + intent 
        
        if intent_name not in self.__action_book:
            raise KeyError("Unknown intent " + intent_name)
        
        req_queue:Queue = self.__action_book[intent_name]["requests"]
        req = self._build_request(requester, intent, params)
        self.__request_register[req["requestid"]] = req
        
        await req_queue.put(req)
        return req["requestid"]
    
    
        
    
    
    
    '''
        Task Queue Processor - (Per Intent loop)
    '''
    async def __task_processor(self, intent_name):
        while True:
            
            if not intent_name in self.__action_book:
                break
            
            task_queue:Queue = self.__action_book[intent_name]["requests"]
            requestid:str = None
            
            response = None
            requester:IntentProvider = None
            events:List[EventType] = None
        
            try:
                task_definition = await task_queue.get()
                
                requestid = task_definition["requestid"]
                intent:str = task_definition["intent"]
                args:dict = task_definition["params"]
                requester = task_definition["requester"]
                action:Action = self.__action_book[intent_name]["action"]
                
                executable = copy.deepcopy(action)  
                # implement flywheeel pattern here              
                result:ActionResponse = await executable.execute(requester, self.__modules, args)
                events = result.events
                await  requester.onIntentProcessResult(requestid, result.data)
                                 
            except Exception as e:
                
                err = "Error executing action " + str(e)                
                self.logger.debug(err)
                await  requester.onIntentProcessError(requestid, e) 
                
            finally:
                task_queue.task_done()
                
                if requestid != None:
                    del self.__request_register[requestid]
                                
                if events != None:
                    pubsub = self.__modules.getModule(SYSTEM_MODULE)
                    for event in events:
                        await pubsub.publish_event_type(event)