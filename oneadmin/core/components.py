'''
Created on 29-Nov-2020

@author: root
'''

from tornado.queues import Queue
from typing import Text
from oneadmin.core.action import Action, builtin_action_names, action_from_name
from oneadmin.core.intent import INTENT_REBOOT_SYSTEM_NAME, INTENT_GET_SYSTEM_TIME_NAME, INTENT_FORCE_GARBAGE_COLLECTION_NAME, INTENT_GET_SYSTEM_STATS_NAME, INTENT_GET_MEMORY_STATS_NAME, INTENT_GET_CPU_STATS_NAME, INTENT_START_LOG_RECORDING_NAME, INTENT_STOP_LOG_RECORDING_NAME, INTENT_CREATE_FOLDER_NAME, INTENT_DELETE_FOLDER_NAME, INTENT_DELETE_FILE_NAME, INTENT_COPY_FILE_NAME, INTENT_MOVE_FILE_NAME, INTENT_DOWNLOAD_FILE_NAME, INTENT_BROWSE_FILE_SYSTEM_NAME, INTENT_INVOKE_ON_TARGET_NAME, INTENT_RESTART_TARGET_NAME, INTENT_STOP_TARGET_NAME, INTENT_START_TARGET_NAME, INTENT_SUBSCRIBE_CHANNEL_NAME, INTENT_UNSUBSCRIBE_CHANNEL_NAME, INTENT_REMOVE_CHANNEL_NAME, INTENT_CREATE_CHANNEL_NAME, INTENT_PUBLISH_CHANNEL_NAME, INTENT_RUN_DIAGNOSTICS_NAME
import logging
import tornado
from core.intent import built_in_intents, INTENT_PREFIX
from core.action import ACTION_PREFIX
from core.grahil_types import Modules



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
        self.__action_book = {}
        
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
        
        pass
    
    
    
    
    
    def registerActionByNameforIntent(self, intent_name:Text, action_name:Text):
        
        
        actions_names = builtin_action_names()
        
        if action_name not in actions_names:
            raise ValueError("Invalid action name "+action_name)
        
        if intent_name in self.__action_book:
            raise ValueError("intent "+intent_name+" is already registered for an action")
        
        action = action_from_name(action_name)
        
        self.__action_book[intent_name] =  {"action": action, "requests": Queue(maxsize=5)} # make 5 configurable
        
        pass
    
    
    
    
    async def handle_request(self, intent:Text, params:object):
        
        intent_name = INTENT_PREFIX + intent 
        
        if intent_name not in self.__action_book:
            raise KeyError("Unknown intent " + intent_name)
        
        requests:Queue = self.__action_book[intent_name]["requests"]
        
        
        pass