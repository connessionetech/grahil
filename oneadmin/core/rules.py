'''
Created on 08-Dec-2020

@author: root
'''
from builtins import str
from enum import Enum
from typing import Text
import re



class RuleReaction(object):
    
    def __init__(self):
        '''
        Constructor
        '''
        self.__nonce = False
        self.__intent = None
        self.__parameters = {}
    
    
    @property
    def nonce(self) ->bool:
        return self.__nonce
        
        
    @nonce.setter
    def nonce(self, _nonce:bool)->None:
        self.__nonce = _nonce
    
    
    @property
    def intent(self):
        return self.__intent
        
        
    @intent.setter
    def intent(self, _intent):
        self.__intent = _intent
    
    
    @property
    def parameters(self):
        return self.__parameters
        
        
    @parameters.setter
    def parameters(self, _parameters):
        self.__parameters = _parameters



class RuleExecutionEvaluator(object):
    
    
    def evaluate(self, haystack, needle, condition) -> bool:
        raise NotImplementedError();
        pass



class SimpleCheckEvaluator(RuleExecutionEvaluator):
    
    def evaluate(self, haystack, needle, condition)-> bool:
        if haystack.contains(needle):
            return True
        return False
    
    

class RegExCheckEvaluator(RuleExecutionEvaluator):
    
    def evaluate(self, haystack, regex, condition=None)-> bool:
        pattern = re.compile(condition)
        if pattern.match(haystack):
            return True
        return False



class RuleState(Enum):
    
    READY = 1
    EXECUTING = 2
    ERROR = 3
    DONE = 4



class Trigger(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.__evaluator = None
    
    
    @property
    def evaluator(self) -> RuleExecutionEvaluator:
        return self.__evaluator
        
        
    @evaluator.setter
    def evaluator(self, _evaluator:RuleExecutionEvaluator):
        self.__evaluator = _evaluator
        



class TimeTrigger(Trigger):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
        self.__recurring = False
        self.__cron_expression = None
    
    
    @property
    def recurring(self):
        return self.__recurring
        
        
    @recurring.setter
    def recurring(self, _recurring):
        self.__recurring = _recurring
        
    
    @property
    def cron_expression(self):
        return self.__cron_expression
        
        
    @cron_expression.setter
    def cron_expression(self, _cron_expression):
        self.__cron_expression = _cron_expression



class PayloadTrigger(Trigger):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
        self.__payload_object_key = None
    
    
    @property
    def payload_object_key(self):
        return self.__payload_object_key
        
        
    @payload_object_key.setter
    def payload_object_key(self, _payload_object_key):
        self.__payload_object_key = _payload_object_key
        
        


class RuleBase(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.__id = None
        self.__description = None
        self.__trigger = None
        self.__response = None
        self.__enabled = False
        self.__target_topic = None
        self.__state = RuleState.READY
        
    
    @property
    def id(self) -> Text:
        return self.__id
    

    @id.setter
    def id(self, _id:Text) -> None:
        self.__id = _id
        
        
    @property
    def description(self) -> Text:
        return self.__description
    

    @description.setter
    def description(self, _description:Text):
        self.__description = _description
    
    
    @property
    def target_topic(self) -> Text:
        return self.__target_topic
        
        
    @target_topic.setter
    def target_topic(self, _target_topic:Text) -> None:
        self.__target_topic = _target_topic
    
    
    @property
    def enabled(self) -> bool:
        return self.__enabled
        
        
    @enabled.setter
    def enabled(self, _enabled:bool) -> None:
        self.__enabled = _enabled
        
    
    @property
    def state(self) -> RuleState:
        return self.__state
    
    
    @state.setter
    def state(self, _state:RuleState) -> None:
        self.__state = _state
        
        
    @property
    def trigger(self) -> Trigger:
        return self.__trigger
        
        
    @trigger.setter
    def trigger(self, _trigger:Trigger) -> None:
        self.__trigger = _trigger
    
    
    @property
    def response(self) -> RuleReaction:
        return self.__trigger
        
        
    @response.setter
    def response(self, _response:RuleReaction) -> None:
        self.__response = _response
        



class CronRule(RuleBase):
    '''
    classdocs
    '''


    def __init__(self, params=None):
        '''
        Constructor
        '''
        super().__init__()
        self.__recurring = False
        self.__cron_expression = None
         
    
    @property
    def recurring(self):
        return self.__recurring
        
        
    @recurring.setter
    def recurring(self, _recurring):
        self.__recurring = _recurring
        
    
    @property
    def cron_expression(self):
        return self.__cron_expression
        
        
    @cron_expression.setter
    def cron_expression(self, _cron_expression):
        self.__cron_expression = _cron_expression
