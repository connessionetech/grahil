'''
Created on 14-Mar-2021

@author: root
'''


from oneadmin.core.abstracts import IModule
from oneadmin.responsebuilder import formatSuccessBotResponse, formatSuccessResponse
from oneadmin.core.action import Action, ActionResponse, ACTION_PREFIX
from oneadmin.responsebuilder import formatErrorResponse
from oneadmin.core.event import DataEvent
from oneadmin.core.abstracts import IntentProvider, LoggingHandler
from oneadmin.core import grahil_types
from oneadmin.core.intent import INTENT_PREFIX

import tornado
import logging
import json

from tornado import ioloop
from tornado.web import url
from typing import Dict, Text, List
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
        

    
    def valid_configuration(self, conf:Dict) ->bool:
        return True      
    

    def get_url_patterns(self)->List:
        return [ url(r"/smarthome/doorbell", DoorBellHandler), url(r"/smarthome/plantpump", PlantWaterPumpHandler) ]
    
    
    
    '''
        Returns a list of supported actions
    '''
    def supported_actions(self) -> List[object]:
        return [ActionSmartHomeNotify()]


    '''
        Returns a list supported of action names
    '''
    def supported_action_names(self) -> List[Text]:
        return [ACTION_SMARTHOME_NOTIFY]
    
    
    
    '''
        Returns a list supported of intents
    '''
    def supported_intents(self) -> List[Text]:
        return [INTENT_SMARTHOME_NOTIFY]



# custom intents
INTENT_SMARTHOME_NOTIFY = INTENT_PREFIX + "smarthome_notify"


# custom actions
ACTION_SMARTHOME_NOTIFY = ACTION_PREFIX + "smarthome_notify"


'''
Module action demo
'''
class ActionSmartHomeNotify(Action):
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_SMARTHOME_NOTIFY
    
    
    
    
    
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
class DoorBellHandler(tornado.web.RequestHandler, LoggingHandler):
    
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
        event = DataEvent("/smarthome/doorbell", {"message": subject})
        await self.application.handle_event(event)
        pass
    




'''
Plant waterpump callback handler
'''
class PlantWaterPumpHandler(tornado.web.RequestHandler, LoggingHandler):
    
    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)    
        pass
        
    
    
    async def post(self):
        self.logger.info("plant waterpump callback")
        
        devicecode = self.get_argument("hmu_pc_001", "false", True)
        if devicecode == "true" or devicecode == True:
            
            pump = self.get_argument("pump", 0, True)
            message = self.get_argument("message", "State Unknown", True)
            queue_time = self.get_argument("queue_time", 0, True)
            send_time = self.get_argument("send_time", 0, True)
            
            await self.handle_pump_event(pump, message, queue_time, send_time)
        
        self.finish()
        
        
        
    async def handle_pump_event(self, pump, message:Text,queue_time=None, send_time=None):
        
        subject = ""
        subject = subject + message
        today = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        running = "Stopped" if pump == 0 else "Running"
        subject = subject + "\r\n Time : " + today;
        if queue_time>0 and send_time>0:
            subject = "\r\n Message delay : "  +  str(send_time - queue_time) + " ms";
            
        event = DataEvent("/smarthome/plantpump", {"message": subject})
        await self.application.handle_event(event)
        pass