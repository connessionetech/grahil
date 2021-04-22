#/bin/bash

: '
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
'

if [ -f /etc/lsb-release ]; then
    . /etc/lsb-release
    OS_NAME=$DISTRIB_ID
    OS_VERSION=$DISTRIB_RELEASE
elif [ -f /etc/debian_version ]; then
    OS_NAME=Debian  # XXX or Ubuntu??
    OS_VERSION=$(cat /etc/debian_version)
elif [ -f /etc/redhat-release ]; then
    # TODO add code for Red Hat and CentOS here
    OS_VERSION=$(rpm -q --qf "%{VERSION}" $(rpm -q --whatprovides redhat-release))
    OS_NAME=$(rpm -q --qf "%{RELEASE}" $(rpm -q --whatprovides redhat-release))
else
    OS_NAME=$(uname -s)
    OS_VERSION=$(uname -r)
fi

OS_MAJ_VERSION=${OS_VERSION%\.*}

if [[ "$OS_NAME" =~ ^(Ubuntu|Debian)$ ]]; then
    OS_TYPE="Debian"
elif [[ "$OS_NAME" =~ ^(CentOS|RedHat)$ ]]; then
    OS_TYPE="RedHat Linux"
fi

output=""

output="$output{"
output="$output\"system_info\": {" 
output="$output\"os_name\": "\"$OS_NAME\"
output="$output, \"os_type\": "\"$OS_TYPE\"
output="$output, \"os_version\": "\"$OS_VERSION\"
output="$output, \"timedate\": "\"$(date | awk '{print $1,$2,$3,$4,$6}')\"
output="$output, \"timezone\": "\"$(date | awk '{print $5}')\"
output="$output, \"uptime\": "\"$(uptime | awk '{print $1,$2,$3}')\"
output="$output, \"average_load\": "\"$(uptime | awk '{print $8,$9,$10}')\"}

cpu_info=$(lscpu | awk '/^Architecture:/ {arch=$NF} /^Vendor ID:/ {vendor=$NF} /^Model name:/ {modelname=$3$4$5$6$7$8$9} /^CPU.s.:/ {cpus=$NF} /^Core.s. per socket:/ {cpus_per_socket=$NF} /^CPU MHz:/ {cpu_frequency=$NF} END {printf "{\"cpu_frequency\": %s, \"cpu_count\": %s, \"cpus_per_socket\": %s, \"arch\": \"%s\", \"vendor\": \"%s\", \"model\": \"%s\"}", cpu_frequency, cpus, cpus_per_socket, arch, vendor, modelname}')
output="$output, \"cpu_info\": $cpu_info"

mem_info=$(free | awk 'NR==2{printf "{\"mem_total\":%s, \"mem_used\":%s,\"mem_free\":%s, \"mem_shared\":%s, \"mem_buff_cache\":%s, \"mem_available\":%s, ", $2,$3,$4,$5,$6,$7} NR==3{printf "\"swap_total\":%s, \"swap_used\":%s,\"swap_free\":%s}", $2,$3,$4}')
output="$output, \"memory_info\": $mem_info"

disk_info=$(df  --output=source,fstype,size,used,avail,pcent,target -x tmpfs -x devtmpfs |sed '1d' | awk '{printf "{\"mountpoint\":\"%s\", \"fstype\":\"%s\", \"size\":%s,\"used\":%s, \"free\":%s, \"percent\":\"%s\"},", $7,$2,$3,$4,$5,$6}')
disk_info=${disk_info::-1}
output="$output, \"disk_info\": [$disk_info],"

net_info=""
for inter in $(ls /sys/class/net/); do   
    net_info="$net_info \"$inter\":"
    info=$(ip -s -s link show dev $inter | awk 'NR==4{printf "{\"bytes_recv\": %s, \"packets_recv\": %s, \"errin\": %s, \"dropin\": %s, ", $1,$2,$3,$5} NR==8{printf "\"bytes_sent\": %s, \"packets_sent\": %s, \"errout\": %s, \"dropout\": %s},", $1,$2,$3,$5}')
    net_info="$net_info $info"
done

net_info=${net_info::-1}
output="$output\"network_info\": {$net_info}"
output="$output}"
echo $output