'''
Created on 20-Oct-2020

@author: root
'''
import logging
import tornado


import json
from aiogram import Bot
from oneadmin.abstracts import ServiceBot
from aiogram import Bot, Dispatcher, types
from numpy.distutils.fcompiler import none
from tornado.queues import Queue
import uuid
from exceptions import RPCError
from aiogram.utils import exceptions, executor
from utilities import isJSON, isImagePath
from tornado.platform import asyncio
from aiogram.types.input_file import InputFile





class TelegramBot(ServiceBot):
    
    
    dp = None;
    
    '''
    classdocs
    '''

    def __init__(self, conf, executor, nlp_engine=None):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__connected = False
        self.__supports_webhook = False
        self.__uid = None
        self.__conf = conf
        self.__action_executor = executor
        self.__nlp_engine = nlp_engine
        self.__requests = {}
        self.__mgsqueue = Queue()
        self.id = str(uuid.uuid4())
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__notifyHandler)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__activate_bot)
    
    
    
    async def __activate_bot(self):
    
        try:
            self.__bot = Bot(token=self.__conf['conf']['token'])
            self.__disp = Dispatcher(self.__bot)
            
            self.__disp.register_message_handler(self.handleMessages)
            self.__disp.register_message_handler(self.start_handler, commands={"start", "restart"})
            
            '''    
            self.__disp.register_message_handler(self.text_startswith_handler, text_startswith=['prefix1', 'prefix2'])
            '''
                    
            await self.__read_messages()
            me = await self.__bot.get_me()
            self.__uid =  me.username
            self.logger.debug(f"🤖 Hello, I'm {me.first_name}.\nHave a nice Day!")
        except Exception as e:
            self.logger.error("bot init error " + str(e))
        '''finally:
            await bot.close()'''
            
            
            
    async def handleBotRPC(self, response, message: types.Message):
        
        action = response["action"]
        
        
        #if(not self.isBotRPC(message)):
        #    raise RPCError("Invalid message type. Not a RPC'")
        
        
        requestid = message.message_id
        methodname = action["method"]
        
        args = action["parameters"]
        
        pre_response = action["pre_response"]
        post_response = response["text"]
        wshandler = self
        
        if len(args) == 0: 
            args = [wshandler] 
        else: 
            args.insert(0, wshandler)
        
        try:
            await message.answer(pre_response)
            task_info = {"requestid":requestid, "method": str(methodname), "params": args}
            self.__requests[requestid] = {"handler": wshandler, "response": response, "subject": message} 
            await self.__action_executor.addTask(task_info, self)
        
        except:
            if requestid in self.__requests:
                del self.__requests[requestid]
                
            raise RPCError("Failed to invoke method." + sys.exc_info()[0])
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
            # figure out what kind of output we got
            if isJSON(response_data):
                await self.__bot.send_message(user_id, response_text + "\n\r\n\r" + response_data, disable_notification=disable_notification)
            
            elif isinstance(response_data,dict):
                response_data = json.dumps(dict)    
                await self.__bot.send_message(user_id, response_text + "\n\r\n\r" + response_data, disable_notification=disable_notification)
            
            elif isImagePath(response_data): 
                img = InputFile(str(response_data), "snapshot.jpg")
                await self.__bot.send_photo(user_id, img, response_text)
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
            self.logger.info(f"Target [ID:{user_id}]: success")
            return True
        return False 
    
    
    
    async def respond_to_message(self, message: types.Message, response_text: str, response_data:object) -> bool:
        await self.send_message(message.from_user.id, response_text, response_data)
        pass
            
    
    
    
    async def onExecutionResult(self, requestid, result):
        self.logger.debug("Bot RPC Success")
        response = self.formatSuccessBotResponse(requestid, result)
        await self.__mgsqueue.put({"requestid": requestid, "status": "success", "message": response})
        pass
    
    
    
    async def onExecutionerror(self, requestid, e):
        self.logger.debug("Bot RPC Error")
        err = str(e)
        response = self.formatErrorBotResponse(requestid, err)
        await self.__mgsqueue.put({"requestid": requestid, "status": "error", "message": response})
        pass
    
    
    
    
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
                
                self.logger.warn("Unable to write message to client %s", handler.id)
                
            finally:
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
            
            
        if "action" in response and response["action"] != None:
            action = response["action"]
            if "method" in action and len(action["method"])>0:
                await self.handleBotRPC(response, message)
        else:
            await message.answer(response["text"])



    async def start_handler(self, event: types.Message):
        await event.answer(f"Hello, {event.from_user.get_mention(as_html=True)} 👋!",parse_mode=types.ParseMode.HTML)
    


    def formatSuccessBotResponse(self, requestid, data):
        return str(data)
        pass
    
    
    
    
    def formatErrorBotResponse(self, requestid, error):
        return "An error occurred "  + str(error)
        pass
    
        
    
    '''
    # if the text starts with any string from the list
    async def text_startswith_handler(self, message: types.Message):
    '''
        
                
    
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
    
    
    def deactivate(self):
        pass