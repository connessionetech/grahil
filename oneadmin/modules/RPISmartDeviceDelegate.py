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
import tornado
import os
from builtins import int, str
from oneadmin.exceptions import TargetServiceError
from tornado.ioloop import IOLoop
import tempfile
import time
import logging
import sys
from oneadmin.abstracts import TargetProcess
from tornado.concurrent import asyncio
from tornado.process import Subprocess
import signal
import subprocess


import RPi.GPIO as GPIO
import Adafruit_DHT


  

class TargetDelegate(TargetProcess):
    '''
    classdocs
    '''    
    
    SERVICE_PATH = None
    SERVO1 = 17
    SERVO2 = 27
    DHT_PIN = 4
    DHT_SENSOR = Adafruit_DHT.DHT22
    
    

    def __init__(self, root=None, params=None):
        '''
        Constructor
        '''
        super().__init__('rpi', root, TargetDelegate.SERVICE_PATH)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setPidProcName(None)
        
        
        log_paths = []
        # log_paths.append(os.path.join(root, "log/red5.log"))
        self.setLogFiles(log_paths)
        
        self.setAllowedReadExtensions(['.xml', '.txt', '.ini'])
        self.setAllowedWriteExtensions(['.xml', '.ini'])
        
        self.__servo__angle_v = 0;
        self.__servo__angle_h = 0;
        
        self.__max_stream_time = 30
        
        self.__current_milli_time = lambda: int(round(time() * 1000))
        
        self.__tmp_dir = tempfile.TemporaryDirectory()
        
        self.__streaming_process = None
        self.__streaming = None
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__init_rpi_hardware)
        #tornado.ioloop.IOLoop.current().spawn_callback(self.do_fulfill_start_streaming)
        pass
    
    
    
    '''
    Initializes the RPI pins 
    Ref https://www.instructables.com/Servo-Motor-Control-With-Raspberry-Pi/
    '''
    async def __init_rpi_hardware(self):
        GPIO.setmode(GPIO.BCM)
        
        GPIO.setup(TargetDelegate.SERVO1, GPIO.OUT)
        GPIO.setup(TargetDelegate.SERVO2, GPIO.OUT)
                
        self.__pwm = GPIO.PWM(TargetDelegate.SERVO1, 50)
        self.__pwm_2 = GPIO.PWM(TargetDelegate.SERVO2, 50)
        
        self.__pwm.start(0)
        self.__pwm_2.start(0)
        
        await IOLoop.current().run_in_executor(None, self.__set_horizontal_angle, 45)
        await IOLoop.current().run_in_executor(None, self.__set_vertical_angle, 0)
        
        pass
    
    
    
    '''
    Set angle for servo
    Ref https://www.instructables.com/Servo-Motor-Control-With-Raspberry-Pi/
    '''
    def __set_horizontal_angle(self, angle):
        
        self.__servo__angle_v = angle
        self.logger.info(" => " + str(angle))
        duty = float(angle)/10 + 2.5
        GPIO.output(TargetDelegate.SERVO1, True)
        self.__pwm.ChangeDutyCycle(duty)
        time.sleep(1)
        GPIO.output(TargetDelegate.SERVO1, False)
        self.__pwm.ChangeDutyCycle(0)
        pass
    
    
    
    
    def __set_vertical_angle(self, angle):
        
        self.__servo__angle_h = angle
        self.logger.info(" => " + str(angle))
        duty = float(angle)/10 + 2.5
        GPIO.output(TargetDelegate.SERVO2, True)
        self.__pwm_2.ChangeDutyCycle(duty)
        time.sleep(1)
        GPIO.output(TargetDelegate.SERVO2, False)
        self.__pwm_2.ChangeDutyCycle(0)
        pass
    
    
    
    def __gpio_start(self):
        self.__pwm.start(1)
        pass
    
    
    
    def __gpio_done(self):
        self.__pwm.stop()
        # GPIO.cleanup()
        pass
    
    
    

    def __demo(self):
        #duty = angle / 18 + 2
        #RPi.GPIO.output(3, True)
        self.__gpio_start()
        self.__set_horizontal_angle(20)
        time.sleep(1)
        self.__set_horizontal_angle(40)
        time.sleep(1)
        self.__set_horizontal_angle(20)
        time.sleep(1)
        self.__set_horizontal_angle(40)
        time.sleep(1)
        self.__set_horizontal_angle(20)
        time.sleep(1)
        self.__set_horizontal_angle(40)
        time.sleep(1)
        self.__set_horizontal_angle(20)
        time.sleep(1)
        self.__set_horizontal_angle(40)
        time.sleep(1)
        self.__set_horizontal_angle(20)
        time.sleep(1)
        self.__set_horizontal_angle(40)
        time.sleep(1)
        self.__set_horizontal_angle(20)
        time.sleep(1)
        self.__set_horizontal_angle(40)
        
        self.__gpio_done()
        
    
    
    
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
    
    
    
    
    async def do_fulfill_start_streaming(self):
        
        try:
            cmd = ["/usr/bin/ffmpeg", "-threads", "2", "-f", "lavfi", "-thread_queue_size", "512", "-i", "anullsrc=r16000:cl=stereo", "-re", "-thread_queue_size", "512", "-i", "/dev/video0", "-c:a", "aac", "-strict", "experimental", "-b:a", "128k", "-ar", "44100", "-s", "640x480", "-vcodec", "libx264", "-x264-params", "keyint=120:scenecut=0", "-vb", "200k", "-pix_fmt", "yuv420p", "-f", "flv", "rtmp://a.rtmp.youtube.com/live2/jg9q-hfeg-t7g2-x6bz-8f3c"]
            self.__streaming_process = Subprocess(cmd, stdout=Subprocess.STREAM, stderr=subprocess.STDOUT, universal_newlines=True)
            self.__streaming_process.set_exit_callback(self.__ffmpeg_closed)
            IOLoop.instance().add_timeout(time.time() + self.__max_stream_time, self.do_fulfill_stop_streaming)
            
            while True:
                line = await self.__streaming_process.stdout.read_until_regex(b"\r\n|\r|\n")
                line_str:str = line.decode("utf-8") 
                self.logger.info(line_str)
                if "frame=" in line_str:
                    self.__streaming = True
                    pass            
        except Exception as e:
            self.__streaming = False    
        pass
    
    
    
    def __ffmpeg_closed(self, param=None):
        self.logger.debug("closed")
        self.__streaming = False 
        pass
    
    
    
    async def do_fulfill_stop_streaming(self):
        
        try:
            if self.__streaming == True:
                pid = self.__streaming_process.pid
                os.kill(pid, signal.SIGTERM)
        except Exception as e:
            self.logger.error("Error terminating process gracefully %s", str(e))   
        finally:
            self.__streaming = False
    
    
    
    
    async def do_fulfill_get_humidity_temperature(self):
        
        try:
            humidity, temperature = Adafruit_DHT.read_retry(TargetDelegate.DHT_SENSOR, TargetDelegate.DHT_PIN)
            if humidity is not None and temperature is not None:
                return {
                "temperature": str(round(temperature, 1)) + " deg C",
                "humidity" : str(round(humidity, 1)) + " %",
                }
            else:
                raise TargetServiceError("Unable to get temperature and humidity info")
        except Exception as e:
                raise TargetServiceError("Error getting temperature and humidity info " + str(e))
    
    
    
    
    async def do_fulfill_turn_left(self):
        
        try:
            self.logger.info("Turn left")
            __servo__angle = self.__servo__angle_v - 11 if self.__servo__angle_v - 11 >= 0 else 0
            await IOLoop.current().run_in_executor(None, self.__set_horizontal_angle, __servo__angle)
        except Exception as e:
            raise TargetServiceError("Unable to set angle " + str(e))
        
        
    
    
    
    async def do_fulfill_turn_right(self):
        
        try:
            self.logger.info("Turn right")
            __servo__angle = self.__servo__angle_v + 11 if self.__servo__angle_v + 11 <= 90 else 90
            await IOLoop.current().run_in_executor(None, self.__set_horizontal_angle, __servo__angle)
        except Exception as e:
            raise TargetServiceError("Unable to set angle " + str(e))
        
        
        
    
    async def do_fulfill_turn_down(self):
        
        try:
            self.logger.info("Turn left")
            __servo__angle = self.__servo__angle_h - 5 if self.__servo__angle_h - 5 >= 0 else 0
            await IOLoop.current().run_in_executor(None, self.__set_vertical_angle, __servo__angle)
        except Exception as e:
            raise TargetServiceError("Unable to set angle " + str(e))
        
        
    
    
    async def do_fulfill_turn_up(self):
        
        try:
            self.logger.info("Turn right")
            __servo__angle = self.__servo__angle_h + 5 if self.__servo__angle_h + 5 <= 90 else 90
            await IOLoop.current().run_in_executor(None, self.__set_vertical_angle, __servo__angle)
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
        
        
        
    async def do_fulfill_test(self, name:str = "output.avi", path:str = None):
        try:
            self.logger.info("test")
        except Exception as e:
            raise TargetServiceError("Unable to capture video " + str(e))   
        
        
    
    
    def __cv_capture_video(self, file:str, maxduration:int = 10000):
        
        #Capture video from webcam
        vid_capture = cv2.VideoCapture(0)        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        output = cv2.VideoWriter(file,fourcc, 15.0, (640,480))
        
        start_time = int(round(time.time() * 1000))
             
        while(True):
            ret,frame = vid_capture.read()
            output.write(frame)
            now = int(round(time.time() * 1000))
            if now - start_time >= maxduration:
                break
            
        # close the already opened camera
        vid_capture.release()
        # close the already opened file
        output.release()
        
        root_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        
        if os.path.exists(file):
            return {
                "meta": {
                    "type": "video",
                    "duration": maxduration/1000,
                    "width": 640,
                    "height": 480,
                    "thumb" : root_path + os.path.sep + "assets/video.png" 
                },
                    "data" : file
            }
            
            
                            
        raise FileNotFoundError("Could not locate recording or recording failed")
    
    
    
    async def do_fulfill_capture_image(self, name:str = "image.jpg", path:str = None):
        try:
            
            if path != None:
                name = (path + name) if path.endswith("/") else (path + os.path.sep + name)
            else:
                name = '/home/pi/grahil-py'+ os.path.sep + name
            
            return  await IOLoop.current().run_in_executor(
                    None,
                    self.__cv_capture_image, name
                    )
        except Exception as e:
            raise TargetServiceError("Unable to capture image " + str(e))
                
    
   
    
    def __cv_capture_image(self, file:str):
        
            videoCaptureObject = cv2.VideoCapture(0)
            i = 0
            n = 6
            while(i<n):
                ret,frame = videoCaptureObject.read()
                time.sleep(1)
                i = i+1
                if i<(n-1):
                    continue
                
                cv2.imwrite(file,frame)
                                
            
            # Release everything if job is finished
            videoCaptureObject.release()
            cv2.destroyAllWindows()
            
            if os.path.exists(file):
                return {
                    "meta": {
                        "type": "image"            
                    },
                        "data" : file
                 }
            
            raise FileNotFoundError("Could not locate recording or recording failed")

    
    
    '''
        Sample custom method
    '''
    def do_fulfill_hello(self, params):
        return " world"