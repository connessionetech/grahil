#!/bin/bash


# Restart service

proc=$1

if service --status-all | grep -Fq "$proc"; then  
    "/etc/init.d/$proc" restart    
fi
