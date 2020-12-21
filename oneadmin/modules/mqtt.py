'''
Created on 19-Dec-2020

@author: root
'''
from abstracts import IEventDispatcher, IntentProvider, IClientChannel,\
    IMQTTClient
from core.components import ActionDispatcher
from tornado.platform import asyncio

import asyncio
from contextlib import AsyncExitStack
from asyncio_mqtt import Client, MqttError
from builtins import str
import tornado
from tornado.queues import Queue
import logging
from paho.mqtt.subscribeoptions import SubscribeOptions
from typing import Text, Callable, List
from exceptions import RPCError
from utilities import is_data_message, is_command_message, has_sender_id_message,\
    has_uuid_message, requires_ack_message
import sys
import json
from responsebuilder import formatSuccessMQTTResponse, formatErrorMQTTResponse



class MQTTGateway(IMQTTClient, IEventDispatcher, IntentProvider, IClientChannel):
    '''
    Class to handle RPC style communication over MQTT.
    
    
    Request/command with response
    ----------------------------
    
    {
     "client-id": <sender>,
     "session-id":  <uuid>,
     "intent": <intent>,
     "data": {
        "params": {
            "param": <value>
        },
        "res-topic": <responder-topic>
     },
     "timestamp": <utc-timestamp>
    }
    
    
    
    Request/command without response
    ------------------------------
    
    {
     "client-id": <sender>,
     "session-id":  <uuid>,
     "intent": <intent>,
     "data": {
        "params": {
            "param": <value>
        }
     },
     "timestamp": <utc-timestamp>
    }
    
    
    
    data feed - with ack
    ------------------------------
    
    {
     "client-id": <sender>,
     "session-id":  <uuid>,
     "data": {
        "params": {
            "param": <value>
        },
        "res-topic": <responder-topic>
     },
     "timestamp": <utc-timestamp>
    }
    
    
    
    
    data feed - no ack
    ------------------------------
    
    {
     "client-id": <sender>
     "session-id":  <uuid>
     "data": {
        "params": {
            "param": <value>
        },
        "res-topic": <responder-topic>
     },
     "timestamp": <utc-timestamp>
    }
    
    
    '''
    
    def __init__(self, conf:dict, executor:ActionDispatcher) ->None:
        '''
        Constructor
        '''
        
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__action_dispatcher = executor
        self.__conf = conf       
        self.__requests = {}
        self.__mgsqueue = Queue()
        
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__notifyHandler)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__initialize)
        pass
    
    
    
    async def _setup(self):
        # We 💛 context managers. Let's create a stack to help
        # us manage them.
        async with AsyncExitStack() as stack:
            # Keep track of the asyncio tasks that we create, so that
            # we can cancel them on exit
            tasks = set()
            stack.push_async_callback(self.cancel_tasks, tasks)
    
            # Connect to the MQTT broker
            self.client = Client(self.__conf["host"])
            await stack.enter_async_context(self.client)
    
            # You can create any number of topic filters
            topic_filters = tuple(self.__conf["topic_filters"])
            for topic_filter in topic_filters:
                # Log all messages that matches the filter
                manager = self.client.filtered_messages(topic_filter)
                messages = await stack.enter_async_context(manager)
                template = f'[topic_filter="{topic_filter}"] {{}}'
                task = asyncio.create_task(self.messages_with_filter(messages, template))
                tasks.add(task)
    
            # Messages that doesn't match a filter will get logged here
            messages = await stack.enter_async_context(self.client.unfiltered_messages())
            task = asyncio.create_task(self.messages_without_filter(messages, "[unfiltered] {}"))
            tasks.add(task)
    
            # Subscribe to topic(s)
            # 🤔 Note that we subscribe *after* starting the message
            # loggers. Otherwise, we may miss retained messages.
            subscribe_topics:list = self.__conf["subscriptions"]
            subscriptions:list = []
            
            for subscribe_topic in subscribe_topics:
                subscriptions.append((subscribe_topic["topic"], subscribe_topic["qos"]))
            
            await self.client.subscribe(subscriptions)
    
           
            # Wait for everything to complete (or fail due to, e.g., network
            # errors)
            await asyncio.gather(*tasks)
        
    
    
    async def post_to_topics(self, client:Client, topic:str, message:str)->None:
        await client.publish(topic, message, qos=1)
        await asyncio.sleep(.1)
        
        
    
    '''
    Overridden method from IMQTTClient
    '''
    async def publish_to_topic(self, topic:str, message:str, callback:Callable=None)->None:
        await self.client.publish(topic, message, qos=1)
        pass
    
    
    
    '''
    Overridden method from IMQTTClient
    '''
    async def publish_to_topics(self, topics:List[str], message:str, callback:Callable=None)->None:
        for topic in topics:
            await self.client.publish(topic, message)
        pass


    
    
    async def messages_with_filter(self, messages, template):
        async for message in messages:
            # 🤔 Note that we assume that the message paylod is an
            # UTF8-encoded string (hence the `bytes.decode` call).
            self.logger.info("messages_with_filter")
            self.logger.info(template.format(message.payload.decode()))
            await self. handleMessage(message.payload.decode())
            pass
        
        
        
    async def messages_without_filter(self, messages, template):
        async for message in messages:
            # 🤔 Note that we assume that the message paylod is an
            # UTF8-encoded string (hence the `bytes.decode` call).
            self.logger.info("messages_without_filter")
            self.logger.info(template.format(message.payload.decode()))
            await self. handleMessage(message.payload.decode())
            pass
    
    
    
    async def cancel_tasks(self, tasks):
        for task in tasks:
            if task.done():
                continue
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    
    
    async def __initialize(self):
        # Run the advanced_example indefinitely. Reconnect automatically
        # if the connection is lost.
        while True:
            try:
                await self._setup()
            except MqttError as error:
                self.logger.info(f'Error "{error}". Reconnecting in {reconnect_interval} seconds.')
            finally:
                await asyncio.sleep(self.__conf["reconnect_wait_time_seconds"])
    
    
    
    async def handleMessage(self, msg:str, handler=None):
        
        intent = None
        args = None
        sender = None
        restopic = None
        
        message = json.loads(msg)
        
        if is_command_message(message):
            intent = message["intent"]
            data = message["data"]
        elif is_data_message(message):
            data = message["data"]
        else:
            raise RPCError("Unknown message type")
        
        if has_uuid_message(message):
            local_request_id = message["session-id"]
        else:
            raise RPCError("Unknown message type")
        
        
        if has_sender_id_message(message):
            sender = message["client-id"]
            
        if requires_ack_message(message):
            restopic = data["res-topic"]
        
        intent = message["intent"]
        args = {} if data["params"] is None else data["params"]
        args["handler"]= self
        
        try:
            requestid = await self.__action_dispatcher.handle_request(self, intent, args)
            self.__requests[requestid] = {"local_request_id": local_request_id, "handler": handler, "client-id": sender, "res-topic": restopic}
        
        except:
            if requestid in self.__requests:
                del self.__requests[requestid]
                
            raise RPCError("Failed to invoke method." + str(sys.exc_info()[0]))
        pass
    
    
    
    '''
    Overriden method from intent provider, handles intent execution result
    '''
    async def onIntentProcessResult(self, requestid:str, result:object) -> None:
        self.logger.debug("onIntentProcessResult")
        local_request_id  = self.__requests[requestid]["local_request_id"]
        response = formatSuccessMQTTResponse(local_request_id, result)
        await self.__mgsqueue.put({"requestid": requestid, "message": response})
        pass
    

    
    '''
    Overriden method from intent provider, handles intent execution error
    '''
    async def onIntentProcessError(self, requestid:str, e:object, message:str = None) -> None:
        self.logger.debug("onIntentProcessError")
        local_request_id  = self.__requests[requestid]["local_request_id"]
        response = formatErrorMQTTResponse(local_request_id, str(e))
        await self.__mgsqueue.put({"requestid": requestid, "message": response})
        pass
    
    
    
    
    async def __notifyHandler(self):
        while True:
            try:
                data = await self.__mgsqueue.get()
                requestid = data["requestid"]
                response = data["message"]
                restopic = self.__requests[requestid]["res-topic"]
                
                if restopic != None:
                    self.logger.debug("write status for requestid " + str(requestid) + " to client")
                    await self.publish_to_topic(restopic, json.dumps(response))
                
                self.logger.info("Processing complete for message %s", requestid)
                
            except Exception as e1:
                self.logger.warn("Unable to write message to broker %s", str(e1))
                
            finally:
                self.__mgsqueue.task_done()
        pass
    