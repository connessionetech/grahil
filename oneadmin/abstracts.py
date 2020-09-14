'''
This file is part of `Reactivity` 
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

class Notifyable(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
    
    def notifyEvent(self, event):
        pass  
    



class ServiceBot(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self._initialize()
        
        
    def _initialize(self):
        self.__webhook = False
        self.__supports_webhook = False
        self.__webhook_handler_url_config = None
        self.__webhook_secret = None
        pass
    
    
    def __read_messages(self, params=None):
        pass
    
    
    def __read_message(self, params=None):
        pass
    
    
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
        
    