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
from oneadmin.utilities import buildLogWriterRule
from oneadmin.exceptions import RulesError
from oneadmin.abstracts import IEventDispatcher, IClientChannel, IntentProvider
from oneadmin.exceptions import RPCError, ModuleNotFoundError
from oneadmin.core.event import EventType, PingEvent, is_valid_event
from oneadmin.core.constants import TOPIC_EVENTS, TOPIC_PING


import logging
import sys
import tornado
import datetime
import asyncio

from tornado.queues import Queue
from tornado.websocket import websocket_connect




class RPCGateway(IEventDispatcher, IntentProvider, IClientChannel):
    '''
    Class to handle RPC style communication over websockets.
    '''
    
    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)       
        self.__requests = {}
        self.__mgsqueue = Queue()
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__notifyHandler)
        pass
    

    
    
    def isRPC(self, message):
        return message["type"] == "rpc"
    
    
    
    
    async def handleRPC(self, wshandler, message):
        
        if(not self.isRPC(message)):
            raise RPCError("Invalid message type. Not a RPC'")
        if(message["intent"] == None):
            raise RPCError("Missing parameter 'intent'")        
        if(message["requestid"] == None):
            raise RPCError("Missing parameter 'requestid'")
        
        local_request_id = message["requestid"]
        intent = message["intent"]
        
        args = {} if message["params"] is None else message["params"] 
        args["handler"]= wshandler
        
        try:
            requestid = await self.notifyintent(intent, args)
            self.__requests[requestid] = {"local_request_id": local_request_id, "handler": wshandler}
        
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
        response = formatSuccessRPCResponse(local_request_id, result)
        await self.__mgsqueue.put({"requestid": requestid, "message": response})
        pass
    

    
    '''
    Overriden method from intent provider, handles intent execution error
    '''
    async def onIntentProcessError(self, requestid:str, e:object, message:str = None) -> None:
        self.logger.debug("onIntentProcessError")
        local_request_id  = self.__requests[requestid]["local_request_id"]
        err = str(e)
        response = formatErrorRPCResponse(local_request_id, err)
        await self.__mgsqueue.put({"requestid": requestid, "message": response})
        pass
    
    
    
    
    async def __notifyHandler(self):
        while True:
            try:
                
                data = await self.__mgsqueue.get()
                requestid = data["requestid"]
                response = data["message"]
                handler = self.__requests[requestid]["handler"]
                local_request_id  = self.__requests[requestid]["local_request_id"]
                
                if handler != None and handler.is_closed() == False:
                    self.logger.debug("write status for requestid " + str(requestid) + " to client")
                    await handler.submit(response)
            
            except Exception as e1:
                
                self.logger.warn("Unable to write message to client %s", handler.id)
                
            finally:
                
                if requestid != None and requestid in self.__requests:
                    del self.__requests[requestid]
                
                self.__mgsqueue.task_done()



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
            
            if len(clients) == 0 and self.is_dynamic_channel(topicname):
                self.removeChannel(topicname)
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




'''
Created on 14-Sep-2020

@author: rajdeeprath
'''


class WebSocketClient(IEventDispatcher):
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
        
        