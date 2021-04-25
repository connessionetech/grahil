'''
Created on 05-Mar-2021

@author: root
'''
from oneadmin.core.abstracts import IModule
from oneadmin.responsebuilder import formatSuccessBotResponse, formatSuccessResponse

from concurrent.futures.thread import ThreadPoolExecutor
from tornado import ioloop

import tornado
import time
import logging
import datetime
from typing import Text
import json




class ParallelismDemo(IModule):
    '''
    classdocs
    '''
    
    NAME = "parallelism_sample_module"
    
    thread_pool = ThreadPoolExecutor(5)



    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
    
    
    
        
    def getname(self) ->Text:
        return ParallelismDemo.NAME    
        

    
    def initialize(self) ->None:
        self.logger.info("Module init")
        tornado.ioloop.IOLoop.current().spawn_callback(self.__spinthreads)
        
        
    
    def __spinthreads(self):
        for x in range(5):
            tornado.ioloop.IOLoop.current().run_in_executor(ParallelismDemo.thread_pool, self.blocking_sync_function, x)
    
    
    
    def blocking_sync_function(self, index):
        self.logger.debug("\nregular_function " + str(index) + " " +  str(datetime.datetime.now()))
        time.sleep(2)

        