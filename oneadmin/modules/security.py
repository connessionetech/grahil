'''
Created on 20-Apr-2021

@author: root
'''
from oneadmin.abstracts import IModule
from oneadmin.exceptions import AccessPermissionsError

import logging
from typing import Text
import datetime
import jwt
import json
import asyncio
import tornado


logger = logging.getLogger(__name__)


class SecurityProvider(IModule):
    '''
    classdocs
    '''
    
    NAME = "security_provider"



    def __init__(self, config):
        '''
        Constructor
        '''
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__config = config
        
        
        self.users = self.__config["users"]
        self.userlevels = self.__config["userlevels"]
        self.permissions = self.__config["permissions"]
        
        self.__jwt_algorithm = self.__config["jwt_algorithm"]
        self.__jwt_secret = self.__config["jwt_secret"]
        self.__jwt_token_expiry_hours = self.__config["jwt_token_expiry_hours"]
        self.__token_keep = {}
    
    
    
    def initialize(self) ->None:
        self.logger.info("Module init")
        tornado.ioloop.IOLoop.current().spawn_callback(self.__token_validator)
        pass



    def getname(self) ->Text:
        return SecurityProvider.NAME
    
    
    
    
    '''Shallow authentication'''
    def authenticate(self, username, mhash):
        self.logger.info("Authenticating %s for hash %s", username, mhash)
        for user in self.users:
            if(user['username'] == username and user['hash'].lower() == mhash.lower()):
                return True
        return False
    
    
    
    ''' Issue JWT token for authenticated users'''
    def issueTokenForAuthenticatedUser(self, request, username):
        role = self.getRole(username)
        x_real_ip = request.headers.get("X-Real-IP")
        remote_ip = x_real_ip or request.remote_ip
        issued_at = datetime.datetime.utcnow().timestamp()
        # issue time  + expiry hours
        expires_at = issued_at + (self.__jwt_token_expiry_hours * 60 * 60 * 1000)
        data = {"remote_addr": remote_ip, "username": username, "role": role, "issued_at": issued_at, "expires_at": expires_at}
        encoded = jwt.encode(data, self.__jwt_secret, algorithm=self.__jwt_algorithm)
        token = encoded.decode('utf-8')
        self.__token_keep[token] = data
        return token
    
    
    
    ''' Verify JWT token'''
    def verifyToken(self, request, encoded_token):
        try:
            decoded_token = jwt.decode(encoded_token, self.__jwt_secret,  algorithms=[self.__jwt_algorithm])
            decoded_data = json.dumps(decoded_token)
            decoded_json = json.loads(decoded_data)
            username = decoded_json["username"]
            remote_addr = decoded_json["remote_addr"]
            role = decoded_json["role"]
            issued_at = decoded_json["issued_at"]
            expires_at = decoded_json["expires_at"]
            
            x_real_ip = request.headers.get("X-Real-IP")
            remote_ip = x_real_ip or request.remote_ip
            
            if not encoded_token in self.__token_keep:
                raise Exception("Token is invalid or unknown to the system!")
            
            if self.__token_invalid(username, expires_at):
                raise Exception("Token expired!")
            
            if remote_addr != remote_ip:
                raise Exception("Token hijacked or tampered with!")
            
            self.logger.debug("Authenticated %s as %s", username, role)
            return {"username":username, "role":role, "issued_at":issued_at}
        except Exception as e:
            err = "Unable to decode token "+encoded_token+". Cause "+ str(e)
            self.logger.error(err)
            raise AccessPermissionsError("Unable to decode token.Invalid or tampered token")
    
    
    
    
    ''' Expire JWT token'''
    def expireToken(self, encoded_token):
        try:
            decoded_token = jwt.decode(encoded_token, self.__jwt_secret,  algorithms=[self.__jwt_algorithm])
            decoded_data = json.dumps(decoded_token)
            decoded_json = json.loads(decoded_data)
            username = decoded_json["username"]
            
            if not encoded_token in self.__token_keep:
                raise Exception("Token is already expired or is unknown to the system!")
            
            self.logger.info("Expiring token " + encoded_token + " for username " + username)
            del self.__token_keep[encoded_token]
        except Exception as e:
            err = "Unable to decode token "+encoded_token+". Cause "+ str(e)
            self.logger.error(err)
            raise AccessPermissionsError("Unable to decode token.Invalid or tampered token")   
    
    
    
    def __token_invalid(self, username, expires_at):
        current_time = datetime.datetime.utcnow().timestamp()
        
        # If token has expired by time
        if current_time > expires_at:
            return True
        else:
            for user in self.users:
                if(user['username'] == username):
                    return False
           
            # If username does not exist     
            return True        
        pass            
    
    
    '''
    Loops through and invalidates tokens if they have expired
    '''
    async def __token_validator(self):
        while True:
            for token, data in self.__token_keep.items(): 
                
                try:
                
                    self.logger.debug("Checking token " + token + " for expiry")
                    
                    '''
                    remote_addr = data["remote_addr"]
                    token_user = data["username"]
                    token_role = data["role"]
                    issued_at = data["issued_at"]
                    '''
                    expires_at = data["expires_at"]
                    
                    # If expired
                    current_time = datetime.datetime.utcnow().timestamp()
                    if current_time > expires_at:
                        self.logger.info("Expiring token " + token)
                        del self.__token_keep[token]
                         
                except Exception as e:
                    self.logger.error("An error occurred while checking token " + token + " " + str(e))
        
            await asyncio.sleep(5)            
        pass
    
    
    '''Get role of user'''
    def getRole(self, username):
        self.logger.info("Fetching role for username %s", username)
        for user in self.users:
            if(user['username'] == username):
                return user['role']
        return None
    
    
    '''Get permissions context for a role'''
    def getPermissions(self, role):
        self.logger.info("Fetching permissions for role %s", role)
        for permissions in self.permissions:
            if(permissions['role'] == role):
                return permissions['contexts']
        return None
    
    
    '''Get users'''
    def getUsers(self):
        self.logger.info("Fetching users info")
        userslist = []
        for user in self.users:
            userobj = None
            userobj["username"] = user["username"]
            userobj["role"] = user["role"]
            userslist.append(userobj)
            
        return userslist
    
    
    '''Get level for a role'''
    def getLevelForRole(self, role):
        for userlevel in self.userlevels:
            if(userlevel['role'] == role):
                return userlevel['level']
        
        return None
        pass
        