'''
Created on 31-Oct-2020

@author: root
'''
from tornado.queues import Queue
import logging
from oneadmin.responsebuilder import formatSuccessRPCResponse, formatErrorRPCResponse
import tornado
from oneadmin.exceptions import RPCError, ModuleNotFoundError
from tornado.concurrent import asyncio

class ActionExecutor(object):
    '''
    classdocs
    '''


    def __init__(self, conf, modules):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__task_queue = {}
        self.__conf = conf
        self.__system_modules = modules
        self.__initialize()
        pass
    
    
    def __initialize(self):
        self.__task_queue["start_target"] = Queue(maxsize=5)
        self.__task_queue["stop_target"] = Queue(maxsize=5)
        self.__task_queue["restart_target"] = Queue(maxsize=5)
        self.__task_queue["start_log_recording"] = Queue(maxsize=5)
        self.__task_queue["stop_log_recording"] = Queue(maxsize=5)
        self.__task_queue["subscribe_channel"] = Queue(maxsize=5)
        self.__task_queue["unsubscribe_channel"] = Queue(maxsize=5)
        self.__task_queue["create_channel"] = Queue(maxsize=5)
        self.__task_queue["remove_channel"] = Queue(maxsize=5)
        self.__task_queue["publish_channel"] = Queue(maxsize=5)
        self.__task_queue["run_diagnostics"] = Queue(maxsize=5)
        self.__task_queue["browse_fs"] = Queue()
        self.__task_queue["delete_file"] = Queue(maxsize=3)
        self.__task_queue["fulfillRequest"] = Queue(maxsize=5)
        self.__task_queue["get_cpu_stats"] = Queue()
        self.__task_queue["get_memory_stats"] = Queue()
        self.__task_queue["get_system_stats"] = Queue()
        self.__task_queue["get_system_time"] = Queue()
        self.__task_queue["force_gc"] = Queue()
        self.__task_queue["reboot_system"] = Queue()
        self.__task_queue["schedule_update"] = Queue()
        self.__task_queue["get_software_version"] = Queue()
        
        
        self.__rulesmanager = None
        
        for rpc_task in self.__task_queue:
            tornado.ioloop.IOLoop.current().spawn_callback(self.__task_processor, rpc_task)
        pass
    
    
    
    @property    
    def rulesmanager(self):
        return self.__rulesmanager
        
    
    
    @rulesmanager.setter
    def rulesmanager(self, __rulesmanager):
        self.__rulesmanager = __rulesmanager
    
    
    
    
    async def addTask(self, task, responder):
        
        methodname = task["method"]
        
        if(methodname in self.__task_queue and hasattr(self, methodname) and callable(getattr(self, methodname))):
            task["responder"] = responder # reference to invoking channel
            task_queue = self.__task_queue[methodname]
            await task_queue.put(task)
        else:
            raise RuntimeError("No method by the name " + methodname + " exists")
        pass
    
    
    
    
    
    '''
        Task Queue Processor - (Per Task)
    '''
    async def __task_processor(self, topic):
        while True:
            
            if not topic in self.__task_queue:
                break
            
            task_queue = self.__task_queue[topic]
            
            response = None
            responder = None
        
            try:
                task_definition = await task_queue.get()
                
                requestid = task_definition["requestid"]
                methodname = task_definition["method"]
                args = task_definition["params"]
                responder = task_definition["responder"]
                
                method_to_call = getattr(self, methodname)
                result = await method_to_call(args)
                
                onsuccess = getattr(responder, 'onExecutionResult', None)
                if callable(onsuccess):
                    await onsuccess(requestid, result) 
                
            except Exception as e:
                
                err = "Error executing task " + str(e)                
                self.logger.debug(err)
                
                onfailure = getattr(responder, 'onExecutionerror', None)
                if callable(onfailure):
                    await onfailure(requestid, e)
                
            finally:
                task_queue.task_done()
        pass
    
    
    
    '''
        Runs system diagnostics and generates report
    '''
    async def run_diagnostics(self, params=None):
        
        self.logger.debug("run diagnostics")
        
        __sysmon = None
        
        if self.__system_modules.hasModule("sysmon"):
            __sysmon = self.__system_modules.getModule("sysmon")
            
        if(__sysmon != None):        
            return await __sysmon.run_system_diagnostics()
        else:
            raise ModuleNotFoundError("`sysmon` module does not exist")
        pass
    
    
    
    
    '''
        Publishes message to channel
        
        Payload content =>
        topicname : The topic name to publish message at 
        message : A arbitrary string
    '''
    async def publish_channel(self, params):
        self.logger.debug("publish channel")
        
        __pubsubhub = None
        
        if self.__system_modules.hasModule("pubsub"):
            __pubsubhub = self.__system_modules.getModule("pubsub")
        
        if(__pubsubhub != None):
            handler = params[0] 
            topicname = params[1]  
            message = params[2]        
            __pubsubhub.publish(topicname, message, handler)
        pass
    
    
    
    '''
        Creates a channel
        
        Payload content =>
        channel_info : channel info object (JSON) containing parameters to create new channel
        {name=<topicname>, type=<topictype>, queue_size=<queue_size>, max_users=<max_users>}
    '''        
    async def create_channel(self, params):
        self.logger.debug("create channel")
        
        __pubsubhub = None
        
        if self.__system_modules.hasModule("pubsub"):
            __pubsubhub = self.__system_modules.getModule("pubsub")
            
        if(__pubsubhub != None):
            channel_info = params[0]  
            channel_info['type'] = "bidirectional"      
            __pubsubhub.createChannel(channel_info)
        else:
            raise ModuleNotFoundError("`PubSub` module does not exist")
        pass
    
    
    
    
    '''
        Removes a channel
        
        Payload content =>
        topicname : The topic name to remove 
    '''
    async def remove_channel(self, params):
        self.logger.debug("remove channel")
        
        __pubsubhub = None
        
        if self.__system_modules.hasModule("pubsub"):
            __pubsubhub = self.__system_modules.getModule("pubsub")
        
        if(__pubsubhub != None):
            channel_name = params[0]        
            __pubsubhub.removeChannel(channel_name)
        else:
            raise ModuleNotFoundError("`PubSub` module does not exist")
        pass
    
    
    
    
    
    
    '''
        subscribes to a channel
        
        Payload content =>
        topicname : The topic name to remove 
    '''
    async def subscribe_channel(self, params):
        self.logger.debug("subscribe topic")
        
        __pubsubhub = None
        
        if self.__system_modules.hasModule("pubsub"):
            __pubsubhub = self.__system_modules.getModule("pubsub")
        
        if(__pubsubhub != None):
            handler = params[0]
            topic = params[1]
            # finalparams = params.copy() 
            #if(len(finalparams)>1):
            #    finalparams = finalparams[2:]
            __pubsubhub.subscribe(topic, handler)
        else:
            raise ModuleNotFoundError("`PubSub` module does not exist")
        pass
    
    
    
        '''
        unsubscribes from a channel
        
        Payload content =>
        topicname : The topic name to unsubscribe from 
    '''
    async def unsubscribe_channel(self, params):
        self.logger.debug("unsubscribe topic")
        
        __pubsubhub = None
        
        if self.__system_modules.hasModule("pubsub"):
            __pubsubhub = self.__system_modules.getModule("pubsub")
        
        if(__pubsubhub != None):
            handler = params[0]
            topic = params[1]       
            __pubsubhub.unsubscribe(topic, handler)
        else:
            raise ModuleNotFoundError("`PubSub` module does not exist")
        pass
    
    
    
    
    
    '''
        Starts the target delegate
        
        Payload content => NONE 
    '''
    async def start_target(self, params):
        self.logger.debug("start target")
        
        if self.__system_modules.hasModule("target_delegate"):
            __delegate = self.__system_modules.getModule("target_delegate")
            await __delegate.start_proc()
        else:
            raise ModuleNotFoundError("`TargetDelegate` module does not exist")
        pass
    
    
    
    
    
    '''
        Stops the target delegate
        
        Payload content => NONE 
    '''
    async def stop_target(self, params):
        self.logger.debug("stop target")
        
        if self.__system_modules.hasModule("target_delegate"):
            __delegate = self.__system_modules.getModule("target_delegate")
            await __delegate.stop_proc()
        else:
            raise ModuleNotFoundError("`TargetDelegate` module does not exist")
        pass
    
    
    
    
    
    
    '''
        Restarts the target delegate
        
        Payload content => NONE 
    '''
    async def restart_target(self, params):
        self.logger.debug("restart target")
        
        __delegate = None
        if self.__system_modules.hasModule("target_delegate"):
            __delegate = self.__system_modules.getModule("target_delegate")
            await __delegate.restart_proc()
        else:
            raise ModuleNotFoundError("`TargetDelegate` module does not exist")
        pass
    
    
    
    
    
    
    '''
        Calls arbitrary method in TargetDelegate impl
        
        Payload content =>
        command : method name to invoke
        params : arbitrary array of parameters  
    '''
    async def fulfillRequest(self, params):
        self.logger.debug("custom RPC call")
        
        __delegate = None
        
        if self.__system_modules.hasModule("target_delegate"):
            __delegate = self.__system_modules.getModule("target_delegate")
            
        if(__delegate != None):
            if(len(params)<1):
                raise Exception("Minimum of one parameter is required for this method call")
            
            handler = params[0]
            command = str(params[1])
            self.logger.debug(command)
            finalparams = params.copy()
            finalparams = finalparams[2:]
            return await __delegate.fulfillRequest(command, finalparams)
        else:
            raise ModuleNotFoundError("`TargetDelegate` module does not exist")
        pass
    
    
    
    
    
    
    
        '''
        Calls arbitrary method in TargetDelegate impl
        
        Payload content =>
        command : method name to invoke
        params : arbitrary array of parameters  
        '''
        def fulfillRequest_sync(self, params):
            self.logger.debug("custom RPC call")
            
            __delegate = None
            
            if self.__system_modules.hasModule("target_delegate"):
                __delegate = self.__system_modules.getModule("target_delegate")
                
            if(__delegate != None):
                if(len(params)<1):
                    raise Exception("Minimum of one parameter is required for this method call")
                
                handler = params[0]
                command = str(params[1])
                self.logger.debug(command)
                finalparams = params.copy()
                finalparams = finalparams[2:]
                return __delegate.fulfillRequest_sync(command, finalparams)
            else:
                raise ModuleNotFoundError("`TargetDelegate` module does not exist")
            pass
    
    
    
    
    
    
    
    '''
        Gets filesystem listing for a specified path. 
        of target delegate.
        
        Payload content =>
        path : Path to scan for files and folders.Path should be a sub path within the access scope.  
    '''
    async def browse_fs(self, params):
        self.logger.info("browse filesystem")
        
        __filemanager = None
        
        if self.__system_modules.hasModule("file_manager"):
            __filemanager = self.__system_modules.getModule("file_manager")
        
        if(__filemanager != None):
            handler = params[0]
            path = str(params[1])
            result = await __filemanager.browse_content(path)
            return result
        else:
            raise ModuleNotFoundError("`FileManager` module does not exist")
        pass
    
    
    
    
    
    
    '''
        delete file from a specified path.
        
        Payload content =>
        path : Path of file to delete.  
    '''
    async def delete_file(self, params):
        self.logger.info("delete file")
        
        __filemanager = None
        
        if self.__system_modules.hasModule("file_manager"):
            __filemanager = self.__system_modules.getModule("file_manager")
        
        if(__filemanager != None):
            handler = params[0]
            path = str(params[1])
            result = await __filemanager.deleteFile(path)
            return result
        else:
            raise ModuleNotFoundError("`FileManager` module does not exist")
        pass
    
    
    
    
    
    '''
        Starts recording of a log file by creating a log record rule in reaction engine
        
        Payload content =>
        logname : The name of the log file
    '''
    async def start_log_recording(self, params):
        self.logger.debug("start_log_recording")
        
        __logmon = None
        
        if self.__system_modules.hasModule("log_monitor"):
            __logmon = self.__system_modules.getModule("log_monitor")
        else:
            raise ModuleNotFoundError("`LogMon` module does not exist")
        
        handler = params[0]
        
        if self.__rulesmanager is not None:
            log_name = params[1]  
            log_info = __logmon.getLogInfo(log_name)
            
            if hasattr(handler, 'id'):
                rule_id = handler.id + '-' + log_name
                topic_path = log_info["topic_path"]                
                topic_path = topic_path.replace("logging", "logging/chunked") if 'logging/chunked' not in topic_path else topic_path
                filepath = log_info["log_file_path"]
                    
                rule = buildLogWriterRule(rule_id, topic_path, filepath)
                if self.__rulesmanager.hasRule(rule_id):
                    raise RulesError('Rule for id ' + rule_id + 'already exists')
                else:
                    self.__rulesmanager.registerRule(rule)
                    handler.liveactions['logrecordings'].add(rule_id) # store reference on client WebSocket handler
                    return rule_id
        pass
    
    
    
    
    
    
    '''
        Stops an ongoing recording of a log file by removing a log record rule in reaction engine
        
        Payload content =>
        logname : The name of the log file
    '''
    async def stop_log_recording(self, params):
        
        self.logger.debug("stop_log_recording")
        
        handler = params[0]
                
        if self.__rulesmanager is not None:
            rule_id = params[1]
            if hasattr(handler, 'id'):                                
                if self.__rulesmanager.hasRule(rule_id):
                    self.__rulesmanager.deregisterRule(rule_id)
                    if rule_id in handler.liveactions['logrecordings']:
                        handler.liveactions['logrecordings'].remove(rule_id) # remove reference on client WebSocket handler
                        return
        else:
            raise ModuleNotFoundError("No rules manager assigned")    
        
        
        

    async def get_cpu_stats(self, params):
        self.logger.debug("get cpu statss")
        
        __sysmon = None
        
        if self.__system_modules.hasModule("sysmon"):
            __sysmon = self.__system_modules.getModule("sysmon")
            
        if(__sysmon != None):        
            result =  __sysmon.getCPUStats()
            await asyncio.sleep(.5)
            return result
        else:
            raise ModuleNotFoundError("`sysmon` module does not exist")
        pass
    
    
    
    
    
    async def get_memory_stats(self, params):
        self.logger.debug("get cpu statss")
        
        __sysmon = None
        
        if self.__system_modules.hasModule("sysmon"):
            __sysmon = self.__system_modules.getModule("sysmon")
            
        if(__sysmon != None):        
            result =  __sysmon.getMemorytats()
            await asyncio.sleep(.5)
            return result
        else:
            raise ModuleNotFoundError("`sysmon` module does not exist")
        pass
    
    
    
    
    async def force_gc(self, params):
        self.logger.debug("force gc")
        
        __sysmon = None
        
        if self.__system_modules.hasModule("sysmon"):
            __sysmon = self.__system_modules.getModule("sysmon")
            
        if(__sysmon != None):        
            __sysmon.force_gc()
            await asyncio.sleep(.5)
            return
        else:
            raise ModuleNotFoundError("`sysmon` module does not exist")
        pass
    
    
    
    
    async def get_system_stats(self, params):
        self.logger.debug("get cpu statss")
        
        __sysmon = None
        
        if self.__system_modules.hasModule("sysmon"):
            __sysmon = self.__system_modules.getModule("sysmon")
            
        if(__sysmon != None):        
            result =  __sysmon.getLastSystemStats()
            await asyncio.sleep(.5)
            return result
        else:
            raise ModuleNotFoundError("`sysmon` module does not exist")
        pass
    
    
    
    
    async def get_system_time(self, params):
        self.logger.debug("get cpu statss")
        
        __sysmon = None
        
        if self.__system_modules.hasModule("sysmon"):
            __sysmon = self.__system_modules.getModule("sysmon")
            
        if(__sysmon != None):        
            result =  __sysmon.getSystemTime()
            await asyncio.sleep(.5)
            return result
        else:
            raise ModuleNotFoundError("`sysmon` module does not exist")
        pass
    
    
    
    async def reboot_system(self, params):
        self.logger.debug("reboot system")
        
        __sysmon = None
        
        if self.__system_modules.hasModule("sysmon"):
            __sysmon = self.__system_modules.getModule("sysmon")
            
        if(__sysmon != None):        
            result =  __sysmon.rebootSystem()
            await asyncio.sleep(.5)
            return result
        else:
            raise ModuleNotFoundError("`sysmon` module does not exist")
        pass
    
    
    
    
    async def schedule_update(self, params):
        self.logger.debug("schedule update")
        
        __sysmon = None
        
        if self.__system_modules.hasModule("file_manager"):
            __file_manager = self.__system_modules.getModule("file_manager")
            if(__file_manager != None):
                #__updater_script = await __file_manager.get_updater_script()
                if self.__system_modules.hasModule("sysmon"):
                    __sysmon = self.__system_modules.getModule("sysmon")
                    if(__sysmon != None):
                        return __sysmon.schedule__update()
                else:
                    raise ModuleNotFoundError("`sysmon` module does not exist")
        else:
                    raise ModuleNotFoundError("`file_manager` module does not exist")
        pass
    
    
    
    
    async def get_software_version(self, params=None):
        self.logger.debug("get software version")
        __sysmon = None
        if self.__system_modules.hasModule("sysmon"):
                __sysmon = self.__system_modules.getModule("sysmon")
                if(__sysmon != None):
                    return __sysmon.getVersion()
        else:
                raise ModuleNotFoundError("`sysmon` module does not exist")
        pass
    
    