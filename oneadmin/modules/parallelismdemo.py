'''
Created on 05-Mar-2021

@author: root
'''
from oneadmin.abstracts import IModule

from concurrent.futures.thread import ThreadPoolExecutor
from tornado import ioloop

import tornado
import time
import logging
import datetime



class ParallelismDemo(IModule):
    '''
    classdocs
    '''
    
    thread_pool = ThreadPoolExecutor(5)



    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
        
        

    def initialize(self) ->None:
        self.logger.info("Module init")
        tornado.ioloop.IOLoop.current().spawn_callback(self.__spinthreads)
        
        
    
    def __spinthreads(self):
        for x in range(5):
            tornado.ioloop.IOLoop.current().run_in_executor(ParallelismDemo.thread_pool, self.blocking_sync_function, x)
    
    
    def blocking_sync_function(self, index):
        self.logger.info("\nregular_function " + str(index) + " " +  str(datetime.datetime.now()))
        time.sleep(2)
        