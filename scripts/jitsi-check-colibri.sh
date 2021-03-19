#!/bin/bash

api_enabled=0
xmpp_enabled=0
colibri_sip_stats_enabled=0
colibri_sip_protocol_enabled=0

check_videobridge_config()
{
    while IFS= read -r line; do

        if [[ $line == *"JVB_OPTS="* ]]; then
            
            if [[ $line == *"api"* ]]; then
                api_enabled=1
            fi

            if [[ $line == *"xmpp"* ]]; then
                xmpp_enabled=1
            fi
        fi
    done < /etc/jitsi/videobridge/config
}


check_sipcommunicator_props()
{
    stats_enabled=
    stats_transport=

    while IFS= read -r line; do

        if [[ $line == *"ENABLE_STATISTICS="* ]]; then
            stats_enabled=$line
        fi

        if [[ $line == *"STATISTICS_TRANSPORT="* ]]; then
            stats_transport=$line
        fi

    done < /etc/jitsi/videobridge/sip-communicator.properties


    if [[ "$stats_enabled" == *true ]]; then
        colibri_sip_stats_enabled=1
    fi

    if [[ "$stats_transport" == *colibri ]]; then
        colibri_sip_protocol_enabled=1
    fi    
	
}

check_videobridge_config && check_sipcommunicator_props
echo "{\"api\": $api_enabled, \"xmpp\": $xmpp_enabled, \"colibri_sip_stats_enabled\": $colibri_sip_stats_enabled, \"colibri_sip_protocol_enabled\": $colibri_sip_protocol_enabled}"