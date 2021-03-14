'''
Created on 14-Mar-2021

@author: root
'''


from oneadmin.abstracts import IModule
from oneadmin.responsebuilder import formatSuccessBotResponse, formatSuccessResponse

from tornado import ioloop
from tornado.web import url

import tornado
import logging
from typing import Text, List
import json



class ApiHostModule(IModule):
    '''
    classdocs
    '''
    
    NAME = "api_host_module"



    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
    
    
        
    def getname(self) ->Text:
        return ApiHostModule.NAME    
        

    
    def initialize(self) ->None:
        self.logger.info("Module init")
        
        
    
    

    def get_url_patterns(self)->List:
        return [ url(r"/moduleapi/", SampleHandler) ]






'''
Sample  handler
'''
class SampleHandler(tornado.web.RequestHandler):
    
    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)    
        pass
    

    def get(self):
        self.logger.info("sample path")
        self.write(json.dumps(formatSuccessResponse("Hello world")))
        self.finish()
        