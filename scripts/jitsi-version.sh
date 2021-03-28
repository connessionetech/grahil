#!/bin/bash


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


# Public
isDebian()
{
	if [ "$RPRO_OS_TYPE" == "$OS_DEB" ]; then
	true
	else
	false
	fi
}


if isinstalled jitsi-meet; then
dpkg --status jitsi-meet | grep ^Version
else
echo "None"
fi
