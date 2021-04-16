#!/bin/bash


# Stop service

proc=$1

if service --status-all | grep -Fq "$proc"; then    
  process_active=$(systemctl show -p ActiveState --value "$proc")

    if [ $process_active = "active" ]; then
        "/etc/init.d/$proc" stop
    else
        echo "$proc is already inactive"
    fi
fi
