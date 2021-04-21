'''
Created on 14-Mar-2021

@author: root
'''


from oneadmin.abstracts import IModule
from oneadmin.responsebuilder import formatSuccessBotResponse, formatSuccessResponse
from oneadmin.core.action import Action, ActionResponse, ACTION_PREFIX
from oneadmin.abstracts import IntentProvider, LoggingHandler

from tornado import ioloop
from tornado.web import url

import tornado
import logging
import json

from typing import Text, List
from core import grahil_types
from core.intent import INTENT_PREFIX




class ApiHostModule(IModule):
    '''
    classdocs
    '''
    
    NAME = "api_host_module"



    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
    
    
        
    def getname(self) ->Text:
        return ApiHostModule.NAME    
        

    
    def initialize(self) ->None:
        self.logger.info("Module init")
        
        
    
    

    def get_url_patterns(self)->List:
        return [ url(r"/moduleapi/", SampleHandler) ]
    
    
    
    '''
        Returns a list of supported actions
    '''
    def supported_actions(self) -> List[object]:
        return [ActionModuleAction()]


    '''
        Returns a list supported of action names
    '''
    def supported_action_names(self) -> List[Text]:
        return [ACTION_CUSTOM_ACTION_NAME]
    
    
    
    '''
        Returns a list supported of intents
    '''
    def supported_intents(self) -> List[Text]:
        return [INTENT_CUSTOM_ACTION_NAME]



# custom intents
INTENT_CUSTOM_ACTION_NAME = INTENT_PREFIX + "apidemo_custom_module"


# custom actions
ACTION_CUSTOM_ACTION_NAME = ACTION_PREFIX + "apidemo_custom_module"




'''
Module action demo
'''
class ActionModuleAction(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_CUSTOM_ACTION_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        print("execute")
        pass




'''
Sample  handler
'''
class SampleHandler(tornado.web.RequestHandler, LoggingHandler):
    
    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)    
        pass
    

    def get(self):
        self.logger.info("sample path")
        self.write(json.dumps(formatSuccessResponse("Hello world")))
        self.finish()
        