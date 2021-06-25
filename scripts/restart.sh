#!/bin/bash

# Stopping service
systemctl stop grahil.service

# Wait a little while just to make sure any config updates is in a stable state
sleep 5

# Starting service
systemctl start grahil.service