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
from builtins import int, str
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
from tornado.ioloop import IOLoop
import tempfile
from numpy.distutils.fcompiler import none

# import RPi.GPIO as GPIO

  

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
        
        self.__servo__angle = 0;
        self.__current_milli_time = lambda: int(round(time() * 1000))
        
        self.__tmp_dir = tempfile.TemporaryDirectory()
        

        # tornado.ioloop.IOLoop.current().spawn_callback(self.__init_rpi_hardware)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__analyse_target)
        pass
    
    
    
    '''
    Initializes the RPI pins 
    Ref https://www.instructables.com/Servo-Motor-Control-With-Raspberry-Pi/
    '''
    def __init_rpi_hardware(self):
        RPi.GPIO.setmode(GPIO.BOARD)
        RPi.GPIO.setup(3, GPIO.OUT)
        self.__pwm=GPIO.PWM(3, 50)
        self.__servo__angle = 0
        self.__pwm.start(self.__servo__angle)
        pass
    
    
    
    '''
    Set angle for servo
    Ref https://www.instructables.com/Servo-Motor-Control-With-Raspberry-Pi/
    '''
    def __set_angle(self, angle):
        duty = angle / 18 + 2
        RPi.GPIO.output(3, True)
        self.__pwm.ChangeDutyCycle(duty)
        sleep(1)
        RPi.GPIO.output(3, False)
        self.__pwm.ChangeDutyCycle(0)
        
    
    
    
    
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
    
    
    
    async def do_fulfill_turn_left(self):
        
        try:
            __servo__angle = self.__servo__angle - 1 if self.__servo__angle - 1 >= 0 else 0
            await IOLoop.current().run_in_executor(None, self.__set_angle, __servo__angle)
            self.__pwm.stop()
            RPi.GPIO.cleanup()
        except Exception as e:
            raise TargetServiceError("Unable to set angle " + str(e))
        
        
    
    async def do_fulfill_turn_right(self):
        
        try:
            __servo__angle = self.__servo__angle + 1 if self.__servo__angle + 1 <= 180 else 180
            await IOLoop.current().run_in_executor(None, self.__set_angle, __servo__angle)
            self.__pwm.stop()
            RPi.GPIO.cleanup()
        except Exception as e:
            raise TargetServiceError("Unable to set angle " + str(e))
        
        

    
    async def do_fulfill_capture_video(self, name:str = "output.avi", path:str = None):
        
        try:
            if path != None:
                name = (path + name) if path.endswith("/") else (path + os.path.sep + name)
            else:
                name = self.__tmp_dir.name + os.path.sep + name
                
            return await IOLoop.current().run_in_executor(
                None, 
                self.__cv_capture_video, name
                )
        except Exception as e:
            raise TargetServiceError("Unable to capture video " + str(e))
        
        
    
    
    def __cv_capture_video(self, file:str, maxduration:int = 10000):
        
            cap = cv2.VideoCapture(0)
            
            start_time = int(round(time() * 1000))
            
            # Define the codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(file,fourcc, 20.0, (640,480))
            
            while(cap.isOpened()):
                ret, frame = cap.read()
                if ret==True:
                    frame = cv2.flip(frame,0)
            
                    # write the flipped frame
                    out.write(frame)
            
                    cv2.imshow('frame',frame)
                    
                    # 10 seconds recording only
                    if int(round(time() * 1000)) - start_time >= maxduration:
                        break
                else:
                    break
            
            # Release everything if job is finished
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            
            if os.path.exists(file):
                return file
            return none
    
    
    
    async def do_fulfill_capture_image(self, name:str = "image.jpg", path:str = None):
        try:
            
            if path != None:
                name = (path + name) if path.endswith("/") else (path + os.path.sep + name)
            else:
                name = "/home" + os.path.sep + name
            
            return  await IOLoop.current().run_in_executor(
                    None,
                    self.__cv_capture_image, name
                    )
        except Exception as e:
            raise TargetServiceError("Unable to capture image " + str(e))
                
    
   
    
    def __cv_capture_image(self, file:str):
        
            videoCaptureObject = cv2.VideoCapture(0)
            result = True
            while(result):
                ret,frame = videoCaptureObject.read()
                cv2.imwrite(file,frame)
                result = False
            
            # Release everything if job is finished
            videoCaptureObject.release()
            cv2.destroyAllWindows()
            
            if os.path.exists(file):
                return file
            return none

    
    
    '''
        Sample custom method
    '''
    def do_fulfill_hello(self, params):
        return command + " world"