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

from tornado.httpclient import AsyncHTTPClient
from ast import literal_eval
import urllib
import logging
import json


logger = logging.getLogger(__name__)




'''
        Reaction to event via HTTP
'''
async def http_reaction(ruleid, url, method, queryparams=None, event=None):
    http_client = AsyncHTTPClient()
    qparams = ""
    body = None
    
    try:
        if queryparams != None:
            for key in queryparams:
                
                if len(qparams) == 0:
                    qparams = qparams + "?"
                    
                if len(qparams) > 1 and qparams.count("=") > 0:
                    qparams = qparams + "&"                        
                
                value = queryparams[key]
                qparams = qparams + (key + "=" + value)
                 
        url = url + qparams
        method = method.upper()
        
        if method == "POST" or method == "PUT":
            if event != None and event["data"] != None:
                
                if isinstance(event["data"], str):
                    postdata = literal_eval(event["data"])
                else:
                    postdata = event["data"]
                    
                body = urllib.parse.urlencode(postdata)
        
        response = await http_client.fetch(url, method=method, headers=None, body=body)
        logger.debug("response = %s", str(response))
        
        if response.code == 200:
            logger.info(str(response.body, 'utf-8'))
        
    except Exception as e:
        logger.error("Error in http reaction for rule %s : %s ", ruleid, e)
    pass   
