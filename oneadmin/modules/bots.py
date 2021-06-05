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

from oneadmin.responsebuilder import formatSuccessBotResponse, formatErrorBotResponse
from oneadmin.core.abstracts import ServiceBot, IEventHandler, IntentProvider, IClientChannel
from oneadmin.core.utilities import is_notification_event, is_data_notification_event, isVideo, isImage
from oneadmin.exceptions import RPCError
from oneadmin.core.intent import INTENT_GET_SOFTWARE_VERSION_NAME
from oneadmin.exceptions import *
from oneadmin.version import __version__

import logging
import tornado
import json
import sys
import uuid
from aiogram.utils import exceptions
from tornado.platform import asyncio
from aiogram.types.input_file import InputFile
from aiogram import Bot, Dispatcher, types
from tornado.queues import Queue
from typing import Text




class TelegramBot(ServiceBot, IEventHandler, IntentProvider, IClientChannel):
    
    NAME = "service_bot"
    
    '''
    classdocs
    '''

    def __init__(self, conf:dict):
        '''
        Constructor
        '''
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__connected = False
        self.__supports_webhook = False
        self.__uid = None
        self.__conf = conf
        self.__requests = {}
        self.__mgsqueue = Queue()
        self.__eventsqueue = Queue()
        self.id = str(uuid.uuid4())
        self.__bot_master = None
        
    
    
    def getname(self) ->Text:
        return TelegramBot.NAME
    
        
    
    
    def initialize(self) ->None:
        super().initialize()
        self.initialize_interpreter()
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__notifyHandler)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__event_processor)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__activate_bot)
    
    
    
    def initialize_interpreter(self):
        
        try:
            self.logger.info("preparing interpreter")
            
            interpreter_conf = self.__conf["interpreter"]
            interpreter_module_name = interpreter_conf["module"]
            interpreter_klass_name = interpreter_conf["klass"]
            
            interpreter_module = __import__(interpreter_module_name, fromlist=[interpreter_klass_name])
            interpreter_klass = getattr(interpreter_module, interpreter_klass_name)
            
            interpreter_instance = interpreter_klass(interpreter_conf["conf"])
            
            self.__nlp_engine = interpreter_instance
        
        except ImportError as be:
            
            self.__nlp_engine = None
            self.logger.warn("Interpreter was not found and will not be loaded")
    
    
    
    
    async def __activate_bot(self):
    
        try:
            self.__bot = Bot(token=self.__conf['token'])
            self.__disp = Dispatcher(self.__bot)
            
            self.__disp.register_message_handler(self.start_handler, commands={"start", "restart"})
            self.__disp.register_message_handler(self.handleMessages)
            
            
            ''' Assign master user if specified '''
            if "master_user_id" in self.__conf:
                if self.__conf["master_user_id"] != "":
                    self.__bot_master = self.__conf["master_user_id"]
                    self.logger.debug(f"Bot master ID %s", str(self.__bot_master))
                    #version = await self.__action_dispatcher.handle_request_direct(self, INTENT_GET_SOFTWARE_VERSION_NAME, {})
                    await self.send_message(self.__bot_master, "Bot version:"+__version__+"\nI am listening..")                
                    
            
            '''    
            self.__disp.register_message_handler(self.text_startswith_handler, text_startswith=['prefix1', 'prefix2'])
            '''
            
                    
            await self.__read_messages()
            #me = await self.__bot.get_me()
            #self.__uid =  me.username
            #self.logger.debug(f"🤖 Hello, I'm {me.first_name}.\nHave a nice Day!")
            
            
        except Exception as e:
            self.logger.error("bot init error " + str(e))
        '''finally:
            await bot.close()'''
            
    
    
    '''
        Receives event notifications
    '''        
    async def notifyEvent(self, event):
        self.logger.debug(json.dumps(event))
        if is_data_notification_event(event) or is_notification_event(event):
            await self.__eventsqueue.put(event)        
        pass  
    
            
            
    async def handleBotRPC(self, response, message: types.Message):
        
        wshandler = self
        
        local_request_id = message.message_id
        action = response["action"]
        intent = response["intent"]
        post_response = response["text"]
        args = action["parameters"]
        pre_response = action["pre_response"]
        args["handler"] = wshandler 
        
        try:
            await message.answer(pre_response)
            requestid = await self.notifyintent(intent, args)
            self.__requests[requestid] = {"local_request_id": local_request_id, "handler": wshandler, "response": response, "subject": message}
        
        except:
            
            if requestid in self.__requests:
                del self.__requests[requestid]
                
            raise RPCError("Failed to invoke method." + str(sys.exc_info()[0]))
        pass   
    
    
    
    
    
    async def send_message(self, user_id: int, response_text: str, response_data:object = None, disable_notification: bool = False) -> bool:
        """
        Safe messages sender
        :param user_id:
        :param text:
        :param disable_notification:
        :return:
        """
        try:
            
            if response_data == None:
                response_data = ""
                await self.__bot.send_message(user_id, response_text + "\n\r\n\r" + response_data, disable_notification=disable_notification)
            
            elif isImage(response_data):
                
                path = response_data["data"]                
                img = InputFile(path, "Snapshot")
                await self.__bot.send_photo(user_id, img, response_text)
                
                            
            elif isVideo(response_data): 
                path = response_data["data"]
                duration = None
                width = None;
                height = None;
                thumb = None
                vid = InputFile(path, "Video")
                
                if 'meta' in response_data:
                    duration = response_data['meta']['duration'] if 'duration' in response_data['meta'] else None
                    width = response_data['meta']['width'] if 'width' in response_data['meta'] else None
                    height = response_data['meta']['height'] if 'height' in response_data['meta'] else None
                    thumb = response_data['meta']['thumb'] if 'thumb' in response_data['meta'] else None
                
                await self.__bot.send_video(user_id, vid, duration, width, height, InputFile(thumb), "video")
                
            
            elif isinstance(response_data,dict):
                response_data = json.dumps(response_data) 
                await self.__bot.send_message(user_id, response_text + "\n\r\n\r" + response_data, disable_notification=disable_notification)
            
            else:
                await self.__bot.send_message(user_id, response_text + "\n\r\n\r" + response_data, disable_notification=disable_notification)
                
        except exceptions.BotBlocked:
            self.logger.error(f"Target [ID:{user_id}]: blocked by user")
        except exceptions.ChatNotFound:
            self.logger.error(f"Target [ID:{user_id}]: invalid user ID")
        except exceptions.RetryAfter as e:
            self.logger.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
            await asyncio.sleep(e.timeout)
            return await self.send_message(user_id, response_text, response_data, disable_notification)  # Recursive call
        except exceptions.UserDeactivated:
            self.logger.error(f"Target [ID:{user_id}]: user is deactivated")
        except exceptions.TelegramAPIError:
            self.logger.exception(f"Target [ID:{user_id}]: failed") 
        else:
            self.logger.debug(f"Target [ID:{user_id}]: success")
            return True
        return False 
    

    
    
    
    
    async def respond_to_message(self, message: types.Message, response_text: str, response_data:object) -> bool:
        await self.send_message(message.from_user.id, response_text, response_data)
        pass
    
    
    
    
    async def __event_processor(self):
        while True:
            
            try:
                event = await self.__eventsqueue.get()
                await self.sendEventAsMessage(event)                
            except Exception as e1:
                self.logger.warn("Unable to write message to client reason %s", str(e1))
                pass
            finally:
                self.__eventsqueue.task_done()            
        pass
    
    
    
    
    async def sendEventAsMessage(self, event)-> None:
        if self.__bot_master:
            response_text = event["message"] if "message" in event else event["type"]
            response_data = event["data"]
            await self.send_message(self.__bot_master, response_text, response_data)
        pass



    async def sendImage(self, image, message:str=None)-> None:
        if self.__bot_master:
            response_data = {"data" :  image}
            await self.send_message(self.__bot_master, message, response_data)
        pass    
    
        
    
    async def send_notification(self, message:Text)-> None:
        if self.__bot_master:
            await self.send_message(self.__bot_master, message)
    
    
    
    async def __notifyHandler(self):
        while True:
            try:
                
                data = await self.__mgsqueue.get()
                requestid = data["requestid"]
                response = data["message"]
                handler = self.__requests[requestid]["handler"]
                post_response = self.__requests[requestid]["response"]["text"] 
                subject =  self.__requests[requestid]["subject"]
                
                if handler != None:
                    self.logger.debug("write status for requestid " + str(requestid) + " to client")
                    await self.respond_to_message(subject, post_response, response)
                                
            except Exception as e1:
                
                self.logger.warn("Unable to write message to client %s, reason %s", handler.id, str(e1))
                
            finally:
                
                if requestid != None and requestid in self.__requests:
                    del self.__requests[requestid]
                
                self.__mgsqueue.task_done()
    
    
    
    
    async def handleMessages(self, message: types.Message):
        user_response = message.text
        user_response=user_response.lower()
        if(user_response!='bye'):
            if(user_response=='thanks' or user_response=='thank you' ):
                response = {"text": "You are welcome.." , "action" : None}
            else:
                act_response = self.__nlp_engine.actionable_response(user_response)
                if(act_response != None):
                    response = act_response
                else:
                    response = self.__nlp_engine.response(user_response)
        else:
            response = {"text": "Bye! take care..", "action" : None} 
            
            
        if "intent" in response and response["intent"] != None:
            await self.handleBotRPC(response, message)
        else:
            await message.answer(response["text"])




    '''
    Overriden method from intent provider, handles intent execution result
    '''
    async def onIntentProcessResult(self, requestid:str, result:object) -> None:
        self.logger.info("onIntentProcessResult")
        response = formatSuccessBotResponse(requestid, result)
        await self.__mgsqueue.put({"requestid": requestid, "status": "success", "message": response})
        pass
    

    
    '''
    Overriden method from intent provider, handles intent execution error
    '''
    async def onIntentProcessError(self, requestid:str, e:object, message:str = None) -> None:
        self.logger.info("onIntentProcessError")
        response = formatErrorBotResponse(requestid, e)
        await self.__mgsqueue.put({"requestid": requestid, "status": "error", "message": response})
        pass



    async def start_handler(self, event: types.Message):
        self.__bot_master = event.from_user.id
        await event.answer(f"Hello, {event.from_user.get_mention(as_html=True)} 👋!",parse_mode=types.ParseMode.HTML)
           
                
    
    async def __read_messages(self, params=None):
        await self.__disp.start_polling()
    
    
    def write_message(self, params=None):
        pass
    
    
    def is_webhook_supported(self):
        return self.__supports_webhook
    
    
    def set_webhook_supported(self, supports):
        self.__supports_webhook = bool(supports)
    
    
    def set_webhook(self, url):
        self.__webhook = url
        return False
    
    
    def get_webhook(self):
        return self.__webhook
        
        
    def on_webhook_data(self, data):
        pass
    
    
    def get_webhook_secret(self):
        return self.__webhook_secret
    
    
    async def deactivate(self):
        await self.__bot.close()
        pass