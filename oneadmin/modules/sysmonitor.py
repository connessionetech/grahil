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

import psutil
from tornado.concurrent import asyncio
from time import time
import logging
import tornado
import platform
import datetime
import os
import gc
import json
from pathlib import Path

from crontab import CronTab
from oneadmin.version import __version__
from tornado.httpclient import AsyncHTTPClient
from abstracts import IEventDispatcher

class SystemMonitor(IEventDispatcher):
    
    def __init__(self, config, modules):
        '''
        Constructor
        '''
        
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__config = config
        
        ''' To refactor'''
        self.__delegate = modules.getModule("target_delegate")
        self.__filemanager = modules.getModule("file_manager")
        self.__logmonitor = modules.getModule("log monitor")
        self.__presenter = modules.getModule("presenter")
        ''' --- '''
        
        self.__callback = None
        self.__current_milli_time = lambda: int(round(time() * 1000))
        self.__last_stats = None
        self.__external_ip = None
        
        # must specify logged in user in config for contab to work
        self.__crontab = CronTab(user=config["system_user"]) if "system_user" in config else True 
        tornado.ioloop.IOLoop.current().spawn_callback(self.__discoverHost)        
    pass




    async def __discoverHost(self):
         
        http_client = AsyncHTTPClient()
        try:
            response = await http_client.fetch("http://ip.jsontest.com/")
            data = json.loads(response.body)
            self.__external_ip = data["ip"]
            self.logger.info("IP = %s", self.__external_ip)
        except Exception as e:
            err = "An error occurred in discovering public IP " + str(e)
            self.logger.warning(err)
        


    
    def start_monitor(self):
        tornado.ioloop.IOLoop.current().spawn_callback(self.generateSystemStats)
    pass


    
    @property
    def callback(self):
        return self.__callback
    
    
    @callback.setter
    def callback(self, fun):
        self.__callback = fun

    

    async def __cpu_percent(self, interval = None, *args, **kwargs):
        if interval is not None and interval > 0.0:
            psutil.cpu_percent(*args, **kwargs)
            await asyncio.sleep(interval)
        return psutil.cpu_percent(*args, **kwargs)
    
    
    
    
    def getCPUStats(self, cached=False):
        
        if cached == False:
            return{
                "cpu_count" : psutil.cpu_count(),
                "cpu_percent" : psutil.cpu_percent(),
                "timestamp" : self.__current_milli_time()
                }
        else:
            cpu_info = self.__last_stats["system"]["stats"]["cpu_info"]
            return{
                "cpu_count" : cpu_info["cpu_count"],
                "cpu_percent" : cpu_info["cpu_percent"],
                "timestamp" : self.__last_stats["system"]["time"]
                }
        
        pass
    
    
    
    
    def getMemorytats(self, unit = "b", cached=False):
        
        if cached == False:
            
            virtual_memory = psutil.virtual_memory()
            total_virtual_mem = virtual_memory.total
            used_virtual_mem = virtual_memory.used
            free_virtual_mem = virtual_memory.free
            percent_virtual_mem = virtual_memory.percent 
            
            return{
                "total_virtual_mem": self.valueAsPerUnit(total_virtual_mem, unit),
                "used_virtual_mem": self.valueAsPerUnit(used_virtual_mem, unit),
                "free_virtual_mem":self.valueAsPerUnit(free_virtual_mem, unit),
                "percent_virtual_mem":percent_virtual_mem,
                "timestamp" : self.__current_milli_time()
                }
        else:
            mem_info = self.__last_stats["system"]["stats"]["memory_info"]
            return{
                "total_virtual_mem": mem_info["total_virtual_mem"],
                "used_virtual_mem": mem_info["used_virtual_mem"],
                "free_virtual_mem":mem_info["free_virtual_mem"],
                "percent_virtual_mem":mem_info["percent_virtual_mem"],
                "timestamp" : self.__last_stats["system"]["time"]
                }
        
        pass
    
    
    
    
    
    '''
    Schedules updater script for execution -> N minutes from now and returns
    '''
    def schedule__update(self, updater_script):
        
        self.__crontab.remove_all(comment='updater')
        sch_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
        
        os.chmod(updater_script, 0o755)
        
        args = ""
        if "updater_cron_tab_args" in self.__config:
            args = self.__config["updater_cron_tab_args"]
        
        cmd = str(updater_script) + " " + str(args)
        self.logger.info("Setting : %s for crontab", cmd)
        
        job = self.__crontab.new(command=cmd)
        job.setall(sch_time)
        job.set_comment("updater")
        self.__crontab.write()
        return sch_time.strftime("%m/%d/%Y, %H:%M:%S")
    
    
    
    '''
    Force GC
    '''
    def force_gc(self):
        gc.collect()
        pass
    
    
    
    
        
    '''
    get version from version.py
    '''
    def getVersion(self):
        return __version__
        pass
    
    
    
    
    
    '''
    Last generated system stats
    '''
    def getLastSystemStats(self):
        return self.__last_stats
        pass
    
    
    
    
    '''
    Last generated system stats
    '''
    def getSystemTime(self):
        return self.__last_stats['system_datetime'] if 'system_datetime' in self.__last_stats else datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
        pass
    
    
    
    '''
    Reboot system
    '''
    def rebootSystem(self):
        #os.system("shutdown /r /t 1") 
        os.popen("shutdown -r -t 05")
        pass
    
    
    
    
    '''
    Generates stats snapshot
    '''
    async def generateSystemStats(self):
        
        err = None
        stats = {
                    "system":None,
                    "target":None
                }
        
        while True:
            
            try:
                readable_date_time = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
                time_now= self.__current_milli_time()
                unit = "b"
                
                ''' System information '''
                machine_type = platform.machine()
                machine_processor = platform.processor()
                
                os_type = platform.system()
                os_name = platform.linux_distribution()[0]
                os_version = platform.linux_distribution()[1]
                os_release = platform.release();
                boot_time = psutil.boot_time()
                uptime = time() - psutil.boot_time()
                        
                cpu_count = psutil.cpu_count()
                cpu_percent = await self.__cpu_percent() #await self.__cpu_percent(1)
                
                virtual_memory = psutil.virtual_memory()
                total_virtual_mem = virtual_memory.total
                used_virtual_mem = virtual_memory.used
                free_virtual_mem = virtual_memory.free
                percent_virtual_mem = virtual_memory.percent      
                
                root_disk_usage = psutil.disk_usage('/')
                total_disk_space = root_disk_usage.total
                used_disk_space = root_disk_usage.used
                free_disk_space = root_disk_usage.free
                percent_disk_space = root_disk_usage.percent
                
                
                part_disk_usage = self.getPartitionsInfo(unit)
                    
                # connection info    
                net_connection_info =  self.get_connection_info(self.__config["net_connection_filter"])
                total_net_connections = len(net_connection_info)
                # part_net_connections = None if self.__config["net_connection_count_only"] == True else net_connection_info
                
                if self.__config["nic_stats_per_nic"] == True:
                    net_io = psutil.net_io_counters(pernic=True)
                else:
                    net_io = psutil.net_io_counters()
                 
                nic_stats = []
                if isinstance(net_io, dict):
                                        
                    for key,val in net_io.items():
                        stats = self.__collect_nic_stats(key, val)
                        nic_stats.append(stats)
                    pass
                else:
                    stats = self.__collect_nic_stats("aggregated", net_io)
                    nic_stats.append(stats)
                    
                
                ''' Target information '''
                
                if(self.__delegate != None):        
                    target_name = self.__delegate.getProcName()            
                    target_is_installed = self.__delegate.is_service_installed()
                    
                    if(target_is_installed):        
                        target_version = self.__delegate.getProcVersion()
                        target_is_running = self.__delegate.is_proc_running()
                        target_is_starting = self.__delegate.is_proc_starting()
                        target_is_stopping = self.__delegate.is_proc_stopping()
                        target_stats = await self.__get_target_stats()
                        target_meta = self.__delegate.get_target_meta()
                        target_capabilities = self.__delegate.get_target_capabilities()
                    else:
                        target_version = ""
                        target_is_running = self.__delegate.is_proc_running()
                        target_is_starting = self.__delegate.is_proc_starting()
                        target_is_stopping = self.__delegate.is_proc_stopping()
                        target_stats = None
                        target_meta = None
                        target_capabilities = None
                
                
                    
                    
                '' 'Service capabilities'''
                capabilities = self.__get_capabilities()
                    
                    
                '' 'Building stats'''
                stats = None
                
                
                ''' Data about the system '''
                
                system_stats = None
                system_stats =  {
                        "arch":machine_type,
                        "processor":machine_processor,
                        "os_name": os_name,
                        "os_type": os_type,
                        "os_version": os_version,
                        "os_release": os_release,
                        "boot_time": boot_time,
                        "uptime": uptime,
                        "system_datetime":readable_date_time,
                        "capabilities":capabilities,
                        "time": time_now,
                        "unit": unit,
                        "meta_info":{
                        },
                        "stats":{
                            "cpu_info":{
                                "cpu_count": cpu_count,
                                "cpu_percent":cpu_percent
                            },
                            "memory_info":{
                                "total_virtual_mem": self.valueAsPerUnit(total_virtual_mem, unit),
                                "used_virtual_mem": self.valueAsPerUnit(used_virtual_mem, unit),
                                "free_virtual_mem":self.valueAsPerUnit(free_virtual_mem, unit),
                                "percent_virtual_mem":percent_virtual_mem
                            },
                            "disk_info":{
                                "mount_point": "/",
                                "total_disk_space": self.valueAsPerUnit(total_disk_space, unit),
                                "used_disk_space":self.valueAsPerUnit(used_disk_space, unit),
                                "free_disk_space":self.valueAsPerUnit(free_disk_space, unit),
                                "percent_disk_space":percent_disk_space,
                                "part_disk_info":part_disk_usage
                            },
                            "net_info":{
                                "total_connections": total_net_connections,
                                "nic_stats": nic_stats
                            }
                    }   
                }        
                
                ''' Data about the target process '''
                
                target_stats_data = None
                
                if(self.__delegate != None): 
                    target_stats_data = {
                            "name": target_name,
                            "version": target_version,
                            "installed": target_is_installed,
                            "is_running": target_is_running,
                            "is_starting": target_is_starting,
                            "is_stopping": target_is_stopping,
                            "meta_info":target_meta,
                            "stats":target_stats,
                            "capabilities":target_capabilities
                        }
                else:
                    target_stats_data = {
                            "name": None,
                            "version": None,
                            "installed": False,
                            "is_running": False,
                            "is_starting": False,
                            "is_stopping": False,
                            "meta_info":{
                            },
                            "stats":{
                            },
                            "capabilities":{
                            }
                        }  
                
                ''' Aggregating stats '''
                    
                stats = {
                    "system":system_stats,
                    "target":target_stats_data
                }
                
                self.__last_stats = stats
            except Exception as e:
                err = "An error occurred in generating system stats " + str(e)
                self.logger.warning(err)
            finally:
                try:
                    if self.__callback != None:
                        await self.__callback(stats, err)
                except Exception as e:
                    err = "An error occurred in generating system stats " + str(e)
                    self.logger.warning(err)

                finally:
                    wait_duration = self.__config['snapshot_interval_seconds']
                    await asyncio.sleep(wait_duration)
    
    
    
    def valueAsPerUnit(self, value, unit="b"):
        if unit == "b":
            return value
        elif unit == "kb":
            return value/1024
        elif unit == "mb":
            return (value/1024)/1024
        elif unit == "gb":
            return ((value/1024)/1024)/1024
        elif unit == "tb":
            return (((value/1024)/1024)/1024)/1024
                    
                    
                    
    def get_connection_info(self, connection_filter="all"):
        
        info = []
        connections = psutil.net_connections(connection_filter)
        
        '''
        for conn in connections:
            
            l_addr = conn.laddr.ip
            l_port = conn.laddr.port
            
            r_addr = None
            r_port = None
            
            if len(conn.raddr) > 0:
                r_addr = conn.raddr.ip
                r_port = conn.raddr.port
            
            status = conn.status
            
            info.append({
                "l_addr":l_addr,
                "l_port":l_port,
                "r_addr":r_addr,
                "r_port":r_port,
                "status":status
            })
            
            '''
    
        return connections
    

    def getPartitionsInfo(self, unit="b"):
        part_disk_usage=[]
        partitions = psutil.disk_partitions()
        for partition in partitions:
            # logging.debug("partition.mountpoint: %s" % partition.mountpoint)
            if partition.mountpoint.startswith("/snap/"):
                continue
            partition_data = psutil.disk_usage(partition.mountpoint)
            # total=21378641920, used=4809781248, free=15482871808,
            # percent=22.5
            data = {
                "mountpoint": partition.mountpoint,
                "total": self.valueAsPerUnit(partition_data.total, unit),
                "used": self.valueAsPerUnit(partition_data.used, unit),
                "free": self.valueAsPerUnit(partition_data.free, unit),
                "percent": partition_data.percent
            } 
            
            part_disk_usage.append(data)
            
        return part_disk_usage
    

    def __collect_nic_stats(self, nic_id, net_io):
    
        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv
        packets_sent = net_io.packets_sent
        packets_recv = net_io.packets_recv
        errin = net_io.errin
        errout = net_io.errout
        dropin = net_io.dropin
        dropout = net_io.dropin
        
        return {
            "id": nic_id,
            "bytes_sent":bytes_sent,
            "bytes_recv":bytes_recv,
            "packets_sent":packets_sent,
            "packets_recv":packets_recv,
            "errin":errin,
            "errout":errout,
            "dropin":dropin,
            "dropout":dropout
        }
        
    
    def __get_capabilities(self):
        return {
                    "system_stats":True,
                    "target_stats":True if self.__delegate != None else False,
                    "file_management" : False if self.__filemanager == None else True,
                    "log_monitoring" : False if self.__logmonitor == None else True,
                    "script_execution" : False
                }
    
    
    async def __get_target_stats(self):
        if(self.__delegate.is_proc_running()):
            data = None
            try:
                pids = []
                procname = self.__delegate.getPidProcName()
                process = filter(lambda p: p.name() == procname, psutil.process_iter())
                for i in process:
                    pids.append(i.pid)  
                    
                if len(pids) == 0:
                    raise ProcessLookupError("No PID found for the process name "  + procname)
                    
                
                pids.sort(reverse=True)
                pid = pids[0]
                
                ''' Resolve and set PID  for target '''
                self.__delegate.setTargetPid(pid)                
                                
                process = psutil.Process(pid)
                if(process.is_running()):
                    with process.oneshot():
                        data = {
                                "pid": process.pid,
                                "name": self.__delegate.getProcName(),
                                "created": process.create_time(),
                                "percent_cpu_used": process.cpu_percent(interval=0.0),
                                "percent_memory_used": process.memory_percent(),
                                "used_disk_space": self.__get_folder_size(self.__delegate.getRoot()),
                                "open_file_handles": len(process.open_files()),
                                "proc_data": await self.__delegate.getTargetStats()
                                }
                        
                
            except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess) as e:
                self.logger.debug("Error gathering process stats." + str(e)) 
                self.__delegate.setTargetPid(None) 
                data = {}
                
            except ProcessLookupError as e:
                self.logger.debug("Error locating process." + str(e))
                self.__delegate.setTargetPid(None)
                data = {}
        else:
            data = {     
                "pid": 0,
                "name": self.__delegate.getProcName(),
                "created": 0,
                "percent_cpu_used": 0,
                "percent_memory_used": 0,
                "used_disk_space": 0,
                "open_file_handles": 0,
                "proc_data": None
            }  
        
        return data
    
    
    
    def __get_folder_size(self, start_path = '.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
    
        return total_size
    
    
    
    def __merge_dict(self, dict1, dict2): 
        res = {**dict1, **dict2} 
        return res
    
    