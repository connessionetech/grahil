#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

"""Basic run script"""

import tornado.ioloop

from settings import settings

import argparse
import os
import json
import logging.config
from oneadmin.configurations import Configuration
from oneadmin.application import TornadoApplication
from tornado.httpserver import HTTPServer

# import cv2

def setup_logging(
    default_path='logging.json',
    default_level=logging.DEBUG,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def load_configuration(
    default_path='configuration.json'
):
    __config = Configuration(default_path)
    __config.load()
    return __config
    



'''
    Restart tornado app and http server
'''
def restart_tornado():
    logging.info("Restarting tornado server")
    tornado.ioloop.IOLoop.current().call_later(5, start_tornado)
    stop_tornado()
    pass



'''
    Stop tornado app and http server
'''
def stop_tornado():
    logging.info("Stopping tornado server")
    
    server = tornado.__dict__["server"]
    app = tornado.__dict__["app"]
    
    if(server != None):
        server.stop()
        ioloop = tornado.ioloop.IOLoop.current()
        ioloop.add_callback(ioloop.stop)
    
    tornado.__dict__["server"] = None
    tornado.__dict__["app"] = None
    
    pass



'''
    Start tornado app and http server
'''
def start_tornado():
    
    logging.info("Starting tornado server")
    
    config = tornado.__dict__["config"]
    
    app = TornadoApplication(config)
    port = None
        
    if(not config['ssl']['enabled']):
        server = HTTPServer(app)
        port = config['server']['http_port']
    else:
        server = tornado.httpserver.HTTPServer(app, ssl_options = {
            "certfile": config['ssl']['cert_file'],
            "keyfile": config['ssl']['private_key']
        })        
        port = config['server']['https_port']
    
    server.listen(port)
    
    tornado.__dict__["server"] = server
    tornado.__dict__["app"] = app
    
    tornado.ioloop.IOLoop.current().start()    
    pass


'''
Entry point
'''
def main():
    try:    
        setup_logging(settings["log_configuration"])
        
        logger = logging.getLogger(__name__)
        logger.info("Starting service")  
        
        app_configuration = load_configuration(settings["app_configuration"])
        tornado.__dict__["config"] = app_configuration.data
        
        tornado.__dict__["start_tornado"] = start_tornado
        tornado.__dict__["stop_tornado"] = stop_tornado
        tornado.__dict__["restart_tornado"] = restart_tornado
        
        start_tornado();
    except Exception as e:
            logging.error("Oops!,%s,occurred.", str(e))





main()
