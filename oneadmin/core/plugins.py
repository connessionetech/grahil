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
from typing import Text, Dict, List
from oneadmin.core.abstracts import IntentProvider




def builtin_plugins() -> List[PluginBase]:
    return [AllowedIntentPlugin()]



class IPluginBase(object):
    '''
    classdocs
    '''
        
    
    '''
    Abstract method, must be defined in concrete implementation. plugin names must be unique
    '''
    def name(self) -> Text:
        raise NotImplementedError
    
    
    
    '''
    spits out string name of action
    '''
    def __str__(self) -> Text:
        return "Action('{}')".format(self.name())
    
    

    
    
class IntentPluginBase(IPluginBase):
    '''
    Abstract class to facilitate intercepting intent requests to the action dispatcher 
    '''


    def __init__(self, conf=None):
        '''
        Constructor
        '''
        super().__init__()
        self.__conf = conf       
    
    
    
    '''
    Abstract method, must be defined in concrete implementation. plugin names must be unique
    '''
    def name(self) -> Text:
        raise NotImplementedError
    
    
    
    
    '''
    Abstract intercept method for intent request -> to be implemented in actual method
    '''
    def onIntentRequest(self, provider:IntentProvider, intent:Text, parameters:Dict=None) -> Text:
        raise NotImplementedError
    
    
    
    '''
    spits out string name of action
    '''
    def __str__(self) -> Text:
        return "Intent Plugin ('{}')".format(self.name())
        
        
        


class AllowedIntentPlugin(IntentPluginBase):
    '''
    Abstract class to facilitate intercepting intent requests to the action dispatcher 
    '''


    def __init__(self, conf=None):
        '''
        Constructor
        '''
        super().__init__()      
    
    
    
    '''
    Abstract method, must be defined in concrete implementation. plugin names must be unique
    '''
    def name(self) -> Text:
        return "ALLOWEDINTENTPLUGIN"
    
    
    
    
    '''
    Abstract intercept method for intent request -> to be implemented in actual method
    '''
    def onIntentRequest(self, provider:IntentProvider, intent:Text, parameters:Dict=None) -> None:
        if intent.contains("folder"):
            raise ValueError("Folder operations are not yet supported!")
    
    
    
    '''
    spits out string name of action
    '''
    def __str__(self) -> Text:
        return "Intent Plugin ('{}')".format(self.name())