#!/bin/bash


# Start prosody service
if service --status-all | grep -Fq 'prosody'; then    
  prosody_active=$(systemctl show -p ActiveState --value prosody)

    if [ $prosody_active = "active" ]; then
        /etc/init.d/prosody stop
    else
        echo "prosody is already inactive"
    fi
fi



# Start jicofo service
if service --status-all | grep -Fq 'jicofo'; then    
  jicofo_active=$(systemctl show -p ActiveState --value jicofo)

    if [ $jicofo_active = "active" ]; then
        /etc/init.d/jicofo stop
    else
        echo "jicofo is already inactive"
    fi
fi


# Start videobridge service
if service --status-all | grep -Fq 'jitsi-videobridge2'; then    
  jitsi_videobridge2_active=$(systemctl show -p ActiveState --value jitsi-videobridge2)

    if [ $jitsi_videobridge2_active = "active" ]; then
        /etc/init.d/jitsi-videobridge2 stop
    else
        echo "jitsi-videobridge2 is already inactive"
    fi
fi



# Start nginx service
if service --status-all | grep -Fq 'nginx'; then    
  nginx_active=$(systemctl show -p ActiveState --value nginx)

    if [ $nginx_active = "active" ]; then
        /etc/init.d/nginx stop
    else
        echo "nginx is already inactive"
    fi
fi   