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

from oneadmin.exceptions import *
from oneadmin.core.constants import FILE_MANAGER_MODULE
from oneadmin.abstracts import IEventDispatcher
from oneadmin.abstracts import IModule

import sys
import logging
import os
import ntpath
import tornado
import datetime as dt
import shutil
import asyncio
import os.path

from pathlib import Path
from aiofile.aio import AIOFile
from shutil import copyfile, copytree
from fileinput import filename
from aiofile.utils import Reader, Writer
from settings import *
from smalluuid.smalluuid import SmallUUID
from datetime import datetime
from tornado.ioloop import IOLoop
from os import path
from _collections import deque
from builtins import str
from typing import List, Text, Callable
from tornado.concurrent import Future
import pathlib





class FileManager(IModule):
    '''
    classdocs
    '''
    
    MAX_WORKERS = 2

    def __init__(self, config, accessible_paths=[]):
        '''
        Constructor
        '''
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)        
        self.__config = config
        
        self.__accessible_paths = accessible_paths
        self.__accessible_paths.append(settings["reports_folder"])        
        
        self.__uploaddir = config["upload_dir"]
        self.__allowed_read_extensions = self.__config["allowed_read_extensions"]
        self.__allowed_write_extensions = self.__config["allowed_write_extensions"]
        
        self.__allowed_system_read_extensions = ["py"]
        self.__allowed_system_write_extensions = []
        
        
        self.__uploads = {}
        self.__filestreams = {}
        
        #tornado.ioloop.IOLoop.current().spawn_callback(self.clean_upload_permits)
        
        if self.__config["auto_clean_tmp_directories"] != None and self.__config["auto_clean_tmp_directories"] != False:
            tornado.ioloop.IOLoop.current().spawn_callback(self.clean_tmp_downloads)
        
        pass  
    
    
    
    
    def initialize(self) ->None:
        self.logger.info("TO DO")
        pass
        
        
        
    
    def name(self) -> Text:
        return FILE_MANAGER_MODULE
            
    
    
    '''
        Append allowed read extensions
    '''
    def append_allowed_read_extensions(self, extensions):
        if isinstance(extensions, list):
            for extension in extensions:
                if extension not in extensions:
                    self.__allowed_read_extensions.append(extension)
        pass
    

    
    
    '''
        Return allowed read extensions
    '''
    @property
    def allowed_read_extensions(self):
        return self.__allowed_read_extensions
    
    
    
    
    '''
        Append allowed write extensions
    '''
    def append_allowed_write_extensions(self, extensions):
        if isinstance(extensions, list):
            for extension in extensions:
                if extension not in extensions:
                    self.__allowed_write_extensions.append(extension)
        pass
    
    
    
    '''
        Return allowed write extensions
    '''
    @property
    def allowed_write_extensions(self):
        return self.__allowed_write_extensions
    
    
    
    '''
        Return allowed system read extensions
    '''
    @property
    def allowed_system_read_extensions(self):
        return self.__allowed_system_read_extensions
    
    
    
    '''
        Return allowed system write extensions
    '''
    @property
    def allowed_system_write_extensions(self):
        return self.__allowed_system_write_extensions
    
    
    
    
    @property
    def uploads(self):
        return self.__uploads  
    
    
    @property
    def maxStreamSize(self):
        if "max_streamed_size" in self.__config: 
                return self.__config["max_streamed_size"]
        else:
            return 0
        
    @property
    def maxUploadSize(self):
        if "max_upload_size" in self.__config: 
                return self.__config["max_upload_size"]
        else:
            return 0
        
    
    async def clean_upload_permits(self):
        
        while True:
            
            cleanup_interval = self.__config["permits_cleanup_interval_seconds"]
            permit_expiry_time = self.__config["permit_expire_time_milliseconds"]
            await asyncio.sleep(cleanup_interval)
            
            for permit, data in list(self.__uploads.items()):
                
                endtime_expired = int(data["end_time"]) > 0 and datetime.utcnow().timestamp()- data["end_time"]
                starttime_expired = datetime.utcnow().timestamp() - data["start_time"] > permit_expiry_time
                
                if data["uploaded"] == True or starttime_expired == True or endtime_expired == True:
                    self.logger.debug("deleting permit " + permit)
                    del self.__uploads[permit]

    
    
    def handle_upload_data_received(self, chunk, permit):
        
        if not permit or not permit in self.__uploads:
            raise FileUploadError("Invalid permit" + permit + ".System could not find your permit")
        else:
            if self.__uploads[permit]["start_time"] == 0:
                    self.__uploads[permit]["start_time"] = datetime.utcnow().timestamp()
            
            self.tmp_buffer += chunk
                
            if len(self.tmp_buffer) > self.maxUploadSize:
                raise FileUploadError("Upload stream size exceeds max allowed size")
            
            self.__uploads[permit]["uploaded_bytes"] = len(self.tmp_buffer)
            self.logger.debug("uploaded " + str(self.__uploads[permit]["uploaded_bytes"]) + "bytes")
        pass     
        
        
    
    def generateUploadSlot(self, filename = None, filesize=0):
        
        if len(list(self.__uploads.items())) > self.__config["max_parallel_uploads"]:
            raise FileUploadError("Upload slots exhausted. Please try after some time")
        
        permit = SmallUUID().hex
        self.__uploads[permit] = {"filename":filename, "start_time":0, "end_time":0, "uploaded":False, "total_bytes":filesize, "uploaded_bytes":0}
        return permit
    
    
    
    def getUploadProgress(self, permit):
        if permit == None or not permit in self.__uploads:
            raise FileUploadError("Invalid permit "+permit+".Unauthorized file upload")
        else:
            return self.__uploads[permit]
    
    
    async def handleUploadComplete(self, permit, data, original_filename, args):
        if("filename" in args and args["filename"] is not None):
            filename = args["filename"][0].decode('utf-8')
        else:
            filename = original_filename
            
        if("path" in args and args["path"] is not None):
            filepath = args["path"][0].decode('utf-8')
        else:
            filepath = None
            
        # Validate request parameters here
        await self.doUpload(filename, filepath, data)
        
        self.__uploads[permit]["end_time"] = datetime.utcnow().timestamp()
        self.__uploads[permit]["uploaded"] = True
        self.__uploads[permit]["filename"] = filename
        pass
    
    
    
    '''
        Cleans the tmp folders created in the publicly accessible `downloads` location
    '''
    async def clean_tmp_downloads(self):
        
        now = dt.datetime.now()
        ago = now-dt.timedelta(minutes=30)
        prefix = self.__config["tmp_download_dir_prefix"]
        
        while True:
            await asyncio.sleep(5) 
            self.logger.debug("Scanning for tmp directories")
            files = os.listdir(settings["static_path"])
            for name in files:
                listing_path = Path(os.path.join(settings["static_path"], name))
                if listing_path.is_dir() == False : continue                    
                elif str(listing_path.absolute()).startswith(prefix):                
                    statinfo = os.stat(str(listing_path))
                    ctime = dt.datetime.fromtimestamp(statinfo.st_birthtime)
                    if(ctime > ago):
                        shutil.rmtree(str(listing_path.absolute()), True)
        pass
        
    
    
    '''
        Check to see if the path we are trying to access is within the list of allowed patrhs
        
        If path is a file , check if the file is explicitly permitted in filemanager paths
        If path is a folder, check if its included in one of the permitted paths
    '''
    def is_path_included(self, path):
        
        for accessible_path in self.__accessible_paths:
            
            if os.path.isfile(accessible_path):
                if path == accessible_path:
                    return True
                
            elif os.path.isdir(accessible_path):
                if path.startswith(os.path.abspath(accessible_path) + os.sep):
                    return True
                
        
        return False
    
    
    
    '''
        Handles file upload. Can write only within base directory defined
    '''
    async def doUpload(self, filename, path, data):
            
        if(not self.is_path_included(path)):
            raise FileSystemOperationError("Requested path is not within allowed path")
            
        
        destination = Path(str(self.__uploaddir))
        file = Path(os.path.join(self.__uploaddir, str(filename)))
                    
        try:
            if not destination.exists():
                destination.mkdir(0o755, True)
            
            async with AIOFile(str(file), "wb") as afp:
                await afp.write(data)
                await afp.fsync()
        except Exception as e:            
            raise FileSystemOperationError("Could not write to file." + str(e))
    
    
        if(path is not None):
            try:
                source_path = file
                destination_path = Path(os.path.join(str(path), str(filename)))
                await self.__moveFile(filename, source_path, destination_path)
            except Exception as e:
                raise FileSystemOperationError("Could not move file to destination" + str(e))
  
  
    def path_leaf(self, path):
        head, tail = ntpath.split(str(path))
        return tail or ntpath.basename(head)
  
         
    '''
        Handles file download. Can write only within base directory defined
    '''
    async def make_downloadable_static(self, configuration, static_path, file_path):
        if(not self.is_path_included(file_path)):
            raise FileSystemOperationError("Requested path is not within allowed path")
        
        static_path = Path(str(static_path))
        if static_path.exists():
            prefix = configuration["tmp_download_dir_prefix"]
            foldername = prefix + SmallUUID().hex
            target_folder = Path(os.path.join(str(static_path.absolute()), foldername))
            target_folder.mkdir(0o755, True)
            if target_folder.exists():
                filename = self.path_leaf(str(file_path))
                target = Path(os.path.join(str(target_folder.absolute()), filename))
                target_path = str(target.absolute())
                copyfile(file_path, target_path) 
                return os.path.join(foldername, filename)
            else:
                raise FileSystemOperationError("Could not create target folder " + foldername)
            pass        
        pass
    
    
    
    async def download_file_async(self, file_path, chunksize, callback):
        
        if(not self.is_path_included(file_path)):
            raise FileSystemOperationError("Requested path is not within allowed path")
        
        file = Path(str(file_path))
        if file.exists():    
            async with AIOFile(str(file_path), 'rb') as afp:
                reader = Reader(afp, chunk_size=chunksize)
                await afp.fsync()
                async for chunk in reader:
                    try:
                        await callback(chunk)
                        #self.write(chunk) # write the cunk to response
                        #await self.flush() # flush the current chunk to socket
                    except:
                        # this means the client has closed the connection
                        # so break the loop
                        break
                    finally:
                        # deleting the chunk is very important because 
                        # if many clients are downloading files at the 
                        # same time, the chunks in memory will keep 
                        # increasing and will eat up the RAM
                        del chunk        
        pass
    
    
    '''
        Deletes a file. Can write only within base directory defined
    '''
    async def deleteFile(self, file_path):
        if(not self.is_path_included(file_path)):
            raise FileSystemOperationError("Requested path is not within allowed path")
        
        file = Path(file_path)
        path = file.absolute()
        if file.exists():            
            if file.is_file():
                await IOLoop.current().run_in_executor(
                    None,
                    self.__delete_file, str(path)
                    )
            else:
                raise FileSystemOperationError("Not a file " + path)
        else:
            raise FileNotFoundError("Invalid path " + path + " or file " + filename + " does not exist")
        
    
    def __delete_file(self, filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            raise FileSystemOperationError("Unable to delete file " + filepath + ".Cause " + str(e))
        pass
    
    
    '''
        Renames an existing file. Can write only from within base directory defined
    '''
    async def rename_file(self, old_file, newname):
        if(not self.is_path_included(old_file)):
            raise FileSystemOperationError("Requested path is not within allowed path")
                
        file = Path(old_file)
        filename = self.path_leaf(old_file)
        path = file.absolute()
        if file.exists():            
            if file.is_file():
                try:
                    dstfile = Path(os.path.join(str(path.parent()), newname))
                    if(dstfile.exists()):
                        raise FileSystemOperationError("File with name " + newname + " already exists at specified location")
                    
                    await IOLoop.current().run_in_executor(
                    None,
                    self.__rename_file, str(file.absolute()), str(dstfile.absolute())
                    ) 
                    return
                except:
                    raise FileSystemOperationError("Could not rename file " + filename)
            else:
                raise FileSystemOperationError("Not a file " + filename)
        else:
            raise FileSystemOperationError("Invalid path " + path + " or file " + filename + " not found")
    
    
    '''
        Moved a file to another location. Can read only from within base directory defined
    '''
    async def moveFile(self, source_path, destination_path):
        if(not self.is_path_included(source_path)):
            raise FileSystemOperationError("Source path is not within allowed path")
        
        if(not self.is_path_included(destination_path)):
            raise FileSystemOperationError("Destination path is not within allowed path")
        
        src_file = Path(source_path)
        filename = self.path_leaf(str(src_file.absolute()))
        if src_file.exists():
            if src_file.is_file():
                dstfile = Path(destination_path)
                if dstfile.exists():
                    raise FileSystemOperationError("File with name " + filename + " already exists at specified location")
                
                await IOLoop.current().run_in_executor(
                    None,
                    self.__rename_file, str(src_file.absolute()), str(dstfile.absolute())
                    )
            else:
                raise FileSystemOperationError("Unable to move file.Only files can be moved")
        else:
            raise FileNotFoundError("Invalid path " + source_path + " or file " + filename + " does not exist")
        pass
    
   
    
    
    '''
        Moved a file to another location.
    '''
    async def __moveFile(self, filename, source_path, destination_path):
        
        if source_path.exists():
            if source_path.is_file():
                if destination_path.exists():
                    raise FileSystemOperationError("File with name " + filename + " already exists at specified location")

                await IOLoop.current().run_in_executor(
                    None,
                    self.__rename_file, str(source_path.absolute()), str(destination_path.absolute())
                    )
            else:
                raise FileSystemOperationError("Unable to move file.Only files can be moved")
        else:
            raise FileNotFoundError("Invalid path " + str(source_path) + " or file " + filename + " does not exist")
        pass
    
    
        
    def __rename_file(self, original_path, new_path):
        try:
            os.rename(original_path, new_path)
        except Exception as e:
            raise FileSystemOperationError("Unable to move file " + original_path + ".Cause " + str(e))
        pass
    
    
    
    '''
        Check if file/folder exists
    '''
    def resource_exists(self, path, isFile=True):
        if(not self.is_path_included(path)):
            raise FileSystemOperationError("path is not within allowed path")
        file = Path(path)
        
        if file.exists():
            if isFile == True:
                if os.path.isfile(path):
                    return True
                return False
            else:
                if os.path.isfile(path):
                    return False
                return True
        else:
            return False
        
    
    
    '''
        Copies a file or folder to another location. Can read only from within base directory defined
    '''
    async def copyFile(self, source_path:str, destination_path:str):
        if(not self.is_path_included(source_path)):
            raise FileSystemOperationError("Source path is not within allowed path")
        
        if(not self.is_path_included(destination_path)):
            raise FileSystemOperationError("Destination path is not within allowed path")
        
        
        src_file = Path(source_path)
        filename = self.path_leaf(str(src_file.absolute()))
        if src_file.exists():            
            dstfile = Path(destination_path)
            if(src_file.is_file()):                    
                if(dstfile.exists() and dstfile.is_file()):
                    raise FileSystemOperationError("File with name " + filename + " already exists at specified location")
                
                await IOLoop.current().run_in_executor(
                    None,
                    self.__copy_file_async, source_path, destination_path
                    )
            elif(src_file.isdir()):
                if(dstfile.exists() and dstfile.is_dir()):
                    raise FileSystemOperationError("Directory with name " + filename + " already exists at specified location")
                
                await IOLoop.current().run_in_executor(
                    None,
                    self.__copy_tree_async, source_path, destination_path
                    )
                pass 
            else:
                raise FileSystemOperationError("Unsupported copy mode")
        else:
            raise FileNotFoundError("Invalid path "+ src_file + " or file " + filename + " not found")
        pass
    
    
    def __copy_file_async(self, source, destination):
        try:
            copyfile(source, destination) # file to file
        except Exception as e:
            raise FileSystemOperationError("Unable to copy file " + source + " to " + destination + ".Cause " + str(e))
        pass
    
    
    def __copy_tree_async(self, source, destination):
        try:
            copytree(source, destination) # folder to folder
        except Exception as e:
            raise FileSystemOperationError("Unable to copy tree " + source + " to " + destination + ".Cause " + str(e))
        pass
    
    
    '''
        Reads a file. Can read only from within base directory defined
    '''
    async def readFile(self, filepath):
        if(not self.is_path_included(filepath)):
            raise FileSystemOperationError("Requested path is not within allowed path")
        
        file = Path(filepath)
        filename = self.path_leaf(filepath)
        
        extension = os.path.splitext(filename)[1]
        if not extension in self.__allowed_read_extensions:
            raise Exception("Extension "+extension+" is not permitted in a read operation")
        
        path = file.absolute()
        if file.exists():            
            if file.is_file():
                try:
                    async with AIOFile(str(path), "r") as afp:
                        content = await afp.read()
                        return content
                except:
                    raise FileSystemOperationError(sys.exc_info()[0] + "Could not read file " + filename)
                finally:
                    pass
            else:
                raise FileSystemOperationError("Not a file " + filename)
        else:
            raise FileNotFoundError("Invalid path " + path + " or file " + filename + " not found")
    
    
    
    '''
        Writes a file. Can write only from within base directory defined
    '''
    async def writeFile(self, filepath, content, reserved = False, must_exist = True):
        if reserved == True and not self.is_path_included(filepath):
            raise FileSystemOperationError("Requested path is not within allowed path")
        
        file = Path(filepath)
        filename = self.path_leaf(filepath)
        
        extension = os.path.splitext(filename)[1]
        if not extension in self.__allowed_write_extensions:
            raise Exception("Extension "+extension+" is not permitted in a write operation")
        
        path = file.absolute()
        
        if must_exist and not file.exists():
            raise FileNotFoundError("Invalid path " + path + " or file " + filename + " not found. must exist to write to")
        
        if must_exist and not file.is_file():
            raise FileNotFoundError("Path " + path + " is not a file.")
        
        try:
            async with AIOFile(str(path), "w+") as afp:
                await afp.write(content)
                await afp.fsync()
        except:
            raise FileSystemOperationError("Could not write to file " + filename)
        
        
    
    '''
        Writes a file. Can write only from within base directory defined
    '''
    async def write_report(self, content, name=None):
        
        filename_prefix = self.__config["report_name_prefix"]
        
        target_folder = Path(settings["reports_folder"])
        # target_folder.mkdir(0o755, True)
        
        if not target_folder.exists():
            raise FileSystemOperationError("Could not create tmp directory for report")
        
        if name == None:
            name = filename_prefix + SmallUUID().hex + ".txt"
            
        filepath = Path(os.path.join(str(target_folder.absolute()), name))        
        file = Path(filepath)
        filename = self.path_leaf(filepath)
        
        try:
            await self.writeFile(filepath, content, False, False)
            if file.exists(): 
                return filepath.absolute()
        except Exception as ex:
            raise FileSystemOperationError("Could not write report " + str(ex))

        
    
    '''
        Creates directory at a  given path
    '''
    async def create_directory(self, path, dirname):
        if(not self.is_path_included(path)):
            raise FileSystemOperationError("Requested path is not within allowed path")
        
        dir_file = Path(os.path.join(path, dirname))
        
        if dir_file.exists()  and dir_file.is_dir():
            raise FileSystemOperationError("Directory " + dirname + " already exists at " + path)
        
        await IOLoop.current().run_in_executor(None,self.__create_directory_async, dir_file, 0o755) 
        
        pass
    
    
    
    def __create_directory_async(self, file, permissions):
        try:
            os.mkdir(file, permissions) 
        except Exception as e:
            raise FileSystemOperationError("Unable to create resource at path " + str(file.absolute()) + ".Cause " + str(e))
        pass
    
    
    
    
    '''
        Removes directory at a  given path
    '''
    async def remove_directory(self, path, dirname):
        if(not self.is_path_included(path)):
            raise FileSystemOperationError("Requested path is not within allowed path")
        
        dir_file = Path(os.path.join(path, dirname))
        
        if not dir_file.exists()  and dir_file.is_dir():
            raise FileSystemOperationError("Directory " + dirname + " does not exists at " + path)
        
        if dir_file.exists()  and not dir_file.is_dir():
            raise FileSystemOperationError(dirname + " is not a directory at path " + path)
        
        await IOLoop.current().run_in_executor(None,self.__delete_directory_async, dir_file, 0o755) 
        
        pass
    
    
    
    def __delete_directory_async(self, file, permissions):
        try:
            os.remove(file) 
        except Exception as e:
            raise FileSystemOperationError("Unable to create resource at path " + str(file.absolute()) + ".Cause " + str(e))
        pass
        
        
    
    '''
        Reads the directory listing of the given path (used by WS handler)
    '''    
    async def browse_content(self, path):
        if(not self.is_path_included(path)):
            raise FileSystemOperationError("Requested path is not within allowed path")
        file = Path(path)
        path = file.absolute()
        if file.exists():
            files_listing = []
            files = os.listdir(str(path))
            files = await IOLoop.current().run_in_executor(
                    None,
                    self.__list_directory_async, str(path)
                    ) 
            for name in files:
                listing_path = Path(os.path.join(path, name))
                if(listing_path.is_dir() == False and listing_path.is_file() == False):
                    continue                
                statinfo = os.stat(str(listing_path))
                listing = {}
                listing["name"] = name
                
                listing["is_directory"] = listing_path.is_dir()
                listing["last_modified"] = statinfo[8]
                
                st = os.stat(listing_path)
                oct_perm = oct(st.st_mode)
                listing["permission"] = str(oct_perm)[-3:]
                
                files_listing.append(listing)
                
            return files_listing
        else:
            raise FileSystemOperationError("Invalid path " + path + " or file " + filename + " not found")
        
    
    def __list_directory_async(self, filepath):
        
        try:
            files = os.listdir(filepath)
            return files
        except Exception as e:    
            raise FileSystemOperationError("Unable to list path " + filepath + ".Cause " + str(e))
        pass
    
    
    async def write_file_stream(self, filepath, content, must_exist = False):
        
        file = Path(filepath)
        filename = self.path_leaf(filepath)
        
        extension = os.path.splitext(filename)[1]
        if not extension in self.__allowed_write_extensions:
            raise Exception("Extension "+extension+" is not permitted in a write operation")
        
        path = file.absolute()
        
        if must_exist :
            if not file.exists():
                raise FileNotFoundError("Invalid path " + path + " or file " + filename + " not found. must exist to write to")
        else:
            if not file.exists():
                async with AIOFile(str(path), 'w+') as afp:
                    await afp.fsync()

        if not file.is_file():
            raise FileNotFoundError("Path " + path + " is not a file.")

                
        try:
            
            async with AIOFile(str(path), "a+") as afp:
                writer = Writer(afp)  
                
                try:
                    if isinstance(content, deque):                    
                        while len(content) > 0:
                            line = content.popleft()
                            await writer(line)
                except Exception as ex:
                    self.logger.error("An error occured while writing data : "  + line + " . Cause " + str(ex)) 
                
                await afp.fsync()               
                
        except Exception as ex1:
            raise FileSystemOperationError("Could not write to file " + filename + "." +  str(ex1))
        
    
    
    
    
    def get_modules(self):
        
        current_directory = pathlib.Path(__file__).parent.absolute()
        file = Path(os.path.join(current_directory, "modules"))
        path = file.absolute()
        if file.exists():
            files_listing = []
            files = os.listdir(str(path))
            for name in files:
                listing_path = Path(os.path.join(path, name))
                if(listing_path.is_dir() == False and listing_path.is_file() == False):
                    continue
                files_listing.append(Path(name).stem)
                
            return files_listing
        else:
            raise FileSystemOperationError("Invalid path " + path + " or file " + filename + " not found")    
    
    
    
    
        
        
    
    '''
    Fetches a list of files of specified types from a  path cand returns the response via a deferred object
    Note: System method, not for API usage  
    '''
    def list_files(self, callback:Callable, path:Text, file_types:List=["*"])->None:
        
        if path != None and (not self.is_path_included(path)):
            raise FileSystemOperationError("Requested path is not within allowed path")
        
        for file_type in file_types:
            if not file_type in self.__allowed_read_extensions:
                raise FileSystemOperationError("Extension "+file_type+" is not permitted in a write operation")
        
        '''
        if path == None:
            root_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        else:
            root_path = path
        ''' 
        
        directory_content_future:Future = Future()
        directory_content_future.add_done_callback(callback)
        tornado.ioloop.IOLoop.current().spawn_callback(self.__list_files, directory_content_future, path, file_types)
        pass
    
    
    
    '''
    (internal : async) Fetches a list of files of specified types from a  path
    '''
    async def __list_files(self, directory_content_future:Future, path:Text, file_types:List=["*"])->None:
        
        files = []
         
        try:
            script_folder = path    
            contents = await self.browse_content(script_folder)
                        
            for content in contents:
                if content["is_directory"] == False:
                    filename, file_extension = os.path.splitext(content["name"])
                    if file_extension in file_types or "*" in file_types:
                        full_path = os.path.join(script_folder,  content["name"]) 
                        files.append({"name": content["name"], "path": full_path})
            
            directory_content_future.set_result(files)
            
        except Exception as e:
            directory_content_future.set_exception(e)
        pass
        
    
    async def get_updater_script(self):
        
        # Add restriction here to prevent path injection
        
        root_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        updater_script = os.path.join(root_path,  "updater.sh")        
        home = str(os.path.expanduser('~'))
        
        if "updater_dir" not in self.__config:
            raise ValueError("updater location not specified")
        
        updater_dir = str(self.__config["updater_dir"])
        
        if os.path.sep in updater_dir:
            updater_folder = updater_dir
        else:
            updater_folder=os.path.join(home, self.__config["updater_dir"])
        
        if not os.path.isdir(updater_folder):
            await IOLoop.current().run_in_executor(
                None, self.__create_directory_async, 
                updater_folder, 0o755
                )        
            
        updater_script = os.path.join(root_path, "updater.sh")
        updater_script_executable = os.path.join(updater_folder, "updater.sh")
        
        if not os.path.isfile(updater_script_executable):
            await IOLoop.current().run_in_executor(
                    None,
                    self.__copy_file_async, updater_script, updater_script_executable
                    )
            
        return updater_script_executable