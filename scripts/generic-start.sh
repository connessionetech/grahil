#!/bin/bash


# Start service

proc=$1

if service --status-all | grep -Fq "$proc"; then    
  process_active=$(systemctl show -p ActiveState --value "$proc")

    if [ $process_active = "inactive" ]; then
        "/etc/init.d/$proc" start
    else
        echo "$proc is already active"
    fi
fi
