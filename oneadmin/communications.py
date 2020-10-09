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
    
    def __init__(self, conf, modules):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__task_queue = {}
        self.__system_modules = modules
        self.__initialize()
        pass
    
    
    def __initialize(self):
        self.__task_queue["start_target"] = Queue(maxsize=5)
        self.__task_queue["stop_target"] = Queue(maxsize=5)
        self.__task_queue["restart_target"] = Queue(maxsize=5)
        self.__task_queue["subscribe_channel"] = Queue(maxsize=5)
        self.__task_queue["unsubscribe_channel"] = Queue(maxsize=5)
        self.__task_queue["create_channel"] = Queue(maxsize=5)
        self.__task_queue["remove_channel"] = Queue(maxsize=5)
        self.__task_queue["publish_channel"] = Queue(maxsize=5)
        self.__task_queue["run_diagnostics"] = Queue(maxsize=5)
        self.__task_queue["browse_fs"] = Queue()
        self.__task_queue["delete_file"] = Queue(maxsize=3)
        self.__task_queue["fulfillRequest"] = Queue(maxsize=5)
        
        for rpc_task in self.__task_queue:
            tornado.ioloop.IOLoop.current().spawn_callback(self.__task_processor, rpc_task)
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
            args = [] 
        else: 
            args = message["params"]
         
        if(methodname in self.__task_queue and hasattr(self, methodname) and callable(getattr(self, methodname))):
            try:
                # Add task to relevant queue
                task_info = {"caller": wshandler, "requestid":requestid, "method": str(methodname), "params": args}
                task_queue = self.__task_queue[str(methodname)]
                task_queue.put(task_info)
            except:
                raise RPCError("Failed to invoke method " + sys.exc_info())
        else:
            raise RPCError("No method found by name " + methodname)
        
        pass
    
    
    '''
        Task Queue Processor - (Per Task)
    '''
    async def __task_processor(self, topic):
        while True:
            
            if not topic in self.__task_queue:
                break
            
            # task_info = {"caller": wshandler, "requestid":requestid, "method": str(methodname), "params": args}
            task_queue = self.__task_queue[topic]
            response = None
        
            try:
                task_definition = await task_queue.get()
                
                requestid = task_definition["requestid"]
                handler = task_definition["caller"]
                methodname = task_definition["method"]
                args = task_definition["params"]
                
                method_to_call = getattr(self, methodname)
                result = await method_to_call(handler, args)
                
                self.logger.debug("RPC Success")
                response = formatSuccessRPCResponse(requestid, result)
                
            except Exception as e:
                err = "Error executing RPC " + str(e)                
                self.logger.debug(err)
                response = formatErrorRPCResponse(requestid, err)
                
            finally:
                task_queue.task_done()
                self.logger.debug("write status for requestid " + str(requestid) + " to client")
                
                try:
                    if handler != None and handler.finished == False:
                        await handler.submit(response)
                except Exception as e1:
                    self.logger.warn("Unable to write message to client %s", handler.id)
        pass
    
    
    
    
    '''
        Runs system diagnostics and generates report
    '''
    async def run_diagnostics(self, handler, params=None):
        
        __sysmon = None
        
        if self.__system_modules.hasModule("sysmon"):
            __sysmon = self.__system_modules.getModule("sysmon")
            
        if(__sysmon != None):        
            return await __sysmon.run_system_diagnostics()
        else:
            raise ModuleNotFoundError("`sysmon` module does not exist")
        pass
    
    
    
    
    
    '''
        Publishes message to channel
        
        Payload content =>
        topicname : The topic name to publish message at 
        message : A arbitrary string
    '''
    async def publish_channel(self, handler, params):
        self.logger.debug("publish_channel")
        
        __pubsubhub = None
        
        if self.__system_modules.hasModule("pubsub"):
            __pubsubhub = self.__system_modules.getModule("pubsub")
        
        if(__pubsubhub != None):
            topicname = params[0]  
            message = params[1]        
            __pubsubhub.publish(topicname, message, handler)
        pass
           
            
    
    '''
        Creates a channel
        
        Payload content =>
        channel_info : channel info object (JSON) containing parameters to create new channel
        {name=<topicname>, type=<topictype>, queue_size=<queue_size>, max_users=<max_users>}
    '''        
    async def create_channel(self, handler, params):
        self.logger.debug("create_channel")
        
        __pubsubhub = None
        
        if self.__system_modules.hasModule("pubsub"):
            __pubsubhub = self.__system_modules.getModule("pubsub")
            
        if(__pubsubhub != None):
            channel_info = params[0]  
            channel_info['type'] = "bidirectional"      
            __pubsubhub.createChannel(channel_info)
        else:
            raise ModuleNotFoundError("`PubSub` module does not exist")
        pass
    
    
    
    '''
        Removes a channel
        
        Payload content =>
        topicname : The topic name to remove 
    '''
    async def remove_channel(self, handler, params):
        self.logger.debug("remove_channel")
        
        __pubsubhub = None
        
        if self.__system_modules.hasModule("pubsub"):
            __pubsubhub = self.__system_modules.getModule("pubsub")
        
        if(__pubsubhub != None):
            channel_name = params[0]        
            __pubsubhub.removeChannel(channel_name)
        else:
            raise ModuleNotFoundError("`PubSub` module does not exist")
        pass



    '''
        subscribes to a channel
        
        Payload content =>
        topicname : The topic name to remove 
    '''
    async def subscribe_channel(self, handler, params):
        self.logger.debug("subscribe_topic")
        
        __pubsubhub = None
        
        if self.__system_modules.hasModule("pubsub"):
            __pubsubhub = self.__system_modules.getModule("pubsub")
        
        if(__pubsubhub != None):
            topic = params[0]
            finalparams = params.copy() 
            if(len(finalparams)>1):       
                del finalparams[0] 
                       
            __pubsubhub.subscribe(topic, finalparams, handler)
        else:
            raise ModuleNotFoundError("`PubSub` module does not exist")
        pass
    
    
    
    '''
        unsubscribes from a channel
        
        Payload content =>
        topicname : The topic name to unsubscribe from 
    '''
    async def unsubscribe_channel(self, handler, params):
        self.logger.debug("unsubscribe_topic")
        
        __pubsubhub = None
        
        if self.__system_modules.hasModule("pubsub"):
            __pubsubhub = self.__system_modules.getModule("pubsub")
        
        if(__pubsubhub != None):
            topic = params[0]       
            __pubsubhub.unsubscribe(topic, handler)
        else:
            raise ModuleNotFoundError("`PubSub` module does not exist")
        pass
    
    
    
    '''
        Starts the target delegate
        
        Payload content => NONE 
    '''
    async def start_target(self, handler, params):
        self.logger.debug("start_target")
        
        if self.__system_modules.hasModule("target_delegate"):
            __delegate = self.__system_modules.getModule("target_delegate")
            await __delegate.start_proc()
        else:
            raise ModuleNotFoundError("`TargetDelegate` module does not exist")
        pass
    
    
    
    '''
        Stops the target delegate
        
        Payload content => NONE 
    '''
    async def stop_target(self, handler, params):
        self.logger.debug("stop_target")
        
        if self.__system_modules.hasModule("target_delegate"):
            __delegate = self.__system_modules.getModule("target_delegate")
            await __delegate.stop_proc()
        else:
            raise ModuleNotFoundError("`TargetDelegate` module does not exist")
        pass
    
    
    
    '''
        Restarts the target delegate
        
        Payload content => NONE 
    '''
    async def restart_target(self, handler, params):
        self.logger.debug("restart_target")
        
        __delegate = None
        if self.__system_modules.hasModule("target_delegate"):
            __delegate = self.__system_modules.getModule("target_delegate")
            await __delegate.restart_proc()
        else:
            raise ModuleNotFoundError("`TargetDelegate` module does not exist")
        pass
    
    
    
    '''
        Calls arbitrary method in TargetDelegate impl
        
        Payload content =>
        command : method name to invoke
        params : arbitrary array of parameters  
    '''
    async def fulfillRequest(self, handler, params):
        self.logger.debug("custom RPC call")
        
        __delegate = None
        
        if self.__system_modules.hasModule("target_delegate"):
            __delegate = self.__system_modules.getModule("target_delegate")
            
        if(__delegate != None):
            if(len(params)<1):
                raise Exception("Minimum of one parameter is required for this method call")
            command = str(params[0])
            self.logger.debug(command)
            finalparams = params.copy()
            del finalparams[0]
            return __delegate.fulfillRequest(command, finalparams)
        else:
            raise ModuleNotFoundError("`TargetDelegate` module does not exist")
        pass
    
    
    
    '''
        Gets filesystem listing for a specified path. 
        of target delegate.
        
        Payload content =>
        path : Path to scan for files and folders.Path should be a sub path within the access scope.  
    '''
    async def browse_fs(self, handler, params):
        self.logger.info("browse_fs")
        
        __filemanager = None
        
        if self.__system_modules.hasModule("file_manager"):
            __filemanager = self.__system_modules.getModule("file_manager")
        
        if(__filemanager != None):
            path = str(params[0])
            result = await __filemanager.browse_content(path)
            return result
        else:
            raise ModuleNotFoundError("`FileManager` module does not exist")
        pass
    
    

    '''
        delete file from a specified path.
        
        Payload content =>
        path : Path of file to delete.  
    '''
    async def delete_file(self, handler, params):
        self.logger.info("delete_file")
        
        __filemanager = None
        
        if self.__system_modules.hasModule("file_manager"):
            __filemanager = self.__system_modules.getModule("file_manager")
        
        if(__filemanager != None):
            path = str(params[0])
            result = await __filemanager.deleteFile(path)
            return result
        else:
            raise ModuleNotFoundError("`FileManager` module does not exist")
        pass
        



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
        self.__notifyable = None
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
        
        
    @property    
    def notifyable(self):
        return self.__notifyable
        
    @notifyable.setter
    def notifyable(self, notifyable):
        self.__notifyable = notifyable
        
        
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
        for key in self.channels:
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
                    # Notify reaction engine
                    if self.__notifyable != None and self.__isValidReactableEvent(message) == True:
                        await self.__notifyable.notifyEvent(message)
                except Exception as e:
                        err = "An error occurred in reaction engine while reacting to this event." + str(e)
                        self.logger.error(err)
                
            except:
                logging.error("Oops!,%s,occurred.", sys.exc_info()[0])
            finally:            
                msgque.task_done()