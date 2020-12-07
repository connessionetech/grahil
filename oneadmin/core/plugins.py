'''
Created on 08-Dec-2020

@author: root
'''
from typing import Text, Dict, List
from abstracts import IntentProvider




def builtin_plugins() -> List[PluginBase]:
    return [AllowedIntentPlugin()]



class PluginBase(object):
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
    
    

    
    
class IntentPluginBase(PluginBase):
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