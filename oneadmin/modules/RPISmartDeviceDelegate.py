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

import cv2
from oneadmin.target.TargetProcess import TargetProcess
from pathlib import Path
from jproperties import Properties
from tornado.process import Subprocess, CalledProcessError
import tornado
import os
import re
from builtins import int
from datetime import datetime
import sys
from oneadmin.exceptions import TargetServiceError
from tornado.concurrent import asyncio
from aiofile.aio import AIOFile
import subprocess
from oneadmin.responsebuilder import buildDataNotificationEvent,\
    buildDataEvent
from tornado.httpclient import AsyncHTTPClient
from tornado.httputil import HTTPHeaders
import hashlib
import time
import urllib
import json
from numpy.distutils.fcompiler import none
from tornado.ioloop import IOLoop

class TargetDelegate(TargetProcess):
    '''
    classdocs
    '''    
    
    SERVICE_PATH = None

    def __init__(self, root=None, params=None):
        '''
        Constructor
        '''
        super().__init__('rpi', root, TargetDelegate.SERVICE_PATH)
        
        self.setPidProcName(None)  
        
        
        log_paths = []
        # log_paths.append(os.path.join(root, "log/red5.log"))
        self.setLogFiles(log_paths)
        
        self.setAllowedReadExtensions(['.xml', '.txt', '.ini'])
        self.setAllowedWriteExtensions(['.xml', '.ini'])
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__analyse_target)
        pass
    
    
    
    '''
        Check out the target throughly every N seconds
     '''
    async def __analyse_target(self):
        pass
    
    
    '''
        Fetches application statistics through special r-gateway proxy webapp
    '''
    async def getTargetStats(self):
        return {}
        pass
    
    

    
    
    async def start_proc(self):        
        TargetServiceError("Operation not supported")
        pass

        
        
    async def stop_proc(self):      
        TargetServiceError("Operation not supported")
        pass
    
    
    '''
        Run diagnostics on target
    '''
    async def run_diagonistics(self):
        return {}
        pass


    
    async def do_fulfill_capture_video(self, name = "output", path = None):
        
        try:
            await IOLoop.current().run_in_executor(None, self.__cv_capture_video, name, path)
        except Exception as e:
            raise TargetServiceError("Unable to capture image " + str(e))
        
        
    
    
    def __cv_capture_video(self, name):
        
        try:
            cap = cv2.VideoCapture(0)
            
            # Define the codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(name + '.avi',fourcc, 20.0, (640,480))
            
            while(cap.isOpened()):
                ret, frame = cap.read()
                if ret==True:
                    frame = cv2.flip(frame,0)
            
                    # write the flipped frame
                    out.write(frame)
            
                    cv2.imshow('frame',frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    break
            
            # Release everything if job is finished
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            
            asyncio.sleep(.2)
            
            # Verify image
            
        except Exception as e:
            raise TargetServiceError("Unable to capture video " + str(e))
            pass
    
    
    
    async def do_fulfill_capture_image(self, img = "image.jpg", path = None):
        try:
            await IOLoop.current().run_in_executor(None, self.__cv_capture_image, img, path)
        except Exception as e:
            raise TargetServiceError("Unable to capture image " + str(e))
                
    
   
    def __cv_capture_image(self, name):
        
        try:
            videoCaptureObject = cv2.VideoCapture(0)
            result = True
            while(result):
            ret,frame = videoCaptureObject.read()
            cv2.imwrite(name,frame)
            result = False
            videoCaptureObject.release()
            cv2.destroyAllWindows()
            
        except Exception as e:
            raise TargetServiceError("Unable to capture image " + str(e))
            pass

    
    
    '''
        Sample custom method
    '''
    def do_fulfill_hello(self, command, params):
        return command + " world"