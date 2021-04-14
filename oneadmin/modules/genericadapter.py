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

from oneadmin.abstracts import IntentProvider
from oneadmin.core.constants import TARGET_DELEGATE_MODULE
from oneadmin.core.grahil_types import *
from oneadmin.exceptions import TargetServiceError
from oneadmin.responsebuilder import buildDataNotificationEvent  
from oneadmin.abstracts import TargetProcess
from oneadmin.core.intent import INTENT_PREFIX
from oneadmin.core.action import Action, ACTION_PREFIX, ActionResponse

import tornado
import os
import tempfile
import time
import logging
import sys
import signal
import subprocess

from builtins import int, str
from tornado.ioloop import IOLoop
from tornado.concurrent import asyncio
from tornado.process import Subprocess
from typing import Text, List, Dict 
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError
from settings import settings
import json

import re
from core.constants import TOPIC_NOTIFICATIONS, NOTIFICATIONS_WARN,\
    NOTIFICATIONS_NOTICE
from core.event import SimpleTextNotificationEvent



class GenericDelegate(TargetProcess):
    '''
    classdocs
    '''    
    
    NAME = "generic_delegate"
    

    def __init__(self, conf=None):
        '''
        Constructor
        '''
        super().__init__("red5")
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
        
        
        ''' logs to monitor'''
        
        log_paths = []        
        log_root = self.__conf["log_root"]
        log_targets = self.__conf["log_targets"]
        for log_target in log_targets:
            log_paths.append(os.path.join(log_root, str(log_target)))
            
        self.setLogFiles(log_paths)
        
        
        ''' Allowed file extensions access'''
        
        allowed_read_extensions = self.__conf["allowed_read_extensions"]
        self.setAllowedReadExtensions(allowed_read_extensions)
        
        allowed_write_extensions = self.__conf["allowed_write_extensions"]
        self.setAllowedWriteExtensions(allowed_write_extensions)
        
        self.__current_milli_time = lambda: int(round(time() * 1000))
        self.__tmp_dir = tempfile.TemporaryDirectory()
        
        self.__script_dir = settings["scripts_folder"]
        pass
    
    
    
    
    def initialize(self) ->None:
        self.logger.info("Module init")
        tornado.ioloop.IOLoop.current().spawn_callback(self.__analyse_target)
    
    
    
    
    def getname(self) ->Text:
        return GenericDelegate.NAME
    
    
    
    
    async def install(self):
        pass
    
    
    
    
    async def uninstall(self):
        pass
        
        
    
    
    '''
        Check out the target throughly every N seconds
    '''
    async def __analyse_target(self):
        
        pass
                
    
    
    
    
    '''
        check to see if the software is installed correctly on the system
    '''
    async def __check_installed(self):
        
        return False   
    
    
    
    
    '''
        Fetches application statistics through special r-gateway proxy webapp
    '''
    async def getTargetStats(self):
        return{}
        
        
    
    
    
    '''
    Fetches version information using the internal API
    '''
    async def __get_version(self):
        pass
    
    

    
    
    async def start_proc(self):        
        
        pass

        
        
    
    async def stop_proc(self):      
        
        pass
    
    
    
    
    async def restart_proc(self):
        pass
    
    
    
    '''
        Run diagnostics on target
    '''
    async def run_diagonistics(self):
        return {}

    
    
    
    def supported_actions(self) -> List[Action]:
        return []



    '''
    def supported_action_names(self) -> List[Text]:
        return [a.name() for a in self.supported_actions()]
    
    
    
    
    def supported_intents(self) -> List[Text]:
        return []
    
    
    
    def str_replace(self, old, new, str, caseinsentive = False):
        if caseinsentive:
            return str.replace(old, new)
        else:
            return re.sub(re.escape(old), new, str, flags=re.IGNORECASE)

    '''
    

# ---------------------------------------------


# Delegate Intents

# Delegate Actions