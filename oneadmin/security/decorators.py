'''
Created on 21-Apr-2021

@author: root
'''


from oneadmin.exceptions import AccessPermissionsError
from oneadmin.core.constants import SECURITY_PROVIDER_MODULE

import tornado
import logging



logger = logging.getLogger(__name__)



''' Controls access to method by checking if user is valid '''
def authenticate_client(func):
    def wrapper(*args, **kwargs):
        
        handler = args[0]
        application = handler.application
        
        if not application.modules.hasModule(SECURITY_PROVIDER_MODULE):
            raise ModuleNotFoundError("Security module not found")
        
        accesscontroller = application.modules.getModule(SECURITY_PROVIDER_MODULE)

        token = None
        
        if isinstance(handler, tornado.websocket.WebSocketHandler):
            token = handler.get_argument("token", None, True)
        else:
            token = handler.request.headers.get("token", None)
            
        if(token == None):
            error = "Access denied as token not specified"
            raise ValueError(error)
        else:
            accesscontroller = handler.application.accesscontroller
            try:
                access_data = accesscontroller.verifyToken(handler.request, token)
                
                ''' Append user info to handler for websocket '''
                if isinstance(handler, tornado.websocket.WebSocketHandler) and hasattr(handler, "identity") == False:
                    identity = {}
                    identity["username"] = access_data["username"]
                    identity["role"] = access_data["role"]
                    setattr(handler, "identity", identity)
                    setattr(handler, "token", token)
                
                return func(*args, **kwargs)
               
            except Exception as e:
                    error = str(e)
                    logger.error(str(e))                    
                    raise AccessPermissionsError(error)
    return wrapper





''' Controls access to arbitrary methods by user's role '''
def authorize_method(requiredrole='observer'):                            
    def decorator(fn):                                            
        def decorated(*args,**kwargs):
            handler = args[0]
            application = handler.application
            
            if not application.modules.hasModule(SECURITY_PROVIDER_MODULE):
                raise ModuleNotFoundError("Security module not found")
            
            accesscontroller = application.modules.getModule(SECURITY_PROVIDER_MODULE)
            
            if not isinstance(handler, tornado.websocket.WebSocketHandler) and not isinstance(handler, tornado.web.RequestHandler):
                handler = args[1]
                if not isinstance(handler, tornado.websocket.WebSocketHandler) and not isinstance(handler, tornado.web.RequestHandler):
                    raise Exception("Could not identify request handler")
                 
            token = None
        
            if isinstance(handler, tornado.websocket.WebSocketHandler):
                token = handler.get_argument("token", None, True)
            else:
                token = handler.request.headers.get("token", None)
            
            error = None
            
            if(token == None):
                error = "Access denied as token not specified"
                raise ValueError(error)
            else:
                required_level = accesscontroller.getLevelForRole(requiredrole)
                if required_level == None:
                        raise AccessPermissionsError("Unable to locate access `level` for role " + requiredrole + ".Possibly invalid `role` or data not found")
                try:
                    access_data = accesscontroller.verifyToken(handler.request, token)
                    ''' Append user info to handler for websocket '''
                    if isinstance(handler, tornado.websocket.WebSocketHandler) and hasattr(handler, "identity") == False:
                        identity = {}
                        identity["username"] = access_data["username"]
                        identity["role"] = access_data["role"]
                        setattr(handler, "identity", identity)
                        setattr(handler, "token", token)
                    
                    user_level = accesscontroller.getLevelForRole(access_data["role"])
                    if user_level == None:
                        raise AccessPermissionsError("Unable to locate access `level` for user " +access_data.username)
                    
                    if int(user_level) >= int(required_level):
                        raise AccessPermissionsError("Insufficient permissions. User does not have sufficient privilege to invoke this method")
                        pass
                    
                    return fn(*args,**kwargs) 
                    
                except Exception as e:
                    error = str(e)
                    logger.error(str(e))
                    raise AccessPermissionsError(error) 
        return decorated                                          
    return decorator




''' Controls access to action by user's role '''
def authorize__action(requiredrole='observer'):                            
    def decorator(fn):                                            
        def decorated(*args,**kwargs):
            action = args[0]
            handler = args[3]["handler"]
            application = handler.application
            
            if not application.modules.hasModule(SECURITY_PROVIDER_MODULE):
                raise ModuleNotFoundError("Security module not found")
            
            accesscontroller = application.modules.getModule(SECURITY_PROVIDER_MODULE)
            
            if not isinstance(handler, tornado.websocket.WebSocketHandler) and not isinstance(handler, tornado.web.RequestHandler):
                return
                '''
                handler = args[1]
                if not isinstance(handler, tornado.websocket.WebSocketHandler) and not isinstance(handler, tornado.web.RequestHandler):
                    raise Exception("Could not identify request handler")
                '''
                 
            token = None
        
            if isinstance(handler, tornado.websocket.WebSocketHandler):
                token = handler.get_argument("token", None, True)
            elif(tornado.web.RequestHandler):
                token = handler.request.headers.get("token", None)
            else:
                return
            
            error = None
            
            if(token == None):
                error = "Access denied as token not specified"
                raise ValueError(error)
            else:
                required_level = accesscontroller.getLevelForRole(requiredrole)
                if required_level == None:
                        raise AccessPermissionsError("Unable to locate access `level` for role " + requiredrole + ".Possibly invalid `role` or data not found")
                try:
                    access_data = accesscontroller.verifyToken(handler.request, token)
                    ''' Append user info to handler for websocket '''
                    if isinstance(handler, tornado.websocket.WebSocketHandler) and hasattr(handler, "identity") == False:
                        identity = {}
                        identity["username"] = access_data["username"]
                        identity["role"] = access_data["role"]
                        setattr(handler, "identity", identity)
                        setattr(handler, "token", token)
                    
                    user_level = accesscontroller.getLevelForRole(access_data["role"])
                    if user_level == None:
                        raise AccessPermissionsError("Unable to locate access `level` for user " +access_data.username)
                    
                    if int(user_level) >= int(required_level):
                        raise AccessPermissionsError("Insufficient permissions. User does not have sufficient privilege to invoke this method")
                        pass
                    
                    return fn(*args,**kwargs) 
                    
                except Exception as e:
                    error = str(e)
                    logger.error(str(e))
                    raise AccessPermissionsError(error) 
        return decorated                                          
    return decorator

