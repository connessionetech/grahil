#!/bin/bash


# Start prosody service
if service --status-all | grep -Fq 'prosody'; then    
  prosody_active=$(systemctl show -p ActiveState --value prosody)

    if [ $prosody_active = "inactive" ]; then
        /etc/init.d/prosody start
    else
        echo "prosody is already active"
    fi
fi



# Start jicofo service
if service --status-all | grep -Fq 'jicofo'; then    
  jicofo_active=$(systemctl show -p ActiveState --value jicofo)

    if [ $jicofo_active = "inactive" ]; then
        /etc/init.d/jicofo start
    else
        echo "jicofo is already active"
    fi
fi


# Start videobridge service
if service --status-all | grep -Fq 'jitsi-videobridge2'; then    
  jitsi_videobridge2_active=$(systemctl show -p ActiveState --value jitsi-videobridge2)

    if [ $jitsi_videobridge2_active = "inactive" ]; then
        /etc/init.d/jitsi-videobridge2 start
    else
        echo "jitsi-videobridge2 is already active"
    fi
fi



# Start nginx service
if service --status-all | grep -Fq 'nginx'; then    
  nginx_active=$(systemctl show -p ActiveState --value nginx)

    if [ $nginx_active = "inactive" ]; then
        /etc/init.d/nginx start
    else
        echo "nginx is already active"
    fi
fi   