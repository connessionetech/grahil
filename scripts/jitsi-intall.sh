#!/bin/bash


email=$1
domain=$2

#OpenJDK 8 or OpenJDK 11 must be used.

# Retrieve the latest package versions across all repositories
apt update


# Ensure support for apt repositories served via HTTPS
apt install -y apt-transport-https


sudo apt-add-repository universe -y


# Retrieve the latest package versions across all repositories
sudo apt update


# Add the Jitsi package repository
curl https://download.jitsi.org/jitsi-key.gpg.key | sudo sh -c 'gpg --dearmor > /usr/share/keyrings/jitsi-keyring.gpg'
echo 'deb [signed-by=/usr/share/keyrings/jitsi-keyring.gpg] https://download.jitsi.org stable/' | sudo tee /etc/apt/sources.list.d/jitsi-stable.list > /dev/null


# update all package sources
sudo apt update


# Setup and configure your firewall if applicable
res=$(sudo ufw status verbose)
if [[ $res == *"active"* ]]; then
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 10000/udp
    sudo ufw allow 22/tcp
    sudo ufw allow 3478/udp
    sudo ufw allow 5349/tcp
    sudo ufw enable
fi






check_java()
{
	java_check_success=0
	has_min_java_version=0

	for JAVA in "${JAVA_HOME}/bin/java" "${JAVA_HOME}/Home/bin/java" "/usr/bin/java" "/usr/local/bin/java"
		do
			if [ -x "$JAVA" ]
			then
			break
		fi
	done

	if [ ! -x "$JAVA" ]; then
	  	echo "Unable to locate Java. If you think you do have java installed, please set JAVA_HOME environment variable to point to your JDK / JRE."
	else
		JAVA_VER=$(java -version 2>&1 | sed 's/java version "\(.*\)\.\(.*\)\..*"/\1\2/; 1q')

		JAVA_VERSION=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}')

		echo "Current java version is $JAVA_VERSION"

		JAVA_VERSION_MAJOR=`echo "${JAVA_VERSION:0:3}"`

		if (( $(echo "$JAVA_VERSION_MAJOR < $MIN_JAVA_VERSION" |bc -l) )); then
			has_min_java_version=0			
			lecho "You need to install a newer java version of java!"		
		else
			has_min_java_version=1
			lecho "Minimum java version is already installed!"
		fi
	fi

	if [ ! $# -eq 0 ]
	  then
	    pause
	fi

}




prerequisites_java()
{

	# Checking java
	lecho "Checking java requirements"
	sleep 2
	check_java

	
	if [ "$has_min_java_version" -eq 0 ]; then
		echo "Installing latest java runtime environment..."
		sleep 2

		install_java
	fi 
}


# Install jitsi
echo "jitsi-videobridge jitsi-videobridge/jvb-hostname string $domain" | debconf-set-selections
echo "jitsi-meet jitsi-meet/cert-choice select Self-signed certificate will be generated" | debconf-set-selections
export DEBIAN_FRONTEND=noninteractive
apt -y install jitsi-meet

# Generate Letsencrypt SSL cert
 echo "$email" | /usr/share/jitsi-meet/scripts/install-letsencrypt-cert.sh