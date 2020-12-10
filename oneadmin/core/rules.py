'''
Created on 08-Dec-2020

@author: root
'''
from builtins import str
from enum import Enum
from typing import Text
import re
from core.event import EventType


SIMPLE_RULE_EVALUATOR = "SimpleRuleEvaluator"

REG_EX_RULE_EVALUATOR = "RegExRuleEvaluator"






class RuleResponse(object):
    
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
    def intent(self) ->Text:
        return self.__intent
        
        
    @intent.setter
    def intent(self, _intent:Text) -> None:
        self.__intent = _intent
    
    
    @property
    def parameters(self):
        return self.__parameters
        
        
    @parameters.setter
    def parameters(self, _parameters):
        self.__parameters = _parameters



class RuleExecutionEvaluator(object):
    
    
    def name(self) -> Text:
        raise NotImplementedError()
    
    
    def evaluate(self, haystack, needle, condition) -> bool:
        raise NotImplementedError();
        pass



class SimpleRuleEvaluator(RuleExecutionEvaluator):
    
    
    def name(self) -> Text:
        return SIMPLE_RULE_EVALUATOR
    
    
    def evaluate(self, haystack, needle, condition)-> bool:
        if haystack.contains(needle):
            return True
        return False
    
    

class RegExRuleEvaluator(RuleExecutionEvaluator):
    
    
    def name(self) -> Text:
        return REG_EX_RULE_EVALUATOR
    
    
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
        self.__time_expression = None
    
    
    @property
    def recurring(self):
        return self.__recurring
        
        
    @recurring.setter
    def recurring(self, _recurring):
        self.__recurring = _recurring
        
    
    @property
    def time_expression(self):
        return self.__time_expression
        
        
    @time_expression.setter
    def time_expression(self, _time_expression):
        self.__time_expression = _time_expression



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
        self.__expected_content = None
        self.__condition_clause = None
    
    
    @property
    def expected_content(self) ->str:
        return self.__expected_content
        
        
    @expected_content.setter
    def expected_content(self, _expected_content:str) ->None:
        self.__expected_content = _expected_content
        
        
    @property
    def payload_object_key(self) ->str:
        return self.__payload_object_key
        
        
    @payload_object_key.setter
    def payload_object_key(self, _payload_object_key:str) -> None:
        self.__payload_object_key = _payload_object_key
        
        
    @property
    def condition_clause(self) ->str:
        return self.__condition_clause
        
        
    @condition_clause.setter
    def condition_clause(self, _condition_clause:str) -> None:
        self.__condition_clause = _condition_clause
    

        
        


class ReactionRule(object):
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
        self.__target_topic = "*"
        self.__target_event = "*"
        self.__state = RuleState.READY    
    
    
    
    def is_applicable(self, event:EventType) ->bool:
        if self.__target_topic != "*":
            if  self.__target_topic == event["topic"]:
                if self.__target_event != "*":
                    if self.__target_event == event["name"].lower():
                        return True
                else:
                    return True
        else:
            if self.__target_event != "*":
                if self.__target_event == event["name"].lower():
                        return True
            else:
                return True
        
    
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
    def target_event(self) -> Text:
        return self.__target_event
        
        
    @target_event.setter
    def target_event(self, _target_event:Text) -> None:
        self.__target_event = _target_event
    
    
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
    def response(self) -> RuleResponse:
        return self.__response
        
        
    @response.setter
    def response(self, _response:RuleResponse) -> None:
        self.__response = _response
        



def built_in_evaluators():
    return [SimpleRuleEvaluator(), RegExRuleEvaluator()]



def built_in_evaluator_names():
    return [SIMPLE_RULE_EVALUATOR, REG_EX_RULE_EVALUATOR]



def get_evaluator_by_name(name:Text) ->RuleExecutionEvaluator:
   
    for evaluator in built_in_evaluators():
        if evaluator.name() == name:
            return evaluator
    
    return None 

