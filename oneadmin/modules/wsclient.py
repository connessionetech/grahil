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


from tornado.websocket import websocket_connect
from oneadmin.abstracts import IModule, IntentProvider


import logging
import sys
import tornado
import datetime
import asyncio


class WebSocketClient(IModule):
    '''
    classdocs
    '''


    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__connection = None
        self.__connected = False
        self.__url = None
        
        
    
    
    '''
        creates connection to remote endpoint
    '''
    async def connect(self, url, reconnect = False):
        if(self.__connected == False):
            
            try:
                self.__connection = await websocket_connect(url, connect_timeout=6000,
                      ping_interval=15000, ping_timeout=3000)
            except Exception as e:
                self.logger.error("connection error. could not connect to remote endpoint " + url)
            else:
                self.logger.info("connected to remote endpoint " + url)
                self.__connected = True
                
                '''
                if reconnect == True:
                    tornado.ioloop.IOLoop.current().spawn_callback(self.__tail, name)
                '''
                
                self.__read_message()
                
    
    
    
    '''
        Special method to enforce reconnection to remote endpoint
    '''
    async def __reconnect(self):
        if self.__connected is None and self.__url is not None:
            await self.connect(self.__url)
        
    
    
    
    '''
        Read message from open websocket channel
    '''
    async def __read_message(self):
        while True:
            msg = await self.__connection.read_message()
            if msg is None:
                self.logger.info("connection to remote endpoint " + self.__url +"closed");
                self.__connection = None
                self.__connected = False
                break
    
    
    
    
    '''
        Write message in open websocket channel
    '''
    async def write_message(self, message, binary = False):
        if(self.__connected == True):
            self.__connection.write_message(message, binary);
                
    
    
    
    '''
        Closes connection
    '''
    async def closeConnection(self, code = None, reason = None):
        if(self.__connected == True):
            self.__connection.close(code, reason)
            self.__connection = None
            self.__connected = False
        
        