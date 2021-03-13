'''
Created on 05-Mar-2021

@author: root
'''


from oneadmin.responsebuilder import formatSuccessRPCResponse, formatErrorRPCResponse
from oneadmin.abstracts import IModule, IClientChannel, IntentProvider
from oneadmin.exceptions import RPCError, ModuleNotFoundError
from oneadmin.core.event import is_valid_event
from oneadmin.core.constants import TOPIC_EVENTS, TOPIC_PING
from oneadmin.responsebuilder import formatSuccessResponse


import logging
import sys
import tornado
import json

from tornado.queues import Queue
from typing import Text,List
from tornado.web import url



class RPCGateway(IModule, IntentProvider, IClientChannel):
    '''
    Class to handle RPC style communication over websockets.
    '''
    
    NAME = "rpc_gateway"
    
    
    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)       
        self.__requests = {}
        self.__mgsqueue = Queue()
        pass


    def get_url_patterns(self)->List:
        return [ url(r"/moduleapi/", SampleHandler) ]
    
    
        
    def getname(self) ->Text:
        return RPCGateway.NAME 
    
    
    
    def initialize(self) ->None:
        self.logger.info("Module init")
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
                


'''
Sample  handler
'''
class SampleHandler(tornado.web.RequestHandler):
    
    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)    
        pass

    def get(self):
        self.logger.info("sample path")
        self.write(json.dumps(formatSuccessResponse("Hello world")))
        self.finish()
