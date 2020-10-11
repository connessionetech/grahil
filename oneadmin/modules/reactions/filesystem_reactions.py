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

import logging
import json
import ntpath
import datetime
import time
from oneadmin.utilities import buildLogWriterRule, path_leaf



logger = logging.getLogger(__name__)




'''
        Write log
'''
async def write_log(ruleid, filemanager, params, event):
    # logger.info(json.dumps(params))
    data = event['data']['content']
    await filemanager.write_file_stream(params['filepath'], data)    
    pass



async def copy_file(ruleid, filemanager, params, event):
    # logger.info(json.dumps(params))
    source = params['source']
    destination = params['destination']
    overwrite = params['overwrite']
    
    if filemanager.resource_exists(destination):
        filename = path_leaf(destination)
        millis = int(round(time.time() * 1000))
        filename = filename + "_" + millis
        dirname = ntpath.dirname(destination)
        destination = dirname + filename
    
    await filemanager.copyFile(source, destination)

