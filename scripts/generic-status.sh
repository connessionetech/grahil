#!/bin/bash


# status of service

proc=$1

if service --status-all | grep -Fq "$proc"; then 
	systemctl status "$proc" | grep 'active (running)' &> /dev/null
	if [ $? == 0 ]; then
	   echo "true"
	else
	   echo "false"
	fi
fi
