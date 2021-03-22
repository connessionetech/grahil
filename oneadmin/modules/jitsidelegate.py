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
import numpy as np

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



class JitsiDelegate(TargetProcess):
    '''
    classdocs
    '''    
    
    NAME = "jitsi_delegate"
    

    def __init__(self, conf=None):
        '''
        Constructor
        '''
        super().__init__("jitsi")
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
        
        
        ''' logs to monitor'''
        
        log_paths = []        
        log_root = "/var/log/"
        log_paths.append(os.path.join(log_root, "jitsi/jvb.log"))
        log_paths.append(os.path.join(log_root, "jitsi/jicofo.log"))
        log_paths.append(os.path.join(log_root, "prosody/prosody.log"))
        log_paths.append(os.path.join(log_root, "nginx/error.log"))
        self.setLogFiles(log_paths)
        
        
        ''' Allowed file extensions access'''
        
        self.setAllowedReadExtensions(['.xml', '.txt', '.ini'])
        self.setAllowedWriteExtensions(['.xml', '.ini'])
        
        self.__current_milli_time = lambda: int(round(time() * 1000))
        self.__tmp_dir = tempfile.TemporaryDirectory()
        
        self.__broken_installation = False
        self.__colibri_enabled = False
        
        self.__script_dir = settings["scripts_folder"]
        pass
    
    
    
    
    def initialize(self) ->None:
        self.logger.info("Module init")
        self.__info_api_endpoint = self.__conf["colibri_api_protocol"] + "://" + self.__conf["colibri_api_host"] + ":" + str(self.__conf["colibri_api_port"]) + "/"
        tornado.ioloop.IOLoop.current().spawn_callback(self.__analyse_target)
    
    
    
    
    def getname(self) ->Text:
        return JitsiDelegate.NAME
        
        
    
    
    '''
        Check out the target throughly every N seconds
    '''
    async def __analyse_target(self):
        
        installed = await self.__check_installed()
        version = None
        if installed:
            self.setTargetInstalled(True)
            self.__colibri_enabled = await self.__check_colibri_enabled()
            if self.__colibri_enabled:
                version = await self.__get_version()
            else:
                version = await self.__get_version_bash()
                
            self.setProcVersion(version)
        pass
                
    
    
    
    
    '''
        check to see if the software is installed correctly on the system
    '''
    async def __check_installed(self):
        
        script_path = os.path.join(self.__script_dir, "jitsi-check.sh")
        
        bashCommand = "bash " + script_path
        proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        await proc.wait_for_exit()
        output = proc.stdout.read()
        retcode = proc.returncode
        state = output.decode('UTF-8').strip()
        
        if state == "found":
            return True
        elif state == "broken":
            self.__broken_installation = False
        
        return False    
    
    
    
    '''
        Check to see if colibri is enabled
    '''    
    async def __check_colibri_enabled(self):
        
        script_path = os.path.join(self.__script_dir, "jitsi-check-colibri.sh")
        
        bashCommand = "bash " + script_path
        proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        await proc.wait_for_exit()
        output = proc.stdout.read()
        state = output.decode('UTF-8').strip()
        response = json.loads(state)
        
        if response["api"] == 1 and response["colibri_sip_stats_enabled"] == 1:
            return True
        
        return False 
    
    
    
    
    '''
        Macro function to enable colibri for stats
    ''' 
    async def do_fulfill_enable_colibri(self):
        pass
    
    
    
    
        '''
        Macro function to disable colibri for stats
    ''' 
    async def do_fulfill_disable_colibri(self):
        pass
    
    
    
    
    '''
        Fetches application statistics through special r-gateway proxy webapp
    '''
    async def getTargetStats(self):
        
        jvb_stats = await self.__get_video_bridge_stats()
        jvb_conferences = await self.__get_conferences()
        
        return{
            "jvb_stats": jvb_stats,
            "conferences": jvb_conferences 
            }
        
        pass
        
    
    
    '''
    Fetches video bridge stats using the internal API
    '''
    async def __get_video_bridge_stats(self):
        url = self.__info_api_endpoint + "colibri/stats"
        http_client = AsyncHTTPClient()
        response = await http_client.fetch(url, method="GET", headers=None)
        self.logger.debug("response = %s", str(response))
        if response.code == 200:
            result = str(response.body, 'utf-8')
            return result
        
        raise HTTPError("Unable to make request to url " + url)
    
    
    
    
    '''
    Fetches list of conferences using the internal API
    '''
    async def __get_conferences(self):
        url = self.__info_api_endpoint + "colibri/conferences"
        http_client = AsyncHTTPClient()
        response = await http_client.fetch(url, method="GET", headers=None)
        self.logger.debug("response = %s", str(response))
        if response.code == 200:
            result = str(response.body, 'utf-8')
            return result
        
        raise HTTPError("Unable to make request to url " + url)
    
    
    
    
    '''
    Fetches version information using the internal API
    '''
    async def __get_version(self):
        url = self.__info_api_endpoint + "about/version"
        
        http_client = AsyncHTTPClient()
        response = await http_client.fetch(url, method="GET", headers=None)
        self.logger.debug("response = %s", str(response))
        if response.code == 200:
            result = str(response.body, 'utf-8')
            result_data = json.loads(result)
                        
            if "version" in result_data:
                return result_data["version"]
            else:
                raise HTTPError("Version information could not be obtained")
            
        
        raise HTTPError("Unable to make request to url " + url)
    
    
    
    
    '''
    Fetches version information using the internal API
    '''
    async def __get_version_bash(self):
        script_path = os.path.join(self.__script_dir, "jitsi-version.sh")
        
        bashCommand = "bash " + script_path
        proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        await proc.wait_for_exit()
        output = proc.stdout.read()
        version = output.decode('UTF-8').strip()
        version = self.str_replace("Version:", "", version, False).strip()
        return version
    
    

    
    
    async def start_proc(self):        
        script_path = os.path.join(self.__script_dir, "jitsi-start.sh")
        
        bashCommand = "bash " + script_path
        proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        await proc.wait_for_exit()
        output = proc.stdout.read()
        retcode = proc.returncode
        state = output.decode('UTF-8').strip()
        #Check and dispatch any necessary events
        
        errors = ""
        if "prosody is already active" in state:
            errors = errors + "prosody is already active" + "\n"
        if "jicofo is already active" in state:
            errors = errors + "jicofo is already active" + "\n"
        if "jitsi-videobridge2 is already active" in state:
            errors = errors + "jitsi-videobridge2 is already active" + "\n"
        if "nginx is already active" in state:
            errors = errors + "nginx is already active" + "\n"
        
        if len(errors) > 0:
            evt = SimpleTextNotificationEvent(TOPIC_NOTIFICATIONS, errors, NOTIFICATIONS_WARN)
            self.dispatchevent(evt) 
        
        
        pass

        
        
    
    async def stop_proc(self):      
        script_path = os.path.join(self.__script_dir, "jitsi-stop.sh")
        
        bashCommand = "bash " + script_path
        proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        await proc.wait_for_exit()
        output = proc.stdout.read()
        retcode = proc.returncode
        state = output.decode('UTF-8').strip()
        #Check and dispatch any necessary events
        
        errors = ""
        if "prosody is already inactive" in state:
            errors = errors + "prosody is already inactive" + "\n"
        if "jicofo is already inactive" in state:
            errors = errors + "jicofo is already inactive" + "\n"
        if "jitsi-videobridge2 is already inactive" in state:
            errors = errors + "jitsi-videobridge2 is already inactive" + "\n"
        if "nginx is already inactive" in state:
            errors = errors + "nginx is already inactive" + "\n"
        
        if len(errors) > 0:
            evt = SimpleTextNotificationEvent(TOPIC_NOTIFICATIONS, errors, NOTIFICATIONS_WARN)
            self.dispatchevent(evt) 
        
        
        pass
    
    
    
    
    async def restart_proc(self):
        script_path = os.path.join(self.__script_dir, "jitsi-restart.sh")
        
        bashCommand = "bash " + script_path
        proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        await proc.wait_for_exit()
        output = proc.stdout.read()
        retcode = proc.returncode
        state = output.decode('UTF-8').strip()
        
        errors = ""
        if "prosody is already inactive" in state:
            errors = errors + "prosody is already inactive" + "\n"
        if "jicofo is already inactive" in state:
            errors = errors + "jicofo is already inactive" + "\n"
        if "jitsi-videobridge2 is already inactive" in state:
            errors = errors + "jitsi-videobridge2 is already inactive" + "\n"
        if "nginx is already inactive" in state:
            errors = errors + "nginx is already inactive" + "\n"
        
        if len(errors) > 0:
            evt = SimpleTextNotificationEvent(TOPIC_NOTIFICATIONS, errors, NOTIFICATIONS_NOTICE)
            self.dispatchevent(evt) 
    
    
    
    '''
        Run diagnostics on target
    '''
    async def run_diagonistics(self):
        return {}
        pass
    
            

    
    async def do_fulfill_test(self, name:str = "output.avi", path:str = None):
        try:
            evt = buildDataNotificationEvent(data={"subject" : "Target", "concern": "TargetCameraDevice", "content":{"streaming":self.__streaming}}, topic="/grahil_events", msg="Target camera has stopped streaming")
            await self.eventcallback(evt)           
            
        except Exception as e:
            raise TargetServiceError("Unable to capture video " + str(e))   
    
    
  
    '''
        Sample custom method
    '''
    def do_fulfill_hello(self, params):
        return " world"
    
    
    
    def supported_actions(self) -> List[Action]:
        return []




    def supported_action_names(self) -> List[Text]:
        return [a.name() for a in self.supported_actions()]
    
    
    
    
    def supported_intents(self) -> List[Text]:
        return []
    
    
    
    def str_replace(self, old, new, str, caseinsentive = False):
        if caseinsentive:
            return str.replace(old, new)
        else:
            return re.sub(re.escape(old), new, str, flags=re.IGNORECASE)
    
    

# ---------------------------------------------


# Delegate Intents

# Delegate Actions