'''
Created on 20-Dec-2020

@author: root
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
        