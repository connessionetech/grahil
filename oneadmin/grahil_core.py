'''
Created on 26-Nov-2020

@author: root
'''

class ModuleRegistry(object):
    
    def __init__(self):
        
        self.__registry = {}        
        pass
    
    
    def registerModule(self, name, reference):
        if name not in self.__registry.keys():
            self.__registry[name] = reference;
        pass
    
    
    def deregisterModule(self, name):
        if name in self.__registry.keys():
            del self.__registry[name]
        pass
    
    
    def getModule(self, name):
        if name in self.__registry.keys():
            return self.__registry[name]
        else:
            return None
        pass
    
    
    def hasModule(self, name):
        if name in self.__registry.keys():
            return True
        else:
            return False
