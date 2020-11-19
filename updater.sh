#!/bin/bash

version_file=https://raw.githubusercontent.com/connessionetech/grahil-py/pi-deploy/oneadmin/version.py
repo=https://github.com/connessionetech/grahil-py
branch=pi-deploy
program_dir=/home/rajdeeprath/github/grahil-py
version_current=/home/rajdeeprath/github/grahil-py/oneadmin/version.py
blank=""
target="__version__ = "
new_version_file="version_new.ini"
old_version_file="version_old.ini" 
version="0.0.0"

cd $program_dir

# Online version check

curl -o version_new.ini $version_file
new_version_num=
while IFS= read -r line
do
  if [[ $line = __version__* ]]
   then
     version_found="${line/$target/$blank}" 
     break
  fi

done < "$new_version_file"


IFS='.'
read -ra ADDR <<< "$version_found"
count=0
ver_num=""
for i in "${ADDR[@]}"; do # access each element of array
    new_version_num="$new_version_num$i"
    count=$((count+1))	
    if [[ $count -eq 3 ]]; then
	break
    fi	
done
IFS=' '

echo $new_version_num


sleep 1


# offline version check

cp "$version_current" "$old_version_file"
while IFS= read -r line
do
  if [[ $line = __version__* ]]
   then
     version_found_old="${line/$target/$blank}" 
     break
  fi

done < "$old_version_file"


old_version_num=
IFS='.'
read -ra ADDR <<< "$version_found_old"
count=0
ver_num=""
for i in "${ADDR[@]}"; do # access each element of array
    old_version_num="$old_version_num$i"
    count=$((count+1))	
    if [[ $count -eq 3 ]]; then
	break
    fi	
done
IFS=' '

echo $old_version_num

rm version_old.ini && rm version_new.ini

# Check version and upgrade
if [[ "$new_version_num" -gt "$old_version_num" ]]; then
    sleep 1
    echo "Stopping program"
    sudo systemctl stop grahil.service
    sleep 10
	cd $program_dir
	git pull
	sleep 1
	echo "Starting program"
    sudo systemctl start grahil.service     
fi