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

from oneadmin.core.constants import *
from oneadmin.core.event import EventType
from oneadmin.core.abstracts import IntentProvider, TargetProcess, IClientChannel, IEventHandler, IEventDispatcher, IModule, IntentProvider
from oneadmin.exceptions import ActionError
from oneadmin.core.intent import built_in_intents, INTENT_PREFIX
from oneadmin.core.action import ACTION_PREFIX, ActionResponse, Action, builtin_action_names, action_from_name
from oneadmin.core.grahil_types import Modules
from oneadmin.core.event import EVENT_KEY
from oneadmin.core.constants import built_in_client_types

from typing import Dict,Any
from typing_extensions import TypedDict
import logging
import tornado
from tornado.queues import Queue
import json
from smalluuid import SmallUUID
from time import time
from typing import Text
from typing import List
from builtins import str
import copy
from tornado.ioloop import IOLoop
from concurrent.futures.thread import ThreadPoolExecutor
from tornado.websocket import websocket_connect
import uuid





class VirtualHandler(object):
    '''
    Acts as a handler delegate on behalf of client channels
    '''
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.messages = Queue()
        self.id = str(uuid.uuid4())
        self.liveactions = {}
        self.liveactions['logrecordings'] = set()
        self.liveactions['scriptexecutions'] = set()
        self.finished = False
        tornado.ioloop.IOLoop.current().spawn_callback(self.__run)
        pass
    
    
    
    def close(self):
        self.finished = True
        pass
    
    
    
    async def submit(self, message):
        await self.messages.put(message) 
        pass
    
    
    
    async def __run(self):
        while not self.finished:
            try:
                message = await self.messages.get()
                self.send(message)
            except Exception as e:
                pass
            finally:
                self.messages.task_done()





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
        self.__executor = ThreadPoolExecutor(max_workers=4)
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__initialize)
    pass



    def __initialize(self):
        
        # To do build intent-action map
        for intent_name in built_in_intents():
            
            try:
                action_name = str(intent_name).replace(INTENT_PREFIX, ACTION_PREFIX)
                action:Action = action_from_name(action_name)
                
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
        
        action:Action = action_from_name(action_name)
        
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
    async def handle_request(self, requester:IntentProvider, intent:Text, params:dict, event:EventType=None):
        
        ''' if we have event info pass that to action as well '''
        if event:
            params = self.merge_parameters(params, event)
        
        intent_name = (INTENT_PREFIX + intent) if not intent.startswith(INTENT_PREFIX) else intent
        
        if intent_name not in self.__action_book:
            raise KeyError("Unknown intent " + intent_name)
        
        req_queue:Queue = self.__action_book[intent_name]["requests"]
        req = self._build_request(requester, intent, params)
        self.__request_register[req["requestid"]] = req
        
        await req_queue.put(req)
        return req["requestid"]
    
    
    
    
    '''
        Handles intent requests from -> requesters must implement special interface to be notified of result, error or progress
    ''' 
    async def handle_request_direct(self, requester:IntentProvider, intent:Text, params:dict):
        
        intent_name = (INTENT_PREFIX + intent) if not intent.startswith(INTENT_PREFIX) else intent
        
        if intent_name not in self.__action_book:
            raise KeyError("Unknown intent " + intent_name)
        
        response = None
        requester:IntentProvider = None
        events:List[EventType] = None
        executable:Action = None
    
        try:
            action:Action = self.__action_book[intent_name]["action"]
            executable = copy.deepcopy(action)          
            result:ActionResponse = None
            
            if action.is_async():
                result = await executable.execute(requester, self.__modules, params)
            else:
                result = await IOLoop.current().run_in_executor(
                    self.__executor,
                    executable.execute, requester, self.__modules, params
                    )
            
            events = result.events
            return result.data
                             
        except Exception as e:
            
            err = "Error executing action " + str(e)                
            self.logger.debug(err)
            raise ActionError(err)
                    
        finally:
            
            if executable != None:
                del executable 
                executable = None
            
            
            if events != None:
                pubsub = self.__modules.getModule(PUBSUBHUB_MODULE)
                for event in events:
                    await pubsub.publish_event_type(event)
    
    
    
    ''' Merges event sict into parameters dict '''
    def merge_parameters(self, params, event:EventType):
        event_dict = {EVENT_KEY:event}
        return{**params, **event_dict}        
    
    
    
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
                requester:IntentProvider = task_definition["requester"]
                action:Action = self.__action_book[intent_name]["action"]
                
                executable = copy.deepcopy(action)  
                # implement flywheeel pattern here              
                result:ActionResponse = await executable.execute(requester, self.__modules, args)
                events = result.events
                
                if requester:
                    await  requester.onIntentProcessResult(requestid, result.data)
                                 
            except Exception as e:
                
                err = "Error executing action " + str(e)                
                self.logger.debug(err)
                
                if requester:
                    await  requester.onIntentProcessError(requestid, e) 
                
            finally:
                task_queue.task_done()
                
                if requestid != None:
                    del self.__request_register[requestid]
                                
                if events != None:
                    pubsub = self.__modules.getModule(PUBSUBHUB_MODULE)
                    for event in events:
                        await pubsub.publish_event_type(event)




'''
Delegate interface for communication layer across the application
''' 
class CommunicationHub(IEventHandler, IEventDispatcher):
    
    '''
    classdocs
    '''


    def __init__(self, conf=None):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__interfaces = {}
        self.__channel_data = {}


    
    def register_interface(self, name:Text, role:Text, mod:IClientChannel)->None:
        
        if not role in built_in_client_types():
            raise ValueError("Invalid client type")
        
        
        self.__channel_data[name] = {}
        self.__interfaces[name] = mod
        pass
    
    
    
    def deregister_interface(self, name:Text)->None:        
        del self.__interfaces[name]
        del self.__channel_data[name]
        pass
    
    
    
    def activate_interface(self, name:Text)->None:
        mod = self.__interfaces[name]
        if mod:
            self._activate(name)
        pass
    
    
    def deactivate_interface(self, name:Text)->None:
        mod = self.__interfaces[name]
        if mod:
            self._deactivate(name)
        pass
    
    
    def _activate(self, name:Text)->None:
        pass
    
    
    
    def _deactivate(self, name:Text)->None:
        pass
    
    
    
    '''
    Overridden to provide list of events that we are interested to listen to 
    '''
    def get_events_of_interests(self)-> set:
        return []
    
    
    
    '''
    Overridden to provide list of events that we are interested to listen to 
    '''
    def get_topics_of_interests(self)-> set:
        return []
    
    
    
    '''
    Overridden to handle events subscribed to
    '''
    async def handleEvent(self, event:EventType):
        self.logger.info(event["name"] + " received")
        await self.__events.put(event)
        pass



class WebSocketClient(IModule):
    '''
    classdocs
    '''


    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__connection = None
        self.__connected = False
        self.__url = None
        
        
    
    
    '''
        creates connection to remote endpoint
    '''
    async def connect(self, url, reconnect = False):
        if(self.__connected == False):
            
            try:
                self.__connection = await websocket_connect(url, connect_timeout=6000,
                      ping_interval=15000, ping_timeout=3000)
            except Exception as e:
                self.logger.error("connection error. could not connect to remote endpoint " + url)
            else:
                self.logger.info("connected to remote endpoint " + url)
                self.__connected = True
                
                '''
                if reconnect == True:
                    tornado.ioloop.IOLoop.current().spawn_callback(self.__tail, name)
                '''
                
                self.__read_message()
                
    
    
    
    '''
        Special method to enforce reconnection to remote endpoint
    '''
    async def __reconnect(self):
        if self.__connected is None and self.__url is not None:
            await self.connect(self.__url)
        
    
    
    
    '''
        Read message from open websocket channel
    '''
    async def __read_message(self):
        while True:
            msg = await self.__connection.read_message()
            if msg is None:
                self.logger.info("connection to remote endpoint " + self.__url +"closed");
                self.__connection = None
                self.__connected = False
                break
    
    
    
    
    '''
        Write message in open websocket channel
    '''
    async def write_message(self, message, binary = False):
        if(self.__connected == True):
            self.__connection.write_message(message, binary);
                
    
    
    
    '''
        Closes connection
    '''
    async def closeConnection(self, code = None, reason = None):
        if(self.__connected == True):
            self.__connection.close(code, reason)
            self.__connection = None
            self.__connected = False
        
  