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

from oneadmin.responsebuilder import formatSuccessResponse,formatErrorResponse ,formatProgressResponse, formatErrorRPCResponse
from oneadmin.core.intent import INTENT_DELETE_FILE_NAME, INTENT_STOP_LOG_RECORDING_NAME
from oneadmin.communications import PubSubHub
from oneadmin import responsebuilder
from oneadmin.exceptions import RPCError, AccessPermissionsError
from oneadmin.core.constants import TOPIC_NOTIFICATION, TOPIC_PING, PUBSUBHUB_MODULE, RPC_GATEWAY_MODULE
from oneadmin.core.abstracts import LoggingHandler

import base64
import uuid
import tornado.web
import logging
import tornado.websocket
import json
from user_agents import parse
from settings import settings
from tornado.escape import utf8
from tornado.httputil import parse_multipart_form_data
from tornado.queues import Queue
from tornado.websocket import WebSocketClosedError

        
      
        

'''
Default  handler - do be removed / disabled / redirected later
'''
class MainHandler(tornado.web.RequestHandler, LoggingHandler):
    
    def initialize(self):
        pass

    # @tornado.web.authenticated
    def get(self):
        self.logger.info("index path")        



'''
Websocket connections handler - main entry point for clients
''' 
class WebSocketHandler(tornado.websocket.WebSocketHandler, LoggingHandler):
    
    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.messages = Queue()
        self.id = str(uuid.uuid4())
        self.liveactions = {}
        self.liveactions['logrecordings'] = set()
        self.finished = False
        pass

    def check_origin(self, origin):
        return True

    
    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    
    def open(self):
        self.logger.info("on open")
        tornado.ioloop.IOLoop.current().spawn_callback(lambda: self.__on_connect())
        pass

    
    def on_close(self):
        self.logger.info("on close");
        tornado.ioloop.IOLoop.current().spawn_callback(lambda: self._close())
        pass
    
    
    async def _close(self):        
        await self.__cancelRecordings()
        self.__clearSubscriptions()
        self.logger.info("Total clients %d", self.application.totalclients)
        self.finished = True
        
    
    def is_closed(self):
        return self.finished
        pass

    
    def on_ping(self):
        pass
    
    
    def on_pong(self, data):
        pass
    
    
    
    def __clearSubscriptions(self):
        modules = self.application.modules
        pubsubhub = modules.getModule(PUBSUBHUB_MODULE)
        self.application.unregisterClient(self)
        pubsubhub.clearsubscriptions(self)
        pass
    
    
    
    async def __cancelRecordings(self):
        __action_dispatcher = self.application.action_dispatcher
        for k in self.liveactions['logrecordings'].copy():
            await __action_dispatcher.handle_request(None, INTENT_STOP_LOG_RECORDING_NAME, {"rule_id": k, "handler": self})


    
    async def on_message(self, message):
        self.logger.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        await self.__processMessages(parsed)
        pass
    
    
    
    async def __processMessages(self, message):
        
        modules = self.application.modules
        
        if modules.hasModule(RPC_GATEWAY_MODULE):
            rpcgateway = modules.getModule(RPC_GATEWAY_MODULE)
        
            err = None
            response = None
            
            try:
                if rpcgateway.isRPC(message):
                    await rpcgateway.handleRPC(self, message)
                else:
                    self.logger.warn("Unknown message type received")
            except RPCError as re:
                err = "Error executing RPC " + str(re)                
                self.logger.warn(err)
            except Exception as e:
                err = "Unknown error occurred." + str(e)                
                self.logger.warn(err)                
            finally:
                try:
                    if err != None and self.finished == False:                    
                        response = formatErrorRPCResponse(message["requestid"], err)
                        await self.submit(response)
                except:
                    self.logger.warn("Unable to write message to client " + self.id)            
            pass
        else:
            err = "Feature unavailable" 
            response = formatErrorRPCResponse(message["requestid"], err)
            await self.submit(response)
    
    
    async def __on_connect(self):
        try:
            await self.joinApplication();
        except AccessPermissionsError as ae:
            self.close(401, str(ae))
        pass
    
    
    def __evalclient(self, request):
        user_agent_header = request.headers.get('User-Agent')
        if(user_agent_header is not None):            
            user_agent = parse(user_agent_header)
            self.useragent = user_agent
        else:
            self.useragent = None
        pass
    
    
    async def joinApplication(self):
        
        modules = self.application.modules
        pubsubhub = modules.getModule("pubsub")
        
        self.logger.info("joining")
        
        self.__evalclient(self.request)
        
        self.application.registerClient(self)
        
        self.logger.info("Total clients %d", self.application.totalclients)
        pubsubhub.subscribe_topics([TOPIC_PING], self)
        pubsubhub.subscribe_topics([TOPIC_NOTIFICATION], self)
        
        # Notify system capabilities to client on connect
        capabilities = self.application.get_system_capabilities()
        self.write_message(json.dumps(capabilities))
        
        # pubsubhub.subscribe_topics([PubSubHub.SYSMONITORING, PubSubHub.LOGMONITORING], self)
        # snapshot = self.application.getAggregatedStats()
        await self.run()
        pass        
    
    async def submit(self, message):
        await self.messages.put(message) 
        pass
    
    
    ''' Warning : check for need of task-done '''
    async def run(self):
        while not self.finished:
            try:
                message = await self.messages.get()
                self.send(message)
            except Exception as e:
                pass
            finally:
                self.messages.task_done()


    def send(self, message):
        try:
            self.write_message(message)
        except WebSocketClosedError :
            tornado.ioloop.IOLoop.current().spawn_callback(lambda: self._close())
            
            
