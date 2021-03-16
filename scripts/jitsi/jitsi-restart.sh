#!/bin/bash

# Restart prosody service
if service --status-all | grep -Fq 'prosody'; then    
    /etc/init.d/prosody restart    
fi



# Restart jicofo service
if service --status-all | grep -Fq 'jicofo'; then    
    /etc/init.d/jicofo restart
fi


# Restart videobridge service
if service --status-all | grep -Fq 'jitsi-videobridge2'; then
    /etc/init.d/jitsi-videobridge2 restart
fi



# Restart nginx service
if service --status-all | grep -Fq 'nginx'; then
    /etc/init.d/nginx restart
fi