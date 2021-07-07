#!/bin/bash

PYTHON_2_LOCATION=
PYTHON_3_LOCATION=
PYTHON_2_EXISTS=
PYTHON_3_EXISTS=

has_min_python_version=0

python_2_0_check_success=0
python_3_0_check_success=0

PYTHON_2_LOCATION=
PYTHON_3_LOCATION=
PYTHON_INTERPRETER_LOCATION=

replacement=""
subject="Python "


LOGGING=true

# set location for updater files in config during cron setup
UPDATER_DIR="/home/rajdeeprath/github/grahil-py/update"
UPDATER_SCRIPT="$UPDATER_DIR/updatetest.py"
UPDATER_LOG="$UPDATER_DIR/grahil_update.log"


if $LOGGING; then
    exec 3>&1 4>&2
    trap 'exec 2>&4 1>&3' 0 1 2 3
    exec 1>$UPDATER_LOG 2>&1
fi



# check for python 2.x interpreter
PYTHON_2_EXISTS=$(which python2)
if [[ $PYTHON_2_EXISTS == *"2"* ]]; then
    python_2_0_check_success=1
    has_min_python_version=1
    PYTHON_2_LOCATION=$PYTHON_2_EXISTS
    PYTHON_2_VERSION_OUTPUT=$(python2 --version 2>&1)
    PYTHON_2_VERSION=$(echo "$PYTHON_2_VERSION_OUTPUT" | sed "s/$subject/$replacement/")
    PYTHON_INTERPRETER_LOCATION=$PYTHON_2_LOCATION
fi


# check for python 3.x interpreter
PYTHON_3_EXISTS=$(which python3)
if [[ $PYTHON_3_EXISTS == *"3"* ]]; then
    python_3_0_check_success=1
    has_min_python_version=1
    PYTHON_3_LOCATION=$PYTHON_3_EXISTS
    PYTHON_3_VERSION_OUTPUT=$(python3 --version 2>&1)
    PYTHON_3_VERSION=$(echo "$PYTHON_3_VERSION_OUTPUT" | sed "s/$subject/$replacement/")
    PYTHON_INTERPRETER_LOCATION=$PYTHON_3_LOCATION
fi


# Execute command with proper interpreter & update script
command="$PYTHON_INTERPRETER_LOCATION $UPDATER_SCRIPT > $UPDATER_LOG &"
if [[ -f "$UPDATER_SCRIPT" ]]; then
    if [ "$python_2_0_check_success" -eq 1 ] || [ "$python_3_0_check_success" -eq 1 ]
        eval $command
    fi
fi