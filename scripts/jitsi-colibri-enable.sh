#!/bin/bash

api_enabled=0
xmpp_enabled=0
colibri_sip_stats_enabled=0
colibri_sip_protocol_enabled=0

check_videobridge_config()
{
    while IFS= read -r line; do

        echo "hello"

    done < /etc/jitsi/videobridge/config
}


check_sipcommunicator_props()
{
    stats_enabled=
    stats_transport=

    while IFS= read -r line; do

         echo "hello"

    done < /etc/jitsi/videobridge/sip-communicator.properties    
	
}

check_videobridge_config && check_sipcommunicator_props