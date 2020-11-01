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

import tornado.web
import logging
import tornado.websocket
import json
from user_agents import parse
from oneadmin.responsebuilder import formatSuccessResponse,formatErrorResponse ,\
    formatProgressResponse, formatErrorRPCResponse
from oneadmin.communications import PubSubHub
from tornado.httputil import parse_multipart_form_data
from tornado.queues import Queue
from tornado.websocket import WebSocketClosedError
import base64
from tornado.escape import utf8
import uuid
from oneadmin import responsebuilder
from settings import settings
from oneadmin.exceptions import RPCError, AccessPermissionsError


# Create a base class
class LoggingHandler:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        
      
        

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
File ops handler - to be used for file read write
'''
class FileReadHandler(tornado.web.RequestHandler, LoggingHandler):
    
    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        pass
    
    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json')   

    # read file
    async def post(self):
        
        modules = self.application.modules
        
        if modules.hasModule("file_manager"):
        
            filepath = self.get_argument("path", None, True)
            self.logger.info("Read file request for file %s", filepath)
            
            if(filepath != None):   
                try:
                    content = await self.__getFile(filepath)
                    self.write(json.dumps(formatSuccessResponse(content)))
                except Exception as e:
                    self.write(json.dumps(formatErrorResponse(str(e), 404)))
            else:
                self.write(json.dumps(formatErrorResponse("Invalid parameters", 400)))
                pass
            
        self.finish()
    
    
    async def __getFile(self, path):
        modules = self.application.modules
        filemanager = modules.getModule("file_manager")
        content = await filemanager.readFile(path);
        encoded = base64.b64encode(bytes(content, 'utf-8'))  
        encoded_str = encoded.decode('utf-8')
        return encoded_str
    
    
    
class FileWriteHandler(tornado.web.RequestHandler, LoggingHandler):
    
    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        pass
    
    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json')   

    # write file
    async def post(self):
        
        modules = self.application.modules
        
        if modules.hasModule("file_manager"):
            
            filepath = self.get_argument("path", None, True)
            content = self.get_argument("content", None, True)
            self.logger.debug("Read file request for file %s", filepath)
            
            # Try catch and then send back response as json formatted message
            if(filepath != None):
                try:   
                    content = await self.__putFile(filepath, content)
                    self.write(json.dumps(formatSuccessResponse(content)))
                except Exception as e:
                    self.write(json.dumps(formatErrorResponse(str(e), 404)))
            else:
                self.write(json.dumps(formatErrorResponse("Invalid parameters", 400)))
                pass
        
        self.finish()


    async def __putFile(self, path, encoded):
        modules = self.application.modules
        filemanager = modules.getModule("file_manager")
        decoded = responsebuilder.base64ToString(encoded)
        await filemanager.writeFile(path, decoded)
        pass




class FileDownloadHandler(tornado.web.RequestHandler, LoggingHandler):
    
    CHUNK_SIZE = 256 * 1024
    
    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        pass
            

    async def post(self, slug=None):
        
        modules = self.application.modules
        
        if modules.hasModule("file_manager"):
            filemanager = modules.getModule("file_manager")
            
            if slug == "static":
                try:
                    path = self.get_argument("path", None, True)
                    download_path = await self.__makeFileDownloadable(path)
                    self.write(json.dumps(formatSuccessResponse(download_path)))
                except Exception as e:
                    self.write(json.dumps(formatErrorResponse(str(e), 404)))
                finally:
                    self.finish()
            elif slug == "chunked"  or slug == None:
                try:
                    path = self.get_argument("path", None, True)
                    file_name = filemanager.path_leaf(path)
                    self.set_header('Content-Type', 'application/octet-stream')
                    self.set_header('Content-Disposition', 'attachment; filename=' + file_name)
                    await self.flush()
                    await self.__makeChunkedDownload(path)
                except Exception as e:
                    self.write(json.dumps(formatErrorResponse(str(e), 404)))
                finally:  
                    self.finish()
                    pass
            else:
                self.finish(json.dumps(formatErrorResponse("Invalid action request", 403)))
            pass
    
    
    async def __makeFileDownloadable(self,file_path):
        modules = self.application.modules
        filemanager = modules.getModule("file_manager")
        configuration = self.application.configuration
        static_path = settings["static_path"]
        download_path = await filemanager.make_downloadable_static(configuration, static_path, file_path)
        return download_path
    
    
    async def __makeChunkedDownload(self, path):
        modules = self.application.modules
        filemanager = modules.getModule("file_manager")
        await filemanager.download_file_async(path, FileDownloadHandler.CHUNK_SIZE, self.handle_data)
        pass
    
    
    async def handle_data(self, chunk):
        self.logger.info("Writing chunk data")
        self.write(chunk)
        await self.flush()
        pass
    


class FileDeleteeHandler(tornado.web.RequestHandler, LoggingHandler):
    
    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        pass

    # write file
    async def delete(self):
        
        modules = self.application.modules
        
        if modules.hasModule("file_manager"):
            
            filepath = self.get_argument("path", None, True)
            self.logger.debug("Read file request for file %s", filepath)
            
            # Try catch and then send back response as json formatted message
            if(filepath != None):
                try:   
                    content = await self.__delete(filepath)
                    self.write(json.dumps(formatSuccessResponse(content)))
                except Exception as e:
                    self.write(json.dumps(formatErrorResponse(str(e), 404)))
            else:
                self.write(json.dumps(formatErrorResponse("Invalid parameters", 400)))
                pass
        
        self.finish()


    async def __delete(self, path):
        modules = self.application.modules
        filemanager = modules.getModule("file_manager")
        await filemanager.deleteFile(path)
        pass




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

    
    def on_ping(self):
        pass
    
    
    
    def on_pong(self, data):
        pass
    
    
    
    def __clearSubscriptions(self):
        modules = self.application.modules
        pubsubhub = modules.getModule("pubsub")
        self.application.unregisterClient(self)
        pubsubhub.clearsubscriptions(self)
        pass
    
    
    async def __cancelRecordings(self):
        modules = self.application.modules
        rpc_gateway = modules.getModule("rpc_gateway")
        if rpc_gateway != None:  
            for k in self.liveactions['logrecordings'].copy():
                await rpc_gateway.stop_log_recording(self, [k])


    async def on_message(self, message):
        self.logger.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        await self.__processMessages(parsed)
        pass
    
    
    async def __processMessages(self, message):
        
        modules = self.application.modules
        
        if modules.hasModule("rpc_gateway"):
            rpcgateway = modules.getModule("rpc_gateway")
        
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
        pubsubhub.subscribe_topics([PubSubHub.PING], self)
        
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
    
    
    async def run(self):
        while not self.finished:
            message = await self.messages.get()
            self.send(message)


    def send(self, message):
        try:
            self.write_message(message)
        except WebSocketClosedError :
            tornado.ioloop.IOLoop.current().spawn_callback(lambda: self._close())
            
            
