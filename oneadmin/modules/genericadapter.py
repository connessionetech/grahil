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

from oneadmin.core.abstracts import IntentProvider
from oneadmin.core.constants import TARGET_DELEGATE_MODULE
from oneadmin.core.grahil_types import *
from oneadmin.exceptions import TargetServiceError
from oneadmin.core.abstracts import TargetProcess
from oneadmin.core.intent import INTENT_PREFIX
from oneadmin.core.action import Action, ACTION_PREFIX, ActionResponse
from oneadmin.core.constants import TOPIC_NOTIFICATIONS, NOTIFICATIONS_WARN,\
    NOTIFICATIONS_NOTICE
from oneadmin.core.event import SimpleNotificationEvent

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




class GenericDelegate(TargetProcess):
    '''
    classdocs
    '''    
    
    NAME = "generic_delegate"
    

    def __init__(self, conf=None):
        '''
        Constructor
        '''
        super().__init__(conf["target_alias"], conf["target_process"])
        
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
        
        self.__MIN_OP_DELAY = 5000
        
        self.__last_start = self.__current_milli_time
        self.__last_stop = self.__current_milli_time
        self.__last_restart = self.__current_milli_time
        
        self.__script_dir = settings["scripts_folder"]
        pass
    
    
    
    
    def initialize(self) ->None:
        self.logger.debug("Module init")
        tornado.ioloop.IOLoop.current().spawn_callback(self.__analyse_target)



    def valid_configuration(self, conf:Dict) ->bool:
        return True 
    
    
    
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

        await asyncio.sleep(15)
        
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
        
        
        if self.__current_milli_time - self.__last_start < self.__MIN_OP_DELAY:
            raise TargetServiceError("This operation was executed very recently. Please wait some time and try again.")
            
        
        
        script_path = os.path.join(self.__script_dir, "generic-start.sh")
        
        bashCommand = "bash " + script_path + " " + self.getProcName()
        proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        await proc.wait_for_exit()
        output = proc.stdout.read()
        retcode = proc.returncode
        state = output.decode('UTF-8').strip()
        #Check and dispatch any necessary events
        
        errors = ""
        if "is already active" in state:
            errors = errors + "Process is already active" + "\n"
                    
        if len(errors) > 0:
            evt = SimpleNotificationEvent(TOPIC_NOTIFICATIONS, errors, NOTIFICATIONS_WARN)
            self.dispatchevent(evt)
        else:
            self.__last_start = self.__current_milli_time

        
        
    
    async def stop_proc(self):    
        
        if self.__current_milli_time - self.__last_stop < self.__MIN_OP_DELAY:
            raise TargetServiceError("This operation was executed very recently. Please wait some time and try again.")  
        
        script_path = os.path.join(self.__script_dir, "generic-stop.sh")
        
        bashCommand = "bash " + script_path + " " + self.getProcName()
        proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        await proc.wait_for_exit()
        output = proc.stdout.read()
        retcode = proc.returncode
        state = output.decode('UTF-8').strip()
        #Check and dispatch any necessary events
        
        errors = ""
        if "is already inactive" in state:
            errors = errors + "Process is already inactive" + "\n"
                    
        if len(errors) > 0:
            evt = SimpleNotificationEvent(TOPIC_NOTIFICATIONS, errors, NOTIFICATIONS_WARN)
            self.dispatchevent(evt)
        else:
            self.__last_stop = self.__current_milli_time
    
    
    
    
    async def restart_proc(self):
        
        if self.__current_milli_time - self.__last_restart < self.__MIN_OP_DELAY:
            raise TargetServiceError("This operation was executed very recently. Please wait some time and try again.")
        
        script_path = os.path.join(self.__script_dir, "generic-restart.sh")
        
        bashCommand = "bash " + script_path + " " + self.getProcName()
        proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        await proc.wait_for_exit()
        output = proc.stdout.read()
        retcode = proc.returncode
        state = output.decode('UTF-8').strip()
        #Check and dispatch any necessary events
        
        self.__last_restart = self.__current_milli_time
        
        pass
    
    
    
    async def is_proc_running(self):
        
        script_path = os.path.join(self.__script_dir, "generic-status.sh")
        
        bashCommand = "bash " + script_path + " " + self.getProcName()
        proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        await proc.wait_for_exit()
        output = proc.stdout.read()
        retcode = proc.returncode
        state = output.decode('UTF-8').strip()
        
        if "true" in state:
            return True
        else:
            return False
        
    
    
    
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