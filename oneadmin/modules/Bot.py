'''
Created on 20-Oct-2020

@author: root
'''
import logging
import tornado

import asyncio
from aiogram import Bot
from oneadmin.abstracts import ServiceBot
from aiogram import Bot, Dispatcher, types
from numpy.distutils.fcompiler import none


class TelegramBot(ServiceBot):
    
    dp = None;
    
    '''
    classdocs
    '''

    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__connected = False
        self.__supports_webhook = False
        self.__uid = None
        self.__conf = conf
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__activate_bot)
    
    
    
    async def __activate_bot(self):
    
        try:
            self.__bot = Bot(token=self.__conf['conf']['token'])
            self.__disp = Dispatcher(self.__bot)
            
            self.__disp.register_message_handler(self.start_handler, commands={"start", "restart"})    
            self.__disp.register_message_handler(self.text_in_handler, text=['text1', 'text2'])
            self.__disp.register_message_handler(self.text_contains_any_handler, text_contains='example1')
            self.__disp.register_message_handler(self.text_contains_any_handler, text_contains='example2')  
            self.__disp.register_message_handler(self.text_contains_all_handler, text_contains=['str1', 'str2'])
            self.__disp.register_message_handler(self.text_startswith_handler, text_startswith=['prefix1', 'prefix2'])
            self.__disp.register_message_handler(self.text_endswith_handler, text_endswith=['postfix1', 'postfix2'])
                    
            await self.__read_messages()
            me = await self.__bot.get_me()
            self.__uid =  me.username
            self.logger.debug(f"🤖 Hello, I'm {me.first_name}.\nHave a nice Day!")
        except Exception as e:
            self.logger.error("bot init error " + str(e))
        '''finally:
            await bot.close()''' 



    async def start_handler(self, event: types.Message):
        await event.answer(f"Hello, {event.from_user.get_mention(as_html=True)} 👋!",parse_mode=types.ParseMode.HTML)
        
    
    # if the text from user in the list
    async def text_in_handler(self, message: types.Message):
        await message.answer("The message text equals to one of in the list!")
    
    
    # if the text contains any string
    async def text_contains_any_handler(self, message: types.Message):
        await message.answer("The message text contains any of strings")
    
    
    # if the text contains all the strings from the list
    async def text_contains_all_handler(self, message: types.Message):
        await message.answer("The message text contains all strings from the list")
    
    
    # if the text starts with any string from the list
    async def text_startswith_handler(self, message: types.Message):
        await message.answer("The message text starts with any of prefixes")
    
    
    # if the text ends with any string from the list
    async def text_endswith_handler(self, message: types.Message):
        await message.answer("The message text ends with any of postfixes")

            
    
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
    
    
    def get_webhook_url_config(self):
        return self.__webhook_handler_url_config
    
    
    def set_webhook_url_config(self, urlconfig):
        self.__webhook_handler_url_config = urlconfig
        
        
    def on_webhook_data(self, data):
        pass
    
    
    def get_webhook_secret(self):
        return self.__webhook_secret
    
    
    def deactivate(self):
        pass