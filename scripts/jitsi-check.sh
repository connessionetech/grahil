#!/bin/bash


check_jitsi()
{

	jitsi_check_success=0
	if isinstalled jitsi-meet; then
		if service --status-all | grep -Fq 'prosody'; then  
			if service --status-all | grep -Fq 'jicofo'; then    
				if service --status-all | grep -Fq 'jitsi-videobridge2'; then
					jitsi_check_success=1
					echo "found"
				else
					echo "broken"
				fi
			else
				echo "broken"
			fi			
		else
			echo "broken"
		fi
	else
		jitsi_check_success=0
		echo "not found."
	fi
}

isinstalled()
{
	if isDebian; then
	isinstalled_deb $1 
	else
	isinstalled_rhl $1
	fi
}

isinstalled_rhl()
{
	if yum list installed "$@" >/dev/null 2>&1; then
	true
	else
	false
	fi
}

isinstalled_deb()
{
	PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $1|grep "install ok installed")

	if [ -z "$PKG_OK" ]; then
	false
	else
	true
	fi
}

isDebian()
{
	if [ "$RPRO_OS_TYPE" == "$OS_DEB" ]; then
	true
	else
	false
	fi
}


check_jitsi