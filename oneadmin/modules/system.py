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

from oneadmin.core.abstracts import IModule, ISystemMonitor
from oneadmin.core.event import StatsDataEvent, StatsErrorEvent
from oneadmin.core.constants import TOPIC_STATS
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
from tornado.process import Subprocess
from settings import settings
import signal
import subprocess





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
        
        self.__script_dir = settings["scripts_folder"]
        
        ''' To refactor'''
        
        self.__current_milli_time = lambda: int(round(time() * 1000))
        self.__last_stats = None
        self.__bw_usage_per_second = None
        self.__notify_snapshot_event = True if self.__config["snapshot_interval_seconds"] > 0 else False
        self.__external_ip = None      
    pass




    
    def initialize(self) ->None:
        self.logger.info("Module init")
        tornado.ioloop.IOLoop.current().spawn_callback(self.__generateSystemStats)
        pass



    
    
    def getname(self) ->Text:
        return SystemMonitor.NAME
  


    
    
    
    async def __cpu_percent(self, interval = None, *args, **kwargs):
        if interval is not None and interval > 0.0:
            psutil.cpu_percent(*args, **kwargs)
            await asyncio.sleep(interval)
        return psutil.cpu_percent(*args, **kwargs)
    
    
    
    
    
    async def get_system_stats_via_shell(self):
        
        script_path = os.path.join(self.__script_dir, "sys.sh")
        
        bashCommand = "bash " + script_path
        proc = Subprocess(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        await proc.wait_for_exit()
        output = proc.stdout.read()
        stats = output.decode('UTF-8').strip()
        response = json.loads(stats)
        return response
    
    
    
    async def get_system_stats_via_extlib(self, unit = "b"):
        
        now = datetime.datetime.now()
        local_now = now.astimezone()
        local_tz = local_now.tzinfo
        local_tzname = local_tz.tzname(local_now)
        readable_date_time = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
        time_now= self.__current_milli_time()
        
        ''' System information '''
        machine_type = platform.machine()
        machine_processor = platform.processor()
        
        os_type = platform.system()
        os_name = platform.linux_distribution()[0]
        os_version = platform.linux_distribution()[1]
        os_release = platform.release();
        boot_time = psutil.boot_time()
        uptime = time() - psutil.boot_time()
        
        os_flavor = platform.release()
        
        avgload=psutil.getloadavg()
        
        
        cpu_count = psutil.cpu_count()
        cpu_frequency = psutil.cpu_freq().current
        cpu_vendor = "NA"
        cpu_model = "NA"
        cpu_percent = await self.__cpu_percent() #await self.__cpu_percent(1)
        
        virtual_memory = psutil.virtual_memory()
        total_virtual_mem = virtual_memory.total
        used_virtual_mem = virtual_memory.used
        free_virtual_mem = virtual_memory.free
        percent_virtual_mem = virtual_memory.percent  
        
        swap_memory = psutil.swap_memory()
        total_swap_mem = swap_memory.total 
        used_swap_mem = swap_memory.used
        free_swap_mem = swap_memory.free
        
        
        return {
            "os":{
                "arch":machine_type,
                "name": os_name,
                "type": os_type,
                "flavor": os_flavor,
                "version": os_version,
                "boot_time": boot_time,
                "uptime": uptime,
                "datetime":readable_date_time,
                "timezone": local_tzname,
                "average_load": avgload
            },
            "cpu": {
                "frequency": cpu_frequency,
                "count": cpu_count,
                "vendor": cpu_vendor,
                "model": cpu_model,
                "percent":cpu_percent
            },
            "memory":{
                "total": total_virtual_mem,
                "used": used_virtual_mem,
                "free": free_virtual_mem,
                "percent":percent_virtual_mem,
                "swap_total": total_swap_mem,
                "swap_used": used_swap_mem,
                "swap_free": free_swap_mem
            },
            "disk": self.__getPartitionsInfo(),
            "network": self.__get_nic_info(),
            "timestamp": self.__current_milli_time()
        }
    
    
    
    
    def get_cpu_stats(self, cached=False) ->Dict:
        
        cpu_info = self.__last_stats["system"]["stats"]["cpu"]
        return{
            "count" : cpu_info["count"],
            "percent" : cpu_info["percent"],
            "timestamp" : self.__last_stats["system"]["timestamp"]
        }
    
    
    
    
    def get_memory_stats(self, unit = "b") ->Dict:
        
        mem_info = self.__last_stats["system"]["stats"]["memory"]
        return{
            "total": mem_info["total"],
            "used": mem_info["used"],
            "free":mem_info["free"],
            "percent":mem_info["percent"],
            "timestamp" : self.__last_stats["system"]["timestamp"]
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
        return self.__last_stats["system"]["os"]["datetime"] if 'datetime' in self.__last_stats["system"]["os"] else datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
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
    async def __generateSystemStats(self, unit = "b"):
        
        err = None
        stats = {
                    "system":None,
                    "target":None
                }
        
        while True:
            
            try:
                data = None
                
                if "stats_via_shell" in self.__config and self.__config["stats_via_shell"] == True:
                    data = await self.get_system_stats_via_shell()
                else:
                    data = await self.get_system_stats_via_extlib()
                                    
                
                system_datetime = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
                
                ''' System information '''
                os_arch = data["os"]["arch"]
                os_flavor = data["os"]["flavor"]
                os_type = data["os"]["type"]
                os_name = data["os"]["name"]
                os_version = data["os"]["version"]
                boot_time = data["os"]["boot_time"]
                uptime = data["os"]["uptime"]
                system_datetime = data["os"]["datetime"]
                timezone = data["os"]["timezone"]
                average_load = data["os"]["average_load"]
                        
                cpu_count = data["cpu"]["count"]                
                cpu_frequency = data["cpu"]["frequency"]
                cpu_vendor = data["cpu"]["vendor"]
                cpu_model = data["cpu"]["model"]
                cpu_percent = data["cpu"]["percent"]
                
                total_mem = data["memory"]["total"]
                used_mem = data["memory"]["used"]
                free_mem = data["memory"]["free"]
                percent_mem = data["memory"]["percent"]
                
                total_swap_mem = data["memory"]["swap_total"]
                used_swap_mem = data["memory"]["swap_used"]
                free_swap_mem = data["memory"]["swap_free"]
                
                disk_usage = data["disk"]
                nic_stats = data["network"]
                    
                    
                '' 'Building stats'''
                stats = None
                
                
                ''' Data about the system '''
                
                system_stats = None
                system_stats =  {
                        "os":{
                            "arch":os_arch,
                            "os_name": os_name,
                            "os_type": os_type,
                            "os_flavor": os_flavor,
                            "os_version": os_version,
                            "boot_time": boot_time,
                            "uptime": uptime,
                            "system_datetime":system_datetime,
                            "timezone": timezone,
                            "average_load": average_load
                        },
                        "meta_info":{
                        },
                        "cpu":{
                                "cpu_frequency": cpu_frequency,
                                "cpu_count": cpu_count,
                                "cpu_vendor": cpu_vendor,
                                "cpu_model": cpu_model,
                                "cpu_percent":cpu_percent

                        },
                        "memory":{
                                "total": total_mem,
                                "used": used_mem,
                                "free": free_mem,
                                "percent":percent_mem,
                                "swap":{
                                    "total": total_swap_mem,
                                    "used": used_swap_mem,
                                    "free": free_swap_mem
                                }
                        },
                        "disk":disk_usage,
                        "network":nic_stats
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
                        evt = StatsErrorEvent(TOPIC_STATS, error=err)
                    else:
                        evt = StatsDataEvent(TOPIC_STATS, stats)
                    
                    if self.__notify_snapshot_event:
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
    
    
    
    
    
    
    def __get_nic_info(self, unit="b"):
        
        nic_stats = []
        if self.__config["nic_stats_per_nic"] == True:
            net_io = psutil.net_io_counters(pernic=True)
        else:
            net_io = psutil.net_io_counters()
         
        
        if isinstance(net_io, dict):
                                
            for key,val in net_io.items():
                stats = self.__collect_nic_stats(key, val)
                nic_stats.append(stats)
            pass
        else:
            stats = self.__collect_nic_stats("aggregated", net_io)
            nic_stats.append(stats)
        
        return nic_stats
    



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
    async def check_port(self, port, host="127.0.0.1"):
        return await tornado.ioloop.IOLoop.current().run_in_executor(SystemMonitor.THREADPOOL, self.__check_port, host, port)
        pass
    
    


    

    '''
        Check to see if port is open at given address
    '''
    def __check_port(self, host, port):
        
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
    
    