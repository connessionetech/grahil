#!/bin/bash
#!/usr/bin/bash 
## --

# Configuration file
REACT_CONFIGURATION_FILE=conf.ini

# DEFAULT_APP_PATH=/usr/local/reactivity
REACT_LOGGING=true
REACT_LOG_FILE_NAME=installer.log
REACT_LOG_FILE=$PWD/$REACT_LOG_FILE_NAME

REACT_OS_TYPE=
OS_DEB="DEBIAN"
OS_RHL="REDHAT"

REACT_APP_NAME=reactivity
REACT_INSTALL_AS_SERVICE=true
REACT_SERVICE_LOCATION=/lib/systemd/system
REACT_VENV_LOCATION=/opt/reactivity/venv
REACT_ENTRY_POINT=run.py
REACT_SERVICE_NAME=reactivity.service
REACT_SERVICE_VERSION=2

REACT_IS_64_BIT=0
REACT_OS_NAME=
REACT_OS_IS_ARM=false
REACT_OS_VERSION=
REACT_MODE=0

REACT_DEFAULT_DOWNLOAD_NAME="reactivity_latest.zip"
REACT_DEFAULT_DOWNLOAD_FOLDER_NAME="tmp"
REACT_DEFAULT_DOWNLOAD_FOLDER=
REACT_INSTALLER_OPERATIONS_CLEANUP=1

REACT_DOWNLOAD_URL=
REACT_VERSION=_
PYTHON_VERSION=

validatePermissions()
{
	if [[ $EUID -ne 0 ]]; then
		echo "This script does not seem to have / has lost root permissions. Please re-run the script with 'sudo'"
		exit 1
	fi
}

######################################################################################
################################## LOGGER ############################################

write_log()
{
	if [ $# -eq 0 ]; then
		return
	else
		if $REACT_LOGGING; then			
			logger -s $1 2>> $REACT_LOG_FILE
		fi
	fi
}

lecho()
{
	if [ $# -eq 0 ]; then
		return
	else
		echo $1

		if $REACT_LOGGING; then
			logger -s $1 2>> $REACT_LOG_FILE
		fi
	fi
}


lecho_err()
{
	if [ $# -eq 0 ]; then
		return
	else
		# Red in Yellow
		echo -e "\e[41m $1\e[m"

		if $REACT_LOGGING; then
			logger -s $1 2>> $REACT_LOG_FILE
		fi
	fi
}


clear_log()
{
	> $REACT_LOG_FILE
}



delete_log()
{
	rm $REACT_LOG_FILE
}

######################################################################################
############################ MISC ----- METHODS ######################################

cls()
{
	printf "\033c"
}

refresh()
{
	if [ "$REACT_MODE" -eq  1 ]; then
 	show_utility_menu
	else
 	show_simple_menu
	fi
}

pause()
{

	printf "\n"
	read -r -p 'Press any [ Enter ] key to continue...' key


	if [ "$REACT_MODE" -eq  1 ]; then
 	show_utility_menu
	else
 	show_simple_menu
	fi
}

empty_pause()
{
	printf "\n"
	read -r -p 'Press any [ Enter ] key to continue...' key
}

empty_line()
{
	printf "\n"
}


######################################################################################
############################ MISC TOOL INSTALLS ######################################


check_python()
{
	lecho "Checking for python3"			
	python_check_success=0

	if command -v python3 &>/dev/null; then
		python_check_success=1
		py="$(command -v python3)"
		lecho "python3 was found at $py"
		version_str=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
		IFS='.'
		read -ra ADDR <<< "$version_str"
		local count=0
		local ver_num=""
		for i in "${ADDR[@]}"; do # access each element of array
		ver_num="$ver_num$i"
		count=$((count+1))	
		if [[ $count -eq 3 ]]; then
		break
		fi	
		done
		IFS=' '

		PYTHON_VERSION="$ver_num"
	else
		python_check_success=0
		lecho "python3 not found."				
	fi
}



# Public
check_unzip()
{
	write_log "Checking for unzip utility"			
	unzip_check_success=0

	if isinstalled unzip; then
	unzip_check_success=1
	write_log "unzip utility was found"		
	else
	unzip_check_success=0
	lecho "unzip utility not found."				
	fi
}


check_git()
{
	write_log "Checking for git software"	
	git_check_success=0

	if isinstalled git; then
	git_check_success=1
	write_log "git utility was found"
	else
	git_check_success=0
	lecho "git utility not found."
	fi
}

check_wget()
{
	write_log "Checking for wget utility"	
	wget_check_success=0

	if isinstalled wget; then
	wget_check_success=1
	write_log "wget utility was found"
	else
	wget_check_success=0
	lecho "wget utility not found."
	fi
}

check_bc()
{
	write_log "Checking for bc utility"	
	bc_check_success=0

	if isinstalled bc; then
	bc_check_success=1
	write_log "bc utility was found"
	else
	bc_check_success=0
	lecho "bc utility not found."
	fi
}


# Public
install_unzip()
{
	write_log "Installing unzip"

	if isDebian; then
	install_unzip_deb	
	else
	install_unzip_rhl
	fi		
}

# Private
install_unzip_deb()
{
	write_log "Installing unzip on debian"

	apt-get install -y unzip

	install_unzip="$(which unzip)";
	lecho "Unzip installed at $install_unzip"
}

# Private
install_unzip_rhl()
{
	write_log "Installing unzip on rhle"

	# yup update
	yum -y install unzip

	install_unzip="$(which unzip)";
	lecho "Unzip installed at $install_unzip"
}

# Public

install_git()
{
	write_log "Installing git"

	if isDebian; then
	install_git_deb	
	else
	install_git_rhl
	fi		
}

install_wget()
{
	write_log "Installing wget"

	if isDebian; then
	install_wget_deb	
	else
	install_wget_rhl
	fi		
}

install_bc()
{
	write_log "Installing bc"

	if isDebian; then
	install_bc_deb	
	else
	install_bc_rhl
	fi		
}

# Private

install_git_deb()
{
	write_log "Installing git on debian"

	apt-get install -y git

	install_git="$(which git)";
	lecho "git installed at $install_git"
}

install_git_rhl()
{
	write_log "Installing git on rhle"

	yum -y install git

	install_git="$(which git)";
	lecho "git installed at $install_git"
}

install_wget_deb()
{
	write_log "Installing wget on debian"

	apt-get install -y wget

	install_wget="$(which wget)";
	lecho "wget installed at $install_wget"
}

# Private
install_wget_rhl()
{
	write_log "Installing wget on rhle"

	# yup update
	yum -y install wget

	install_wget="$(which wget)";
	lecho "wget installed at $install_wget"
}

# Private
install_bc_deb()
{
	write_log "Installing bc on debian"

	apt-get install -y bc

	install_bc="$(which bc)";
	lecho "bc installed at $install_bc"
}

# Private
install_bc_rhl()
{
	write_log "Installing bc on rhle"

	# yup update
	yum -y install bc

	install_bc="$(which bc)";
	lecho "bc installed at $install_bc"
}



install_python()
{
	if isDebian; then
	 install_python_deb
	else
	 install_python_rhle
	fi
}


install_python_deb()
{
	# If ubuntu	
	#if [ "$REACT_OS_TYPE" == "Ubuntu" ]; then
	if [[ $REACT_OS_NAME == *"Ubuntu"* ]]; then

		version_str="$REACT_OS_VERSION"
		IFS='.'
		read -ra ADDR <<< "$version_str"
		local count=0
		local ver_num=""
		for i in "${ADDR[@]}"; do # access each element of array
		ver_num="$ver_num$i"
		count=$((count+1))	
		if [[ $count -eq 3 ]]; then
		break
		fi	
		done
		IFS=' '


		if [[ $ver_num -gt 1604 ]]; then
			lecho "Installing python3 for Ubuntu > 16.04"
			apt-get update && apt-get install python3.6
		else
			lecho "Installing python3 for Ubuntu 16.04"
			apt-get install software-properties-common
			add-apt-repository ppa:deadsnakes/ppa
			apt-get update && apt-get install python3.6
		fi

	elif [[ $REACT_OS_NAME == *"Debian"* ]]; then

		if [ "$REACT_OS_IS_ARM" = true ] ; then

			lecho "Probably Raspberry PI"

			apt-get install python3-dev libffi-dev libssl-dev -y
			wget https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tar.xz
			tar xJf Python-3.6.3.tar.xz
			cd Python-3.6.3
			./configure
			make
			make install
			pip3 install --upgrade pip
		else
			lecho "Operating system not supported"
		fi
		
	else
		lecho "Operating system not supported"
	fi

	check_python
}



install_python_rhle()
{
	yum update && yum install yum-utils
	yum install https://centos7.iuscommunity.org/ius-release.rpm
	yum install python36u && yum install python36u-pip

	check_python
}



create_python_venv()
{
	local interpreter="$(command -v python3)"

	# Check if virtual environment folder exists or not
	if [ ! -d "$REACT_VENV_LOCATION" ]; then
		mkdir -p $REACT_VENV_LOCATION
		if [ ! -d "$REACT_VENV_LOCATION" ]; then
			lecho_err "Could not create output directory."
			pause;
		fi
	fi


	# Check if virtual environment is ok else initialize
	local PY_EXECUTABLE="$REACT_VENV_LOCATION/bin/python3"
	if [ ! -f "$PY_EXECUTABLE" ]; then
		lecho "Initializing virtual environment!"
		cd $REACT_VENV_LOCATION
		apt-get install -y python3-venv
		$interpreter -m venv $REACT_VENV_LOCATION
		# cd $REACT_VENV_LOCATION && source ./bin/activate
	fi

	
	# one more final check for executable
	if [ ! -f "$PY_EXECUTABLE" ]; then
		lecho_err "Virtual environment could not be initialized."
		pause;
	fi


	lecho "Virtual environment ready!. $REACT_VENV_LOCATION"
}


install_py_header()
{
	if isDebian; then
		if [[ $PYTHON_VERSION -gt 359 ]]; then
			apt-get install -y python3.6-dev
		elif [[ $PYTHON_VERSION -gt 351 ]]; then
			apt-get install -y python3.5-dev
		fi
	else
	 	if [[ $PYTHON_VERSION -gt 359 ]]; then
			yum install -y python3.6-dev
		elif [[ $PYTHON_VERSION -gt 351 ]]; then
			yum install -y python3.5-dev
		fi
	fi
}



install_application()
{
	lecho "Preparing application dependencies"

	cd $REACT_VENV_LOCATION && source ./bin/activate

	local REQUIREMENTS

	install_py_header

	if [[ $PYTHON_VERSION -gt 359 ]]; then
		lecho "python 3.6 version satisfied."
		REQUIREMENTS="prod36.txt"
	elif [[ $PYTHON_VERSION -gt 351 ]]; then
		lecho "python 3.5 version satisfied."
		REQUIREMENTS="prod35.txt"
	else
		lecho "Incompatible python version or python not installed"
		REQUIREMENTS=
		pause
	fi

	local REACTIVITY_REQUIREMENTS="$DEFAULT_APP_PATH/requirements/$REQUIREMENTS"
	pip3 install -r $REACTIVITY_REQUIREMENTS
}



# Private
download_from_url()
{
	clear
	
	latest_rpro_download_success=0
	rpro_zip=
	# REACT_DOWNLOAD_URL=

	lecho "Downloading from url"
	
	# create tmp directory
	#dir=`mktemp -d` && cd $dir
	dir="$REACT_DEFAULT_DOWNLOAD_FOLDER"
	cd $dir

	if [ -z "$REACT_DOWNLOAD_URL" ]; then
		echo "Enter the Reactivity archive file URL source";
		read REACT_DOWNLOAD_URL
	fi

	# Permission check
	validatePermissions

	lecho "Attempting to download archive file to $REACT_DEFAULT_DOWNLOAD_FOLDER"

	wget -O "$REACT_DEFAULT_DOWNLOAD_NAME" "$REACT_DOWNLOAD_URL"

	rpro_zip="$REACT_DEFAULT_DOWNLOAD_FOLDER/$REACT_DEFAULT_DOWNLOAD_NAME"

	if [ -f $rpro_zip ] ; then
		find . -type f -not \( -name '*zip' \) -delete

		latest_rpro_download_success=1
	else
		lecho "Oops!! Seems like the archive was not downloaded properly to disk."
		pause	
	fi

}


auto_install()
{
	write_log "Starting  auto-installer"

	red5_zip_install_success=0

	# Install prerequisites
	prerequisites	

	# Create virtual environment
	create_python_venv

	# Download red5 zip from url
	echo "Preparing to install Reactivity"
	sleep 2

	download_from_url

	if [ "$latest_rpro_download_success" -eq 0 ]; then
		lecho_err "Failed to download Reactivity distribution from $REACT_DOWNLOAD_URL. Please contact support!"
		pause
	fi


	if [ -z "$rpro_zip" ]; then
		lecho_err "Downloaded file could not be found or is invalid. Exiting now!"
		pause
	fi


	lecho "Installing Reactivity from $rpro_zip"
	sleep 2

	install_dist_zip $rpro_zip $REACT_DOWNLOAD_URL

	if [ "$red5_zip_install_success" -eq 0 ]; then		
		lecho_err "Failed to install Reactivity distribution. Something went wrong!! Try again or contact support!"
	fi

	

	
	if [ $# -eq 0 ]
	  then
	    pause
	fi
	
}

# Public
register_as_service()
{
	check_current_installation 1

	if [ "$rpro_exists" -eq 1 ]; then

		write_log "Registering service for Reactivity"

		if [ -f "$REACT_SERVICE_LOCATION/$REACT_SERVICE_NAME" ]; then
		lecho "Service already exists. Do you wish to re-install ?" 
		read -r -p "Are you sure? [y/N] " response

		case $response in
		[yY][eE][sS]|[yY]) 
		register_rpro_service
		;;
		*)
		lecho "Service installation cancelled"
		;;
		esac

		else
		register_rpro_service
		fi
	fi

	if [ $# -eq 0 ]
	  then
	    pause
	fi
}

# Public
unregister_as_service()
{
	check_current_installation 0

	if [ "$rpro_exists" -eq 1 ]; then

		if [ ! -f "$REACT_SERVICE_LOCATION/$REACT_SERVICE_NAME" ]; then
			lecho "Service does not exists. Nothing to remove" 
		else
			unregister_service
		fi

	fi

	if [ $# -eq 0 ]
	  then
	    pause
	fi
}

# Public
install_dist_zip()
{
	red5_zip_install_success=0

	# Install prerequisites
	# prerequisites [ extra not needed ]
			
	clear
	lecho "Installing Reactivity from zip"
	

	if [ $# -eq 0 ]; then
		echo "Enter the full path to Reactivity distribution archive"
		read rpro_zip_path
	else 
		rpro_zip_path=$1
	fi

	write_log "Installing Reactivity from zip $rpro_zip_path"

	if ! isValidArchive $rpro_zip_path; then
		lecho "Cannot process archive $rpro_zip_path"
		pause;
	fi

	local filename=$(basename "$rpro_zip_path")
	local extension="${filename##*.}"
	filename="${filename%.*}"

	lecho "Attempting to install Reactivity from zip"

	dir="$REACT_DEFAULT_DOWNLOAD_FOLDER"
	cd $dir

	unzip_dest="$dir/$filename"

	check_current_installation 1
	
	if [ "$rpro_exists" -eq 1 ]; then

		lecho "An existing Reactivity installation was found at install destination.If you continue this will be replaced. The old installation will be backed up to $RPRO_BACKUP_HOME"

		sleep 1
		echo "Warning! All file(s) and folder(s) at $DEFAULT_APP_PATH will be removed permanently"
		read -r -p "Do you wish to continue? [y/N] " response

		case $response in
		[yY][eE][sS]|[yY])

		if [ $rpro_backup_success -eq 0 ]; then
			# proceed to install new Reactivity
			lecho_err "Failed to create a backup of your existing Reactivity installation"
			pause
		fi	

		# remove rpro service
		unregister_service

		# check remove old files
		rm -rf $DEFAULT_APP_PATH

		;;
		*)
		lecho "Operation cancelled"
		pause
		;;
		esac	
	fi

	lecho "Unpacking archive $rpro_zip_path to install location..."

	if [ -d "$unzip_dest" ]; then
	  rm -rf $unzip_dest
	fi
	
	
	if ! unzip $rpro_zip_path -d $unzip_dest; then
		lecho_err "Failed to extract zip. Possible invalid archive"
		pause;
	fi


	if [ ! -d "$unzip_dest" ]; then
		lecho_err "Could not create output directory."
		pause;
	fi

	# Move to actual install location 
	rpro_loc=$DEFAULT_APP_PATH

	lecho "Moving files to install location : $rpro_loc"

	# Identify archive type and move accordingly

	if [[ $# -gt 1 ]]; then

		if isSingleLevel $unzip_dest; then
			
			# Single level archive -> top level manual zip
			if [ ! -d "$rpro_loc" ]; then
			  mkdir -p $rpro_loc
			fi

			mv -v $unzip_dest/* $rpro_loc

		else
			# Two level archive -> like at red5pro.com
			rpro_loc=$DEFAULT_APP_PATH
			mv -v $unzip_dest/* $rpro_loc
		fi


	else
		# Move to actual install location 
		rpro_loc=$DEFAULT_APP_PATH
		mv -v $unzip_dest/* $rpro_loc
	fi

	# DEFAULT_APP_PATH=/usr/local/red5pro

	lecho "Setting permissions ..."

	sleep 1


	# Setup application
	install_application
 

	# Clear tmp directories - IMPORTANT
	if [ "$REACT_INSTALLER_OPERATIONS_CLEANUP" -eq 1 ]; then
		lecho "cleaning up ..."
		sleep 1

		# Delete unzipped content
		rm -rf $unzip_dest

		# Delete zip
		rm -rf $rpro_zip_path
	fi

	sleep 1	

	if [ ! -d "$rpro_loc" ]; then
		lecho "Could not install Reactivity at $rpro_loc"
		pause
	else
		echo "All done! ..."
		lecho "Reactivity installed at  $rpro_loc"
		red5_zip_install_success=1
	fi


	# Installing red5 service
	if $REACT_INSTALL_AS_SERVICE; then			

		echo "For Reactivity to autostart with operating system, it needs to be registered as a service"
		read -r -p "Do you want to register Reactivity service now? [y/N] " response

		case $response in
		[yY][eE][sS]|[yY]) 
		
			lecho "Registering Reactivity as a service"

			sleep 2
			register_rpro_service
		
			if [ "$rpro_service_install_success" -eq 0 ]; then
			lecho_err "Failed to register Reactivity service. Something went wrong!! Try again or contact support!"
			pause
			fi
		;;
		*)
		;;
		esac

		# All Done
		lecho "Reactivity service is now installed on your system. You can start / stop it with from the menu".
	else
		
		lecho "Reactivity service auto-install is disabled. You can manually register Reactivity as service from the menu.".
	fi
	

	# Moving to home directory	
	cd ~

	if [ $# -eq 0 ]
	  then
	    pause
	fi
	
}

isValidArchive()
{
	local archive_path=$1

	if [ ! -f "$archive_path" ]; then
		lecho "Invalid archive file path $archive_path"
		false
	else
		local filename=$(basename "$archive_path")

		local extension="${filename##*.}"
		filename="${filename%.*}"

		local filesize=$(stat -c%s "$archive_path")
		
		if [ "$filesize" -lt 30000 ]; then
			lecho "Invalid archive file size detected for $archive_path. Probable corrupt file!"
			false
		else
			case "$extension" in 
			zip|tar|gz*) 
			    true
			    ;;	
			*)
			    lecho "Invalid archive type $extension"
			    false
			    ;;
			esac
		fi
	fi
}

isSingleLevel()
{
	local rpro_tmp=$1
	local count=$(find $rpro_tmp -maxdepth 1 -type d | wc -l)

	if [ $count -gt 2 ]; then
		true
	else
		false
	fi
}

# Public
register_rpro_service()
{
	# Permission check
	validatePermissions

	register_rpro_service_v2	
}

# Public
unregister_service()
{
	# Permission check
	validatePermissions
	
	unregister_service_v2	
}


####################### V2 #############################

# Private
register_rpro_service_v2()
{
	rpro_service_install_success=0

	lecho "Preparing to install service..."
	sleep 2

	local PYTHON_EXEC="$REACT_VENV_LOCATION/bin/python3"
	local REACTIVITY_EXECUTABLE="$DEFAULT_APP_PATH/$REACT_ENTRY_POINT"

#######################################################

service_script="[Unit]
Description=Reactivity agent for service monitoring and management
After=network.target
Before=red5pro.service

[Service]
User=ubuntu
WorkingDirectory=$DEFAULT_APP_PATH
ExecStart=$PYTHON_EXEC $REACTIVITY_EXECUTABLE
Restart=on-failure

[Install]
WantedBy=multi-user.target"

#######################################################


	lecho "Writing service script"
	sleep 1

	touch /lib/systemd/system/$REACT_SERVICE_NAME

	# write script to file
	echo "$service_script" > /lib/systemd/system/$REACT_SERVICE_NAME

	# make service file executable
	chmod 644 /lib/systemd/system/$REACT_SERVICE_NAME

	register_rpro_service_generic_v2

	lecho "Reactivity service installed successfully!"
	rpro_service_install_success=1	
}

# Private
register_rpro_service_generic_v2()
{

	lecho "Registering service \"$REACT_SERVICE_NAME\""
	sleep 1	

	# Reload daemon 
	systemctl daemon-reload

	lecho "Enabling service \"$REACT_SERVICE_NAME\""

	# enable service
	systemctl enable $REACT_SERVICE_NAME
}

# Private
unregister_service_generic_v2()
{
	lecho "Unregistering service \"$REACT_SERVICE_NAME\""
	sleep 1	

	# Reload daemon 
	systemctl daemon-reload

	lecho "Disabling service \"$REACT_SERVICE_NAME\""

	# disaable service
	systemctl disable $REACT_SERVICE_NAME
}

# Private
unregister_service_v2()
{
	rpro_service_remove_success=0
	
	prog="red5"

	lecho "Preparing to remove service..."
	sleep 2

	if [ -f "/lib/systemd/system/$REACT_SERVICE_NAME" ];	then
	
		unregister_service_generic_v2

		# remove service
		rm -f "/lib/systemd/system/$REACT_SERVICE_NAME"

		lecho "Service removed successfully"
		rpro_service_remove_success=0
	
	else
		lecho "Reactivity service was not found"
	fi
}

# Private
start_red5pro_service_v2()
{
	systemctl start red5pro
}

# Private
stop_service_v2()
{
	systemctl stop red5pro
}

# Private
restart_red5pro_service_v2()
{
	systemctl restart red5pro
}

############################################################

is_service_installed()
{
	if [ ! -f "$REACT_SERVICE_LOCATION/$REACT_SERVICE_NAME" ];	then
	false
	else
	true
	fi
}

start_red5pro_service()
{
	cd ~

	check_current_installation 1 1

	if [ "$rpro_exists" -eq 1 ]; then

		if [ ! -f "$REACT_SERVICE_LOCATION/$REACT_SERVICE_NAME" ];	then
			lecho "It seems Reactivity service was not installed. Please register Reactivity service from the menu for best results."
			lecho " Attempting to start Reactivity manually"

			if !(is_running_red5pro_service_v1); then
				cd $DEFAULT_APP_PATH && exec $DEFAULT_APP_PATH/red5.sh > /dev/null 2>&1 &
			else
				lecho "Server is already running!" 
			fi			

		else
			lecho "Reactivity service was found at $REACT_SERVICE_LOCATION/$REACT_SERVICE_NAME"
			lecho " Attempting to start service"

			if [ "$REACT_SERVICE_VERSION" -eq "1" ]; then
				
				if !(is_running_red5pro_service 1); then
					start_red5pro_service_v1
				else
					lecho "Server is already running!" 
				fi
			else		

				if !(is_running_red5pro_service 1); then
					start_red5pro_service_v2
				else
					lecho "Server is already running!" 
				fi

			fi
		
		fi
	fi

	if [ $# -eq 0 ]
	  then
	    pause
	fi
}

stop_service()
{
	cd ~

	check_current_installation 1 1

	if [ "$rpro_exists" -eq 1 ]; then	


		if [ ! -f "$REACT_SERVICE_LOCATION/$REACT_SERVICE_NAME" ];	then
			lecho "It seems Reactivity service was not installed. Please register Reactivity service from the menu for best results."
			
			lecho "Server is not running!"	
		else
			lecho "Reactivity service was found at $REACT_SERVICE_LOCATION/$REACT_SERVICE_NAME."
			lecho "Attempting to stop Reactivity service"

			if is_running_red5pro_service 1; then
				stop_service_v2
			else
				lecho "Server is not running!" 
			fi
		fi
	fi

	if [ $# -eq 0 ]
	  then
	    pause
	fi
}

restart_red5pro_service()
{
	cd ~
	
	check_current_installation 1 1

	if [ "$rpro_exists" -eq 1 ]; then

		if [ ! -f "$REACT_SERVICE_LOCATION/$REACT_SERVICE_NAME" ];	then
			lecho "It seems Reactivity service was not installed. Please register Reactivity service from the menu for to activate this feature."
		else
			lecho "Reactivity service was found at $REACT_SERVICE_LOCATION/$REACT_SERVICE_NAME."
			lecho "Attempting to restart Reactivity service"

			restart_red5pro_service_v2
		fi
	fi


	if [ $# -eq 0 ]
	  then
	    pause
	fi
}

is_running_red5pro_service_v2()
{
	systemctl status red5pro | grep 'active (running)' &> /dev/null
	if [ $? == 0 ]; then
	   true
	else
	   false	
	fi
}


is_running_red5pro_service()
{
	cd ~
	
	local rpro_running=0
	check_current_installation 1 1

	if [ "$rpro_exists" -eq 1 ]; then

		if [ ! -f "$REACT_SERVICE_LOCATION/$REACT_SERVICE_NAME" ];	then
			lecho "It seems Reactivity service was not installed. Please register Reactivity service from the menu for to activate this feature."
		else			

			if [ "$REACT_SERVICE_VERSION" -eq "1" ]; then
				if is_running_red5pro_service_v1; then
					rpro_running=1
				fi

			else
				if is_running_red5pro_service_v2; then
					rpro_running=1
				fi				
			fi
		fi
	fi


	if [ $# -eq 0 ]; then
	    pause
	else
	    if [ "$rpro_running" -eq 1 ]; then
		true
	    else
		false
	    fi
	fi
}

remove_rpro_installation()
{
	lecho "Looking for Reactivity at install location..."
	sleep 2

	if [ ! -d $DEFAULT_APP_PATH ]; then
  		lecho "No Reactivity installation found at install location : $DEFAULT_APP_PATH"
	else
		version_file="$DEFAULT_APP_PATH/oneadmin/version.py" 

		if [ ! -f $version_file ]; then
		lecho "The install folder was found but the installation might be broken !. I could not locate version information"
		else
		echo "Reactivity installation found at install location : $DEFAULT_APP_PATH"
		echo "Warning! All file(s) and folder(s) at $DEFAULT_APP_PATH will be removed permanently"
		read -r -p "Are you sure? [y/N] " response

		case $response in
		[yY][eE][sS]|[yY]) 

		# Stop if running
		stop_service 1

		# remove rpro service
		unregister_service

		# check remove virtual environment
		lecho "Removing virtual environment"
		rm -r $REACT_VENV_LOCATION

		# check remove folder
		rm -rf $DEFAULT_APP_PATH

		unset RED5_HOME

		if [ ! -d "$DEFAULT_APP_PATH" ]; then
			lecho "Installation was removed"
		fi
		;;
		*)
		lecho "Uninstall cancelled"
		;;
		esac
		fi
	fi


	if [ $# -eq 0 ]; then
		pause		
	fi
	
}

check_current_installation()
{
	rpro_exists=0
	local check_silent=0

	# IF second param is set then turn on silent mode quick check
	if [ $# -eq 2 ]; then
		check_silent=1		
	fi


	if [ ! "$check_silent" -eq 1 ] ; then
		lecho "Looking for Reactivity at install location..."
		sleep 2
	fi


	if [ ! -d $DEFAULT_APP_PATH ]; then
		if [ ! "$check_silent" -eq 1 ] ; then
  		lecho "No Reactivity installation found at install location : $DEFAULT_APP_PATH"
		fi
	else

		rpro_exists=1

		if [ ! "$check_silent" -eq 1 ] ; then
			lecho "Reactivity installation found at install location : $DEFAULT_APP_PATH"
		fi
	fi

	if [ $# -eq 0 ]; then
		pause		
	fi


	# return true or false
	if [ ! "$rpro_exists" -eq 1 ] ; then
		true
	else
		false
	fi

}


######################################################################################
############################ SIMPLE OPERATION MENU ################################

show_simple_menu()
{
	simple_menu
	simple_menu_read_options
}

simple_menu()
{

	cls

	check_current_installation 1 1

	detect_system

	printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -	


	if [[ $rpro_exists -eq 1 ]]; then

		printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
		echo "1. --- UPDATE		"
		echo "2. --- UNINSTALL	"
		printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -				
		#printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -	
		if is_service_installed; then
			echo "3. --- START SERVICE			"
			echo "4. --- STOP SERVICE			"	
			echo "5. --- RESTART SERVICE			"
			printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
			echo "6. --- REMOVE SERVICE			"
		else
			printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
			echo "3. --- INSTALL SERVICE			"
		fi
	else
		echo "1. --- INSTALL		"
	fi

	printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -	
	echo "X. --- Exit				"
	echo "                             		"

}

simple_menu_read_options(){

	local choice

	# Permission check
	validatePermissions

	if [[ $rpro_exists -eq 1 ]]; then
		if is_service_installed; then
		read -p "Enter choice [ 1 - 6 | 0 to go back | X to exit ] " choice
		else
		read -p "Enter choice [ 1 - 3 | 0 to go back | X to exit ] " choice
		fi
	else
		read -p "Enter choice [ 1 - 0 | 0 to go back | X to exit ] " choice
	fi
	
	case $choice in
		1) 
			if [[ $rpro_exists -eq 1 ]]; then
				cls && auto_update_rpro_url
			else
				cls && auto_install
			fi
			;;
		2) 
			if [[ $rpro_exists -eq 1 ]]; then
				cls && remove_rpro_installation 
			else
				echo -e "\e[41m Error: Invalid choice\e[m" && sleep 2 && show_simple_menu
			fi
			;;
		3) 

			if [[ $rpro_exists -eq 1 ]]; then
				if is_service_installed; then
					cls && start_red5pro_service
				else
					cls && register_as_service
				fi
			else
				echo -e "\e[41m Error: Invalid choice\e[m" && sleep 2 && show_simple_menu
			fi
			;;
		4) 

			if [[ $rpro_exists -eq 1 ]]; then
				cls && stop_service
			else
				echo -e "\e[41m Error: Invalid choice\e[m" && sleep 2 && show_simple_menu
			fi
			;;
		5)
			if is_service_installed; then
				if [[ $rpro_exists -eq 1 ]]; then
					cls && restart_red5pro_service
				else
					echo -e "\e[41m Error: Invalid choice\e[m" && sleep 2 && show_simple_menu
				fi
			else
				cls && register_as_service
			fi
			;;
		6)
			if is_service_installed; then
				cls && unregister_as_service
			else
				echo -e "\e[41m Error: Invalid choice\e[m" && sleep 2 && show_simple_menu
			fi
			;;
		7)
			if is_service_installed; then
				echo -e "\e[41m Error: Invalid choice\e[m" && sleep 2 && show_simple_menu
			else
				cls && register_as_service
			fi
			;;
		0) cls && main ;;
		[xX])  exit 0;;
		*) echo -e "\e[41m Error: Invalid choice\e[m" && sleep 2 && show_simple_menu ;;
	esac
}

######################################################################################
################################ INIT FUNCTIONS ######################################

load_configuration()
{
	sudo sleep 0

	if [ ! -f $REACT_CONFIGURATION_FILE ]; then

		echo -e "\e[41m CRITICAL ERROR!! - Configuration file not found!\e[m"
		echo -e "\e[41m Exiting...\e[m"
		exit 1
	fi

	# Load config values
	source "$REACT_CONFIGURATION_FILE"


	# Set install location if not set

	CURRENT_DIRECTORY=$PWD
	

	if [ -z ${DEFAULT_REACT_INSTALL_LOCATION+x} ]; then 
		DEFAULT_APP_PATH="$CURRENT_DIRECTORY/$DEFAULT_REACT_FOLDER_NAME"
	else
		DEFAULT_APP_PATH="$DEFAULT_REACT_INSTALL_LOCATION/$DEFAULT_REACT_FOLDER_NAME"			
	fi


	REACT_DEFAULT_DOWNLOAD_FOLDER="$CURRENT_DIRECTORY/$REACT_DEFAULT_DOWNLOAD_FOLDER_NAME"
	[ ! -d foo ] && mkdir -p $REACT_DEFAULT_DOWNLOAD_FOLDER && chmod ugo+w $REACT_DEFAULT_DOWNLOAD_FOLDER

}

detect_system()
{

	local ARCH=$(uname -m | sed 's/x86_//;s/i[3-6]86/32/')

	if [ -f /etc/lsb-release ]; then
	    . /etc/lsb-release
	    REACT_OS_NAME=$DISTRIB_ID
	    REACT_OS_VERSION=$DISTRIB_RELEASE
	elif [ -f /etc/debian_version ]; then
	    REACT_OS_NAME=Debian  # XXX or Ubuntu??
	    REACT_OS_VERSION=$(cat /etc/debian_version)
	elif [ -f /etc/redhat-release ]; then
	    # TODO add code for Red Hat and CentOS here
	    REACT_OS_VERSION=$(rpm -q --qf "%{VERSION}" $(rpm -q --whatprovides redhat-release))
	    REACT_OS_NAME=$(rpm -q --qf "%{RELEASE}" $(rpm -q --whatprovides redhat-release))
	else
	    REACT_OS_NAME=$(uname -s)
	    REACT_OS_VERSION=$(uname -r)
	fi

	case $(uname -m) in
	x86_64)
	    ARCH=x64  # AMD64 or Intel64 or whatever
	    REACT_IS_64_BIT=1
	    os_bits="64 Bit"
	    ;;
	i*86)
	    ARCH=x86  # IA32 or Intel32 or whatever
	    REACT_IS_64_BIT=0
	    os_bits="32 Bit"
	    ;;
	armv6l)
	    ARCH=arm
	    REACT_OS_IS_ARM=true
	    os_bits="32 Bit"
	    ;;
	*)
	    # leave ARCH as-is
	    ;;
	esac

	echo -e "* Distribution: \e[36m$REACT_OS_NAME\e[m"
	write_log "Distribution: $REACT_OS_NAME"

	echo -e "* Version: \e[36m$REACT_OS_VERSION\e[m"
	write_log "Version: $REACT_OS_VERSION"

	echo -e "* Kernel: \e[36m$os_bits\e[m"
	write_log "Kernel: $os_bits"


	empty_line

	
	if [[ $REACT_OS_NAME == *"Ubuntu"* ]]; then
	REACT_OS_TYPE=$OS_DEB
	else
	REACT_OS_TYPE=$OS_RHL
	fi

	write_log "OS TYPE $REACT_OS_TYPE"
}

simple_usage_mode()
{
	write_log "Basic mode selected"

	REACT_MODE=0

	simple_menu
	simple_menu_read_options
}


main()
{
	simple_usage_mode
}

######################################################################################
############################ prerequisites FUNCTION ##################################

prerequisites()
{
	lecho "Checking installation prerequisites..."
	sleep 2

	prerequisites_update

	prerequisites_git
	prerequisites_unzip
	prerequisites_wget
	prerequisites_python
	prerequisites_bc
}

prerequisites_git()
{
	check_git

	if [[ $git_check_success -eq 0 ]]; then
		echo "Installing git..."
		sleep 2

		install_git
	fi 
}


prerequisites_update()
{

	if isDebian; then
	prerequisites_update_deb
	else
	prerequisites_update_rhl
	fi
}

prerequisites_update_deb()
{
	apt-get update
}

prerequisites_update_rhl()
{
	yum -y update
}

prerequisites_unzip()
{	
	check_unzip


	if [[ $unzip_check_success -eq 0 ]]; then
		echo "Installing unzip..."
		sleep 2

		install_unzip
	fi 
}

prerequisites_python()
{
	check_python

	if [[ $python_check_success -eq 0 ]]; then
		echo "Installing python3..."
		sleep 2
		install_python
	else
		MIN_REQUIRED_VER=`expr $MIN_PYTHON_VERSION - 1`
		if [[ $PYTHON_VERSION -gt $MIN_REQUIRED_VER ]]; then
			lecho "Minimum python3 version satisfied."
		else
			echo "Installing python3 valid version..."
			sleep 2
			install_python
		fi

	fi 

}





prerequisites_wget()
{
	
	check_wget


	if [[ $wget_check_success -eq 0 ]]; then
		echo "Installing wget..."
		sleep 2

		install_wget
	fi 
}

prerequisites_bc()
{
	
	check_bc


	if [[ $bc_check_success -eq 0 ]]; then
		echo "Installing bc..."
		sleep 2

		install_bc
	fi 
}



######################################################################################
############################## isinstalled FUNCTION ##################################

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
	if [ "$REACT_OS_TYPE" == "$OS_DEB" ]; then
	true
	else
	false
	fi
}

# Permission check
validatePermissions

# Load configuration
load_configuration

# Start application
write_log "====================================="
write_log "	NEW INSTALLER SESSION		"

main

# detect_system
# auto_install
# check_python
# install_application
# remove_rpro_installation
# create_python_venv
# check_python
#register_rpro_service
# unregister_service


