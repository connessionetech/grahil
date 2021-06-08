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
output="$output\"os\": {" 
output="$output\"arch\": \"$(arch)\""
output="$output, \"name\": "\"$OS_NAME\"
output="$output, \"type\": \"Linux\""
output="$output, \"flavor\": "\"$OS_TYPE\"

boot_time=$(last reboot -F | head -1 | awk '{print $5,$6,$7,$8,$9}')
output="$output, \"boot_time\": "\"$boot_time\"

uptime=$(awk '{print $1}' /proc/uptime)
output="$output, \"uptime\": "\"$uptime\"

output="$output, \"version\": "\"$OS_VERSION\"
output="$output, \"datetime\": "\"$(date | awk '{print $1,$2,$3,$4,$6}')\"
output="$output, \"timezone\": "\"$(date | awk '{print $5}')\"
output="$output, \"average_load\": "\"$(uptime | awk '{print $8,$9,$10}')\"}

cpu_info=$(lscpu | awk '/^Architecture:/ {arch=$NF} /^Vendor ID:/ {vendor=$NF} /^Model name:/ {modelname=$3$4$5$6$7$8$9} /^CPU.s.:/ {cpus=$NF} /^Core.s. per socket:/ {cpus_per_socket=$NF} /^CPU MHz:/ {cpu_frequency=$NF} END {printf "{\"frequency\": %s, \"count\": %s, \"vendor\": \"%s\", \"model\": \"%s\"", cpu_frequency, cpus, cpus_per_socket, arch, vendor, modelname}')
cpu_percent=", \"percent\": \"0%\"}"
cpu_info="$cpu_info$cpu_percent"
output="$output, \"cpu\": $cpu_info"

mem_info=$(free | awk 'NR==2{printf "{\"total\":%s, \"used\":%s,\"free\":%s, \"shared\":%s, \"buff_cache\":%s, \"available\":%s, \"percent\":%s, ", $2,$3,$4,$5,$6,$7,$3/$2 * 100.0} NR==3{printf "\"swap_total\":%s, \"swap_used\":%s,\"swap_free\":%s}", $2,$3,$4}')
output="$output, \"memory\": $mem_info"

disk_info=$(df  --output=source,fstype,size,used,avail,pcent,target -x tmpfs -x devtmpfs |sed '1d' | awk '{printf "{\"mountpoint\":\"%s\", \"fstype\":\"%s\", \"total\":%s,\"used\":%s, \"free\":%s, \"percent\":\"%s\"},", $7,$2,$3,$4,$5,$6}')
disk_info=${disk_info::-1}
output="$output, \"disk\": [$disk_info],"

net_info=""
for inter in $(ls /sys/class/net/); do   
    net_info="$net_info{\"id\":\"$inter\", "
    info=$(ip -s -s link show dev $inter | awk 'NR==4{printf "\"bytes_recv\": %s, \"packets_recv\": %s, \"errin\": %s, \"dropin\": %s, ", $1,$2,$3,$5} NR==8{printf "\"bytes_sent\": %s, \"packets_sent\": %s, \"errout\": %s, \"dropout\": %s},", $1,$2,$3,$5}')
    net_info="$net_info $info"
done

net_info=${net_info::-1}
output="$output\"network\": [$net_info]"
output="$output}"
echo $output