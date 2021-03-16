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

from oneadmin.abstracts import IModule, ISystemMonitor
from oneadmin.core.event import StatsGeneratedEvent, StatsErrorEvent
from oneadmin.core.constants import TOPIC_SYSMONITORING
from oneadmin.version import __version__

import psutil
import logging
import tornado
import platform
import datetime
import os
import gc
import json

from typing import Dict, Text
from tornado.concurrent import asyncio
from time import time
from tornado.httpclient import AsyncHTTPClient
from builtins import str
from apscheduler.executors.pool import ThreadPoolExecutor
import socket




class SystemMonitor(IModule, ISystemMonitor):
    
    
    NAME = "sysmon"
    
    
    THREADPOOL = ThreadPoolExecutor(5)
    
    
    def __init__(self, config):
        '''
        Constructor
        '''
        
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__config = config
        
        ''' To refactor'''
        
        self.__current_milli_time = lambda: int(round(time() * 1000))
        self.__last_stats = None
        self.__bw_usage_per_second = None
        self.__external_ip = None      
    pass




    def initialize(self) ->None:
        self.logger.info("Module init")
        self.start_monitor()
        pass



    def getname(self) ->Text:
        return SystemMonitor.NAME



    '''
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
    '''    


    
    def start_monitor(self) -> None:
        tornado.ioloop.IOLoop.current().spawn_callback(self.__generateSystemStats)
    pass

    
    

    async def __cpu_percent(self, interval = None, *args, **kwargs):
        if interval is not None and interval > 0.0:
            psutil.cpu_percent(*args, **kwargs)
            await asyncio.sleep(interval)
        return psutil.cpu_percent(*args, **kwargs)
    
    
    
    
    def get_cpu_stats(self, cached=False) ->Dict:
        
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
    
    
    
    
    def get_memory_stats(self, unit = "b", cached=False) ->Dict:
        
        if cached == False:
            
            virtual_memory = psutil.virtual_memory()
            total_virtual_mem = virtual_memory.total
            used_virtual_mem = virtual_memory.used
            free_virtual_mem = virtual_memory.free
            percent_virtual_mem = virtual_memory.percent 
            
            return{
                "total_virtual_mem": self.__valueAsPerUnit(total_virtual_mem, unit),
                "used_virtual_mem": self.__valueAsPerUnit(used_virtual_mem, unit),
                "free_virtual_mem":self.__valueAsPerUnit(free_virtual_mem, unit),
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
    Force GC
    '''
    def force_gc(self) ->None:
        gc.collect()
        pass
    
    
    
    
        
    '''
    get version from version.py
    '''
    def get_version(self) ->str:
        return __version__
        pass
    
    
    
    
    
    '''
    Last generated system stats
    '''
    def get_last_system_stats_snapshot(self) ->Dict:
        return self.__last_stats
        pass
    
    
    
    
    '''
    Last generated system stats
    '''
    def get_system_time(self) ->str:
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
    async def __generateSystemStats(self):
        
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
                
                
                part_disk_usage = self.__getPartitionsInfo(unit)
                    
                # connection info    
                net_connection_info =  self.__get_connection_info(self.__config["net_connection_filter"])
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
                                "total_virtual_mem": self.__valueAsPerUnit(total_virtual_mem, unit),
                                "used_virtual_mem": self.__valueAsPerUnit(used_virtual_mem, unit),
                                "free_virtual_mem":self.__valueAsPerUnit(free_virtual_mem, unit),
                                "percent_virtual_mem":percent_virtual_mem
                            },
                            "disk_info":{
                                "mount_point": "/",
                                "total_disk_space": self.__valueAsPerUnit(total_disk_space, unit),
                                "used_disk_space":self.__valueAsPerUnit(used_disk_space, unit),
                                "free_disk_space":self.__valueAsPerUnit(free_disk_space, unit),
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
                    if err:
                        evt = StatsErrorEvent(TOPIC_SYSMONITORING, {"message": err})
                    else:
                        evt = StatsGeneratedEvent(TOPIC_SYSMONITORING, stats)
                        
                    await self.dispatchevent(evt)
                        
                except Exception as e:
                    err = "An error occurred in generating system stats " + str(e)
                    self.logger.warning(err)

                finally:
                    wait_duration = self.__config['snapshot_interval_seconds']
                    await asyncio.sleep(wait_duration)
    
    
    
    def __valueAsPerUnit(self, value, unit="b"):
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
                    
                    
                    
    
    def __get_connection_info(self, connection_filter="all"):
        
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
    
    
    
    
    
    '''
        Get partition info
    '''
    def __getPartitionsInfo(self, unit="b"):
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
                "total": self.__valueAsPerUnit(partition_data.total, unit),
                "used": self.__valueAsPerUnit(partition_data.used, unit),
                "free": self.__valueAsPerUnit(partition_data.free, unit),
                "percent": partition_data.percent
            } 
            
            part_disk_usage.append(data)
            
        return part_disk_usage
    



    '''
        Collects individual stats of each network interface
    '''
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
        
        
        
    
    
    '''
        Checks bandwidth usage every second apart to calculate bw usage per second. This method much be called period manner internally  
    '''
    async def __calculate_network_usage(self):
        
        net_io = psutil.net_io_counters()
        old_usage = 0
        new_usage = 0
        net_usage = 0
        
        while True:
            new_usage = net_io.bytes_sent + net_io.bytes_recv
            if old_usage != 0:
                net_usage = new_usage - old_usage
                self.__bw_usage_per_second = net_usage
            
            await asyncio.sleep(1)
    
    
    
    
    '''
        Gives the average system load in last 1, 5 and 15 minutes as a tuple. The load represents the processes which are in a runnable state, either using the CPU or waiting to use the CPU (e.g. waiting for disk I/O). 
    '''
    def get_avg_load(self):
        return psutil.getloadavg()
        
        



    
    '''
        Check async to see if port is open at given address
    '''    
    async def check_port(self, host="127.0.0.1", port):
        return await tornado.ioloop.IOLoop.current().run_in_executor(SystemMonitor.THREADPOOL, self.__check_port, host, port)
        pass
    
    


    

    '''
        Check to see if port is open at given address
    '''
    def __check_port(self, host="127.0.0.1", port):
        
        a_socket = None
        
        try:
            a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            a_socket.settimeout(2)       
            location = (host, port)
            result = a_socket.connect_ex(location)
            
            if result == 0:
                return True
            else:
                return False
        
        except Exception as e:
            self.logger.error("Error checking port %s. cause %s", str(port), str(e)) 
        
        finally:
            if a_socket != None:
                a_socket.close()
                
                
                
    
    '''
     Returns task manager view consisting of list of all processes with necessary stats per process
    '''
    def get_task_manager_view(self):
        
        # Iterate over all running process
        processes:list = []
        
        for proc in psutil.process_iter():
            
            try:
                # Get process name & pid from process object.
                pInfo:Dict = proc.as_dict(attrs=['pid', 'name', 'cpu_percent', 'create_time', 'memory_info', 'username'])
                pInfo['vms'] = proc.memory_info().vms / (1024 * 1024)
                processes.append(pInfo)
            
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                
                self.logger.error("Error getting process info for proc." + proc + " cause %s", str(e))
                
            
        return processes
                
    
    
    
    
    
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
    
    