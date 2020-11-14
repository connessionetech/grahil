'''
This file is part of `Reactivity` 
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

from tornado.queues import Queue
import logging
import sys
from oneadmin.responsebuilder import formatSuccessRPCResponse, formatErrorRPCResponse
import tornado
from oneadmin.exceptions import RPCError, ModuleNotFoundError
import datetime
import asyncio
from oneadmin.utilities import buildLogWriterRule
from oneadmin.exceptions import RulesError


class Pinger(object):
    
    def __init__(self, conf):
        self.__conf = conf;
        self.__callback = None
        pass
    
    @property
    def callback(self):
        return self.__callback
    
    @callback.setter
    def callback(self, fun):
        self.__callback = fun
    
    
    async def __generatePing(self):
        while True:
            if self.__callback != None:
                        ping = datetime.datetime.utcnow().timestamp()
                        await self.__callback(ping, None)
            
            if self.__conf["ping_interval_seconds"] is not None:
                await asyncio.sleep(self.__conf["ping_interval_seconds"])
        pass
    
    
    def start(self):  
        if self.__conf is not None:      
            tornado.ioloop.IOLoop.current().spawn_callback(self.__generatePing)
        pass
    

class RPCGateway(object):
    '''
    classdocs
    '''
    
    def __init__(self, conf, executor):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__action_executor = executor        
        self.__requests = {}
        self.__mgsqueue = Queue(20)
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__notifyHandler)
        pass
    

    
    
    def isRPC(self, message):
        return message["type"] == "rpc"
    
    
    
    
    async def handleRPC(self, wshandler, message):
        
        if(not self.isRPC(message)):
            raise RPCError("Invalid message type. Not a RPC'")
        if(message["method"] == None):
            raise RPCError("Missing parameter 'method'")        
        if(message["requestid"] == None):
            raise RPCError("Missing parameter 'requestid'")
        
        requestid = message["requestid"]
        methodname = message["method"]
        
        if message["params"] is None: 
            args = [wshandler] 
        else: 
            args = message["params"]
            args.insert(0, wshandler)
        
        try:
        
            task_info = {"requestid":requestid, "method": str(methodname), "params": args}
            self.__requests[requestid] = wshandler
            await self.__action_executor.addTask(task_info)
        
        except:
            if requestid in self.__requests:
                del self.__requests[requestid]
                
            raise RPCError("Failed to invoke method." + sys.exc_info()[0])
        pass    
    
    
    
    
    async def onExecutionResult(self, requestid, result):
        self.logger.debug("RPC Success")
        response = formatSuccessRPCResponse(requestid, result)
        await self.__mgsqueue.put({"requestid": requestid, "message": response})
        pass
    
    
    
    async def onExecutionerror(self, requestid, e):
        self.logger.debug("RPC Error")
        err = str(e)
        response = formatErrorRPCResponse(requestid, err)
        await self.__mgsqueue.put({"requestid": requestid, "message": response})
        pass
    
    
    
    async def __notifyHandler(self):
        while True:
            try:
                
                data = await self.__mgsqueue.get()
                requestid = data["requestid"]
                response = data["message"]
                handler = self.__requests[requestid]  
                
                if handler != None and handler.finished == False:
                    self.logger.debug("write status for requestid " + str(requestid) + " to client")
                    await handler.submit(response)
            
            except Exception as e1:
                
                self.logger.warn("Unable to write message to client %s", handler.id)
                
            finally:
                self.__mgsqueue.task_done()



class PubSubHub(object):
    '''
    classdocs
    '''
    
    LOGMONITORING = "/logging"
    SYSMONITORING = "/stats"
    PING = "/ping"
    EVENTS = "/events"
    

    def __init__(self, config):
        '''
        Constructor
        '''        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__config = config
        self.__channels = {}
        self.__notifyables = []
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
        
        
    def addNotifyable(self, notifyable):
        self.__notifyables.append(notifyable)
        
        
    def removeNotifyable(self, notifyable):
        self.__notifyables.remove(notifyable)
        
        
    @property    
    def notifyables(self):
        return self.__notifyables
    
    
    @notifyables.setter
    def notifyables(self, notifyables):
        self.__notifyables = notifyables
        
        
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
    def createChannel(self, channel_info):
        if "name" in channel_info and not channel_info["name"] in self.channels:
            topicname = channel_info["name"]
            topictype = channel_info["type"]
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
        Publishes event data to a events channel
    '''
    async def publish_event(self, event):
        if PubSubHub.EVENTS in self.channels:
            if self.__isValidEvent(event):
                await self.__submit(PubSubHub.EVENTS, event)
        pass
    
    
    
    '''
        Validates message as `event` object and publishes to 'events' channel
    '''
    def __isValidEvent(self, event):
        # validate event object and place in queue
        if hasattr(event, "name") and hasattr(event, "category") and hasattr(event, "data"):
            return True
        return False
    
    
    
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
            if(not topic in self.channels):
                break
            
            channel = self.channels[topic]
            msgque = channel[2] #queue
            try:
                message = await msgque.get()
                
                clients = channel[3] #set
                if len(clients) > 0:
                    self.logger.debug("Pushing message %s to %s subscribers...".format(message, len(clients)))
                    for clients in clients:
                        await clients.submit(message)                
                                
                try:
                    # Notify notifyables
                    if self.__isValidReactableEvent(message) == True:
                        for notifyable in self.__notifyables:
                            await notifyable.notifyEvent(message)
                except Exception as e:
                        err = "An error occurred notifying %s while reacting to this event.%s"
                        self.logger.error(err, str(notifyable), str(e))
                
            except:
                logging.error("Oops!,%s,occurred.", sys.exc_info()[0])
            finally:            
                msgque.task_done()