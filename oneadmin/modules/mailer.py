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
from oneadmin.abstracts import IMailer

from builtins import str
from email.message import EmailMessage
from typing import Text
import aiosmtplib


class SMTPMailer(IMailer):
    '''
    classdocs
    '''

    def __init__(self, conf:dict):
        '''
        Constructor
        '''
        super().__init__()
        self.__conf = conf
        pass
    
    
    
    async def send_mail(self, subject:Text, body:Text) ->None:
        
        if "tls" in self.__conf and  self.__conf["tls"] == True:
            await self.send_mail_tls(subject, body)
        else:
            message = EmailMessage()
            message["From"] = self.__conf["default_from"]
            message["To"] = self.__conf["default_to"]
            message["Subject"] = subject
            message.set_content(body)
            await aiosmtplib.send(message, hostname=self.__conf["hostname"], port=self.__conf["port"])
        pass
    
    
    
    async def send_mail_tls(self, subject:Text, body:Text) ->None:
        
        message = EmailMessage()
        message["From"] = self.__conf["default_from"]
        message["To"] = self.__conf["default_to"]
        message["Subject"] = subject
        message.set_content(body)
        await aiosmtplib.send(message, hostname=self.__conf["hostname"], port=self.__conf["port"], username=self.__conf["default_username"], password=self.__conf["default_password"], use_tls=True)
        