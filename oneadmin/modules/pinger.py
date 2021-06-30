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

from oneadmin.core.abstracts import IModule
from oneadmin.core.event import EventType, PingEvent, is_valid_event
from oneadmin.core.constants import TOPIC_PING


import logging
import tornado
import datetime
import asyncio
from typing import Dict, Text



class Pinger(IModule):
    
    
    NAME = "pinger"
    
    
    def __init__(self, conf):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
        pass
    
    
    
    def getname(self) ->Text:
        return Pinger.NAME
    
    
    
    def initialize(self) ->None:
        self.logger.debug("Module init")
        self.start()
        pass


    def valid_configuration(self, conf:Dict) ->bool:
        return True
    
    
    async def __generatePing(self):
        while True:
            await self.dispatchevent(PingEvent(topic=TOPIC_PING))
                        
            if self.__conf["ping_interval_seconds"] is not None:
                await asyncio.sleep(self.__conf["ping_interval_seconds"])
        pass
    
    
    def start(self):  
        if self.__conf is not None:      
            tornado.ioloop.IOLoop.current().spawn_callback(self.__generatePing)
        pass