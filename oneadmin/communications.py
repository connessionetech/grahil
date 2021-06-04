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

from oneadmin.responsebuilder import formatSuccessRPCResponse, formatErrorRPCResponse
from oneadmin.core.utilities import buildLogWriterRule
from oneadmin.exceptions import RulesError
from oneadmin.core.abstracts import IEventDispatcher, IClientChannel, IntentProvider
from oneadmin.exceptions import RPCError, ModuleNotFoundError
from oneadmin.core.event import EventType, PingEvent, is_valid_event
from oneadmin.core.constants import TOPIC_EVENTS, TOPIC_PING


import logging
import sys
import tornado
import datetime
import asyncio

from tornado.queues import Queue




class PubSubHub(object):
    '''
    classdocs
    '''
        

    def __init__(self, config):
        '''
        Constructor
        '''        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__config = config
        self.__channels = {}
        self.__listeners = []
        self._initialize()
        
    def _initialize(self):
        
        pubsub_channels = self.__config["topics"]
        
        for channel_info in pubsub_channels:
            topicname = channel_info["name"]
            topictype = channel_info["type"]
            queuesize = channel_info["queue_size"]
            max_users = channel_info["max_users"]
            self.channels[topicname] = (topicname, topictype, Queue(maxsize=queuesize), set(), max_users)
        
        '''
        channels["topic_name"] = ('topic_type', 'public_or_private', {message_queue}, {subscribers_list}, max_users)
        '''
        
        self.logger.debug("total channels = %d", len(self.channels))
    
    
    
    def is_dynamic_channel(self, topicname):
        
        pubsub_channels = self.__config["topics"]
        
        for channel_info in pubsub_channels:
            if topicname == channel_info["name"]:
                return False
        
        return True 
        
    
    @property    
    def channels(self):
        return self.__channels
        
    
    @channels.setter
    def channels(self, _channels):
        self.__channels = _channels        
        
        
    def addEventListener(self, listener):
        self.__listeners.append(listener)
        
        
    def removeEventListener(self, listener):
        self.__listeners.remove(listener)
        
       
        
    def subscribe(self, topicname, client):
        
        if topicname not in self.channels:
            if self.__config["allow_dynamic_topics"] == True:
                channel_info = {}
                channel_info["name"] = topicname  
                channel_info['type'] = "bidirectional"
                channel_info["queue_size"] = 1
                channel_info["max_users"]  = 0
                self.createChannel(channel_info)
            else:
                self.logger.error("Topic channel %s does not exist and cannot be created either", topicname)
        else:
            clients = self.channels[topicname][3] #set
            clients.add(client);                
            self.logger.info("Total clients in %s = %d", topicname, len(clients))
        pass
    
    
    '''
        Client subscribe to multiple topics
    ''' 
    def subscribe_topics(self, topics, client):
        for topicname in topics:
            self.subscribe(topicname, client)
            pass    
    
    
    '''
        Client unsubscribes from topic
    '''
    def unsubscribe(self, topicname, client):
        if topicname in self.channels:
            clients = self.channels[topicname][3] #set
            clients.discard(client);
            self.logger.info("Total clients in %s = %d", topicname, len(clients))
            
            '''
            if len(clients) == 0 and self.is_dynamic_channel(topicname):
                self.removeChannel(topicname)
            '''
        pass
    
    
    
    '''
        clear all subscriptions
    '''
    def clearsubscriptions(self, client):
        for key in list(self.channels):
            self.logger.info("Clearing subscriptions in topic %s", key)
            self.unsubscribe(key, client)
        pass
    
    
    
    '''
        Creates a dynamic bidirectional communication channel
    '''
    def createChannel(self, channel_info, channel_type="bidirectional"):
        if "name" in channel_info and not channel_info["name"] in self.channels:
            topicname = channel_info["name"]
            topictype = channel_type
            queuesize = channel_info["queue_size"]
            max_users = channel_info["max_users"]
            self.logger.info("Registering channel %s", topicname)
            self.channels[topicname] = (topicname, topictype, Queue(maxsize=queuesize), set(), max_users)
            self.logger.debug("Activating message flush for topic %s", topicname)
            tornado.ioloop.IOLoop.current().spawn_callback(self.__flush_messages, topicname)
        pass
    
    
    '''
        Removes a communication channel
    '''
    def removeChannel(self, topicname):
        for k in list(self.channels.keys()):
            if k == topicname:
                channel = self.channels[topicname]
                
                # possible logic to cleanly dispose queue content
                msgque:Queue = channel[2] #queue
                while msgque.qsize() > 0:
                    item = msgque.get_nowait()
                    msgque.task_done()
                                        
                del msgque
                del self.channels[topicname]
                self.logger.info("Removed channel %s", topicname)
        pass
    
    
    
    '''
        Accepts data submission for topic
    '''
    async def __submit(self, topicname, message):
        if topicname in self.channels:
            msgque = self.channels[topicname][2] #queue
            await msgque.put(message)
        pass
    
    
    '''
        Publishes data to a specified topic, if it exists.
        If topic channel does not exist, it is created based on configuration
        parameter `allow_dynamic_topic`
    '''
    async def publish(self, topicname, message, client=None):
        if topicname not in self.channels:
            if self.__config["allow_dynamic_topics"] == True:
                channel_info = {}
                channel_info["name"] = topicname  
                channel_info['type'] = "bidirectional"
                channel_info["queue_size"] = 1
                channel_info["max_users"]  = 0
                self.createChannel(channel_info)
                await self.__submit(topicname, message)
            else:
                self.logger.error("Topic channel does not exist and cannot be created either")
        else:
            await self.__submit(topicname, message)
        pass
    
    
    '''
        Publishes event data to a events channel - "/events"
        *To be deprecated in favor of new event system*
    '''
    async def publish_event(self, event):
        if TOPIC_EVENTS in self.channels:
            if self.__isValidEvent(event):
                await self.__submit(TOPIC_EVENTS, event)
        pass
    
    
    
    
    '''
        Publishes event to designated channel
    '''
    async def publish_event_type(self, event:EventType):
        
        if "topic"in event:
            
            if event["topic"] not in self.channels and self.__config["allow_dynamic_topics"] == True:
                self.createChannel({"name": event["topic"], "type": "bidirectional", "queue_size": 0, "max_users": 0})
        
            if event["topic"] in self.channels:
                if is_valid_event(event):
                    await self.__submit(event["topic"], event)
            pass
        
    
    
    
    '''
        Validates message as `event`for reactionengine
    '''
    def __isValidReactableEvent(self, event):
        # validate event object and place in queue
        if 'topic' in event and 'data' in event:
            return True
        return False
    
    
    
    
    
    '''
    Activate auto message flush for all channels
    '''
    def activate_message_flush(self):
        for topic in self.channels:
            self.logger.debug("Activating message flush for topic %s", topic)
            tornado.ioloop.IOLoop.current().spawn_callback(self.__flush_messages, topic)
            pass
    pass



    
    
    '''
    Flushes messages from  channel queue into client's message queue actively
    '''
    async def __flush_messages(self, topic):        
        while True:
            
            try:
                if(not topic in self.channels):
                    break
                
                channel = self.channels[topic]
                msgque:Queue = channel[2] #queue
                clients:set = channel[3] #set
                
                message = await msgque.get()                
                
                if len(clients) > 0:
                    self.logger.debug("Pushing message %s to %s subscribers...",format(message), len(clients))
                    
                    ''' pushing to clients '''
                    try:    
                        for clients in clients:
                            await clients.submit(message)
                    except Exception as e:
                        logging.error("An error occurred pushing messages to client %s for topic %s. Cause : %s.", str(client), topic, str(e))
                    
                
                ''' pushing to listeners '''
                try:
                    for listener in self.__listeners:
                        await listener._notifyEvent(message)                            
                except Exception as e:
                        self.logger.error("An error occurred notifying %s while reacting to this event.%s", str(listener), str(e))
                
            except GeneratorExit as ge:
                logging.error("GeneratorExit occurred")
                return
            
            except Exception as re:
                logging.error("Unexpected error occurred, which caused by %s", str(re))
                
            finally:
                msgque.task_done()




