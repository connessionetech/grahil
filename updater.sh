#!/bin/bash

version_file=https://github.com/connessionetech/grahil-py/blob/develop/oneadmin/version.py
repo=https://github.com/connessionetech/grahil-py
branch=develop
program_dir=/home/rajdeeprath/github/grahil-py
version_current=/home/rajdeeprath/github/grahil-py/oneadmin/version.py
blank=""
target="__version__ = "


# Online version check


curl -o version_new.ini https://raw.githubusercontent.com/connessionetech/grahil-py/develop/oneadmin/version.py
input="version_new.ini"
version="0.0.0"
new_version_num=
while IFS= read -r line
do
  if [[ $line = __version__* ]]
   then
     version="${line/$target/$blank}" 
     break
  fi

done < "$input"


IFS='.'
read -ra ADDR <<< "$version"
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


version="0.0.0"
cp "$version_current" "./version_old.ini"
while IFS= read -r line
do
  if [[ $line = __version__* ]]
   then
     version="${line/$target/$blank}" 
     break
  fi

done < "$input"


old_version_num=
IFS='.'
read -ra ADDR <<< "$version"
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




