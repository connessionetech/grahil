'''
Created on 14-Mar-2021

@author: root
'''


from oneadmin.abstracts import IModule
from oneadmin.responsebuilder import formatSuccessBotResponse, formatSuccessResponse
from oneadmin.core.action import Action, ActionResponse, ACTION_PREFIX
from oneadmin.responsebuilder import formatErrorResponse
from oneadmin.core.event import ArbitraryDataEvent


from tornado import ioloop
from tornado.web import url
import tornado
import logging
from typing import Text, List
import json
from abstracts import IntentProvider
from core import grahil_types
from core.intent import INTENT_PREFIX
from datetime import datetime




class SmartHome(IModule):
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
        return SmartHome.NAME    
        

    
    def initialize(self) ->None:
        self.logger.info("Module init")
        
        
    

    def get_url_patterns(self)->List:
        return [ url(r"/smarthome/doorbell", DoorBellHandler) ]
    
    
    
    '''
        Returns a list of supported actions
    '''
    def supported_actions(self) -> List[object]:
        return [ActionNotifyDoorBell()]


    '''
        Returns a list supported of action names
    '''
    def supported_action_names(self) -> List[Text]:
        return [ACTION_NOTIFY_DOORBELL]
    
    
    
    '''
        Returns a list supported of intents
    '''
    def supported_intents(self) -> List[Text]:
        return [INTENT_NOTIFY_DOORBELL]



# custom intents
INTENT_NOTIFY_DOORBELL = INTENT_PREFIX + "smarthome_doorbell_notify"


# custom actions
ACTION_NOTIFY_DOORBELL = ACTION_PREFIX + "smarthome_doorbell_notify"


'''
Module action demo
'''
class ActionNotifyDoorBell(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_NOTIFY_DOORBELL
    
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        service_bot = None
        
        if modules.hasModule("service_bot"):
            service_bot = modules.getModule("service_bot")
            message:Text = params["__event__"]["data"]["message"]        
            await service_bot.send_notification(message)
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`service_bot` module does not exist")
        pass







'''
Door bell callback handler
'''
class DoorBellHandler(tornado.web.RequestHandler):
    
    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)    
        pass
        
    
    
    async def post(self):
        self.logger.info("Bell ring callback")
        
        devicecode = self.get_argument("hmu_bl_001", "false", True)
        if devicecode == "true" or devicecode == True:
            await self.handle_doorbell_event()
        
        self.finish()
        
        
        
    async def handle_doorbell_event(self):
        today = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        subject = "Bell Ring! @ " + today;
        event = ArbitraryDataEvent("/smarthome/doorbell", {"message": subject})
        await self.application.handle_event(event)
        pass