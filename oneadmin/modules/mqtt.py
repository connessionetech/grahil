'''
Created on 19-Dec-2020

@author: root
'''
from abstracts import IEventDispatcher, IntentProvider, IClientChannel,\
    IMQTTClient
from core.components import ActionDispatcher
from tornado.platform import asyncio

import asyncio
from contextlib import AsyncExitStack, asynccontextmanager
from random import randrange
from asyncio_mqtt import Client, MqttError
from builtins import str
import tornado
from tornado.queues import Queue
import logging
from paho.mqtt.subscribeoptions import SubscribeOptions


class MQTTGateway(IMQTTClient, IEventDispatcher, IntentProvider, IClientChannel):
    '''
    Class to handle RPC style communication over MQTT.
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
            client = Client(self.__conf["host"])
            await stack.enter_async_context(client)
    
            # You can create any number of topic filters
            topic_filters = tuple(self.__conf["topic_filters"])
            for topic_filter in topic_filters:
                # Log all messages that matches the filter
                manager = client.filtered_messages(topic_filter)
                messages = await stack.enter_async_context(manager)
                template = f'[topic_filter="{topic_filter}"] {{}}'
                task = asyncio.create_task(self.messages_with_filter(messages, template))
                tasks.add(task)
    
            # Messages that doesn't match a filter will get logged here
            messages = await stack.enter_async_context(client.unfiltered_messages())
            task = asyncio.create_task(self.messages_without_filter(messages, "[unfiltered] {}"))
            tasks.add(task)
    
            # Subscribe to topic(s)
            # 🤔 Note that we subscribe *after* starting the message
            # loggers. Otherwise, we may miss retained messages.
            # subscribe([("my/topic", SubscribeOptions(qos=0), ("another/topic", SubscribeOptions(qos=2)])
            subscribe_topics:list = self.__conf["subscriptions"]
            subscriptions:list = []
            
            for subscribe_topic in subscribe_topics:
                subscriptions.append((subscribe_topic["topic"], subscribe_topic["qos"]))
            
            await client.subscribe(subscriptions)
    
           
            # Wait for everything to complete (or fail due to, e.g., network
            # errors)
            await asyncio.gather(*tasks)
        
    
    
    async def post_to_topics(self, client:Client, topic:str, message:str)->None:
        await client.publish(topic, message, qos=1)
        await asyncio.sleep(.1)

    
    
    async def messages_with_filter(self, messages, template):
        async for message in messages:
            # 🤔 Note that we assume that the message paylod is an
            # UTF8-encoded string (hence the `bytes.decode` call).
            self.logger.info("messages_with_filter")
            self.logger.info(template.format(message.payload.decode()))
            pass
        
        
        
    async def messages_without_filter(self, messages, template):
        async for message in messages:
            # 🤔 Note that we assume that the message paylod is an
            # UTF8-encoded string (hence the `bytes.decode` call).
            self.logger.info("messages_without_filter")
            self.logger.info(template.format(message.payload.decode()))
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
    
    
    
    
    async def handleRPC(self, wshandler, message):
        pass 
    
    
    
    '''
    Overriden method from intent provider, handles intent execution result
    '''
    async def onIntentProcessResult(self, requestid:str, result:object) -> None:
        pass
    

    
    '''
    Overriden method from intent provider, handles intent execution error
    '''
    async def onIntentProcessError(self, requestid:str, e:object, message:str = None) -> None:
        pass
    
    
    
    
    async def __notifyHandler(self):
        pass