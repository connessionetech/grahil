'''
Created on 14-Mar-2021

@author: root
'''


from concurrent.futures.thread import ThreadPoolExecutor
from oneadmin.core.constants import TOPIC_IDENTITY
from oneadmin.core.event import DataEvent
import sys

import tornado
import subprocess
import socket
import os
import uuid

from tornado.process import Subprocess
from oneadmin.core.abstracts import IModule
from oneadmin.responsebuilder import formatSuccessBotResponse, formatSuccessResponse
from tornado.web import url
import logging


from typing import Dict, Text, List





class SystemCore(IModule):
    '''
    classdocs
    '''
    
    NAME = "identity"

    thread_pool = ThreadPoolExecutor(2)



    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__identity = None
        self.__conf = conf
    
    
        
    def getname(self) ->Text:
        return SystemCore.NAME    
        

    
    def initialize(self) ->None:
        self.logger.info("Module init")
        tornado.ioloop.IOLoop.current().spawn_callback(self.__evaluate_identity)
    



    def valid_configuration(self, conf:Dict) ->bool:
        return True
    
    

    def get_url_patterns(self)->List:
        return [ ]
    
    
    
    '''
        Returns a list of supported actions
    '''
    def supported_actions(self) -> List[object]:
        return []


    '''
        Returns a list supported of action names
    '''
    def supported_action_names(self) -> List[Text]:
        return []
    
    
    
    '''
        Returns a list supported of intents
    '''
    def supported_intents(self) -> List[Text]:
        return []



    async def __evaluate_identity(self):

        if "identity" in self.__conf and self.__conf["identity"] != "":
            self.__identity = self.__conf["identity"]
            await self.dispatchevent(DataEvent(TOPIC_IDENTITY, data={"identity": self.__identity}))
        else:
            try:
                uid:uuid.UUID = await self.__get_uid()
                address = await self.__get_ip()
                self.__identity = str(uid.hex) + "@" + address
                await self.dispatchevent(DataEvent(TOPIC_IDENTITY, data={"identity": self.__identity}))
            except Exception as e:
                self.logger.error("Error evaluating identity %s", str(e))
    


    @property
    def identity(self):
        return self.__identity
    

    @identity.setter
    def identity(self, uuid):
        self.__identity = uuid


    
    '''
    Gets unique hardware identifier for this system
    '''
    async def __get_uid(self):

        try:
            bashCommand = "dmidecode -s system-uuid"
            proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
            await proc.wait_for_exit()
            output = proc.stdout.read()
            return output.decode('UTF-8').strip()
        except Exception as e:
            return uuid.UUID(int=uuid.getnode())


    
    async def __get_ip(self):
        return await tornado.ioloop.IOLoop.current().run_in_executor(SystemCore.thread_pool, self.get_ip_via_socket)

    
    
    '''
    Synchronous function to get own IP
    '''
    def get_ip_via_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP


    
    '''
    Restarts self
    '''
    def reload(self):
        root_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        script_path = os.path.join(root_path, "reload.sh")
        bashCommand = "nohup /bin/bash " + script_path + " " + "grahil.service"
        tornado.ioloop.IOLoop.current().run_in_executor(Identifier.thread_pool, lambda : subprocess.Popen(bashCommand.split()))
        pass