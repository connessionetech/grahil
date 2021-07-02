'''
Created on 14-Mar-2021

@author: root
'''


from concurrent.futures.thread import ThreadPoolExecutor
import shutil
from oneadmin.core.intent import INTENT_PREFIX
from oneadmin.core.action import ACTION_PREFIX, Action, ActionResponse
from oneadmin.core.constants import TOPIC_IDENTITY
from oneadmin.core.event import DataEvent
from oneadmin.core import grahil_types
import sys

import tornado
import subprocess
import socket
import os
import uuid

from tornado.process import Subprocess
from oneadmin.core.abstracts import IModule, IntentProvider
from oneadmin.responsebuilder import formatSuccessBotResponse, formatSuccessResponse
from tornado.web import url
import logging


from typing import Dict, Text, List





class SystemCore(IModule):
    '''
    classdocs
    '''
    
    NAME = "core"

    thread_pool = ThreadPoolExecutor(2)



    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__identity = None
        self.__interpreter = None
        self.__conf = conf
    
    
        
    def getname(self) ->Text:
        return SystemCore.NAME    
        

    
    def initialize(self) ->None:
        self.logger.debug("Module init")
        self.__interpreter = sys.executable
        tornado.ioloop.IOLoop.current().spawn_callback(self.__evaluate_identity)
    



    def valid_configuration(self, conf:Dict) ->bool:
        return True
    
    

    def get_url_patterns(self)->List:
        return [ ]
    
    
    
    '''
        Returns a list of supported actions
    '''
    def supported_actions(self) -> List[object]:
        return [ActionRestartSelf(), ActionUpdate()]


    '''
        Returns a list supported of action names
    '''
    def supported_action_names(self) -> List[Text]:
        return [ACTION_RESTART_SELF_NAME, ACTION_UPDATE_SELF_NAME]
    
    
    
    '''
        Returns a list supported of intents
    '''
    def supported_intents(self) -> List[Text]:
        return [INTENT_RESTART_SELF_NAME, INTENT_UPDATE_SELF_NAME]





    async def __evaluate_identity(self):

        if "identity" in self.__conf and self.__conf["identity"] != "":
            self.__identity = self.__conf["identity"]
            await self.dispatchevent(DataEvent(TOPIC_IDENTITY, data={"identity": self.__identity}))
        else:
            try:
                uid = await self.__get_uid()
                address = await self.__get_ip()

                if isinstance(uid, str):
                    self.__identity = uid + "@" + address
                else:
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
    async def reload(self):
        '''
        root_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        script_path = os.path.join(root_path, "reload.sh")
        bashCommand = script_path
        '''
        self.logger.info("Restarting...")        
        tornado.ioloop.IOLoop.current().run_in_executor(SystemCore.thread_pool, lambda : subprocess.run(["systemctl", "restart", "grahil.service"]))
        pass


    
    '''
    Triggers update script
    '''
    async def update(self):

        self.logger.info("updating...")
        pass



    '''
    Synchronous function to move update scripts to a different location before running update
    '''
    def copy_update_scripts(self, src:str, dest:str) ->bool:

        try:
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            return True

        except Exception as e:
            return False





INTENT_RESTART_SELF_NAME = INTENT_PREFIX + "restart_self"
INTENT_UPDATE_SELF_NAME = INTENT_PREFIX + "update_self"

ACTION_RESTART_SELF_NAME = ACTION_PREFIX + "restart_self"
ACTION_UPDATE_SELF_NAME = ACTION_PREFIX + "update_self"



class ActionRestartSelf(Action):

    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_RESTART_SELF_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        logging.info("Self restart")

        __core = None
        if modules.hasModule(SystemCore.NAME):
                __core:SystemCore = modules.getModule(SystemCore.NAME)
                __ver = await __core.reload()
                return ActionResponse(data = __ver, events=[])
        else:
                raise ModuleNotFoundError("`" + SystemCore.NAME + "` module does not exist")
        pass



class ActionUpdate(Action):

    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_UPDATE_SELF_NAME
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        logging.info("Update")

        __core = None
        if modules.hasModule(SystemCore.NAME):
                __core:SystemCore = modules.getModule(SystemCore.NAME)
                __ver = await __core.update()
                return ActionResponse(data = __ver, events=[])
        else:
                raise ModuleNotFoundError("`" + SystemCore.NAME + "` module does not exist")
        pass


