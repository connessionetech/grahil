import importlib
import requests
import tempfile
import os
import zipfile
import pathlib
import shutil
from importlib import import_module
import imp
from jsonmerge import merge
from jsonschema import validate
import json
import sys
import time
from pathlib import Path
from urllib.request import urlopen
import logging


# Configure the logging system
logging.basicConfig(filename ='grahil_update.log',
                    level = logging.ERROR)


''' Check if file is downloadable '''
def is_downloadable(url):
    """
    Does the url contain a downloadable resource
    """
    h = requests.head(url, allow_redirects=True)
    header = h.headers
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True

# Check manifest to determien what is the latest version available

# Download file

manifest = "https://grahil.s3.amazonaws.com/manifest.json"
current_program_path = "/home/rajdeeprath/github/grahil-py/"
program_backup_path = "/home/rajdeeprath/grahil_backups/"
update_filename = "grahil-latest.zip"
versions_module_name = "version.py"
backup_filename = "grahil_last_working"
backup_format = "zip"
error_log_file = "log/errors.log"

def_conf_schema = {
            "properties" : {
                "enabled": {
                    "type": "boolean",
                    "mergeStrategy": "overwrite"
                },
                "klass": {
                    "type": "string",
                    "mergeStrategy": "overwrite"
                },
                "conf": {
                    "type": "object",
                    "mergeStrategy": "objectMerge"
                }
            },
            "required": ["enabled", "klass", "conf"]
        }



def_rules_schema = {
            "properties" : {
                "id": {
                    "type": "boolean",
                    "mergeStrategy": "overwrite"
                },
                "enabled": {
                    "type": "boolean",
                    "mergeStrategy": "overwrite"
                },
                "listen-to": {
                    "type": "string",
                    "mergeStrategy": "overwrite"
                },
                "trigger": {
                    "type": "object",
                    "mergeStrategy": "objectMerge"
                },
                "response": {
                    "type": "object",
                    "mergeStrategy": "objectMerge"
                }
            },
            "required": ["id", "description", "listen-to", "enabled", "trigger", "response"]
        }

def_master_configuration_schema = {
            "properties" : {
                "configuration": {
                    "properties" : {
                        "base_package": {
                            "type": "string",
                            "mergeStrategy": "overwrite"
                        },
                        "server": {
                            "type": "object",
                            "mergeStrategy": "objectMerge"
                        },
                        "ssl": {
                            "type": "object",
                            "mergeStrategy": "objectMerge"
                        },
                        "security": {
                            "type": "object",
                            "mergeStrategy": "objectMerge"
                        },
                        "modules": {
                            "type": "object",
                            "mergeStrategy": "objectMerge"
                        }                    
                    },
                     "required": ["base_package", "server", "ssl", "security", "modules"]
                }                
            },
            "required": ["configuration"]
        }

temp_dir_for_latest = tempfile.TemporaryDirectory() # Where to extract and hold the latest files
temp_dir_for_existing = tempfile.TemporaryDirectory() # Where to copy and work with the existing files
temp_dir_for_download = tempfile.TemporaryDirectory() # Where to download latest build
temp_dir_for_updated = tempfile.TemporaryDirectory() # Where to build & test the update before installation

if is_downloadable(manifest):

    logging.info("Downloading manifest from %s", manifest)

    # Extract all the data from manifest    
    manifest_content = urlopen(manifest).read()
    manifest_data = json.loads(manifest_content)
    manifest_provider = manifest_data["vendor"]
    manifest_release_date = manifest_data["released"]
    payload = manifest_data["payload"]
    payload_version = payload["version"]
    payload_url = payload["url"]
    payload_hash = payload["md5"]
    payload_interpreter = payload["dependencies"]["interpreter"]
    payload_requirements_update = payload["dependencies"]["requirements_update"]
    payload_update_cleanups = payload["cleanups"]


    # Download payload archive to filesystem
    path_to_zip_file = os.path.join(temp_dir_for_download.name, update_filename)
    r = requests.get(payload_url, allow_redirects=True)
    open(path_to_zip_file, 'wb').write(r.content)

    if os.path.exists(path_to_zip_file) and os.path.isfile(path_to_zip_file):
        logging.info("Update downloaded to %s", path_to_zip_file)
    else:
        logging.error("Update download failed")
        sys.exit()
    
    # Extract file to tmp working location
    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir_for_latest.name)
    path = os.path.join(temp_dir_for_latest.name, "run.py")
    if pathlib.Path(str(path)).exists():
        logging.info("latest extraction success")
    else:
        logging.error("Failed to extract update content")
        sys.exit()
    
    # Copy existing program installation to tmp working location
    if os.path.exists(temp_dir_for_existing.name):
        shutil.rmtree(temp_dir_for_existing.name)
        
    shutil.copytree(current_program_path, temp_dir_for_existing.name)
    path2 = os.path.join(temp_dir_for_existing.name, "run.py")
    if pathlib.Path(str(path2)).exists():
        logging.info("existing installation copy success")
    else:
        logging.error("Failed to copy existing program to tmp location")
        sys.exit()

    ## compare versions
    old_version_module_path = os.path.join(temp_dir_for_existing.name, "oneadmin", "version.py")

    
    #old_version_module_spec = importlib.util.spec_from_file_location(versions_module_name.strip(".py"), old_version_module_path)
    #old_version_module = importlib.util.module_from_spec(old_version_module_spec)
    #old_version_module_spec.loader.exec_module(old_version_module)
    old_version_module = imp.load_source(temp_dir_for_latest.name, old_version_module_path)
    old_version = old_version_module.__version__.split(".")
    new_version_module_path = os.path.join(temp_dir_for_latest.name, "oneadmin", "version.py")

    
    #new_version_module_spec = importlib.util.spec_from_file_location(versions_module_name.strip(".py"), old_version_module_path)
    #new_version_module = importlib.util.module_from_spec(new_version_module_spec)
    #new_version_module_spec.loader.exec_module(new_version_module)
    new_version_module = imp.load_source(temp_dir_for_latest.name, new_version_module_path)
    new_version = new_version_module.__version__.split(".")

    upgrade=False    
    if new_version[0] > old_version[0]:
        upgrade=True
    elif (new_version[0] == old_version[0]) and  (new_version[1] > old_version[1]):
        upgrade=True
    elif (new_version[0] == old_version[0]) and  (new_version[1] == old_version[1]) and (new_version[2] > old_version[2]):
        upgrade=True

    logging.debug("upgrade %s", +str(upgrade))
    upgrade = True


    if upgrade:
        logging.info("Conditiosn valid to start upgrade")

        ## First we copy all old files into update workspace
        if os.path.exists(temp_dir_for_updated.name):
            shutil.rmtree(temp_dir_for_updated.name)

        shutil.copytree(temp_dir_for_existing.name, temp_dir_for_updated.name)
        path2 = os.path.join(temp_dir_for_updated.name, "run.py")
        if pathlib.Path(str(path2)).exists():
            logging.info("existing installation copy to update workspace success")
        else:
            logging.error("Failed to copy existing program to update workspace")
            sys.exit()


        # Collect list of all new files (json and otherwise)
        logging.debug("Collecting list of all json files to be processed")
        latest_files = []
        latest_json_files = []
        for subdir, dirs, files in os.walk(temp_dir_for_latest.name):
            for file in files:
                if not file.endswith(".json"):
                    program_file = os.path.join(subdir, str(file))
                    latest_files.append(program_file)
                else:
                    json_file = os.path.join(subdir, str(file))
                    latest_json_files.append(json_file)
                
        
        # then we overwrite new files on old files in updated workspace (minus json files)
        for file in latest_files:
            old_file_in_update_workspace = str(file).replace(temp_dir_for_latest.name, temp_dir_for_updated.name)
            dest = shutil.copy2(old_file_in_update_workspace, file)


        ## check, validate and merge json configuration files        
        for file in latest_json_files:
            old_file_in_update_workspace = str(file).replace(temp_dir_for_latest.name, temp_dir_for_updated.name)
            logging.debug("updating file %s", old_file_in_update_workspace)

            with open(old_file_in_update_workspace, 'r') as old_json_file:
                base_data = old_json_file.read()
                base_obj = json.loads(base_data)
            
                with open(file, 'r') as latest_json_file:
                    latest_data = latest_json_file.read()
                    latest_obj = json.loads(latest_data)

                if "conf/" in old_file_in_update_workspace:
                    validate(base_obj, def_conf_schema)
                    validate(latest_obj, def_conf_schema)
                    updated_data = merge(latest_obj, base_obj)
                elif "rules/" in old_file_in_update_workspace:
                    validate(base_obj, def_rules_schema)
                    validate(latest_obj, def_rules_schema)
                    updated_data = merge(latest_obj, base_obj)
                elif "configuration.json" in old_file_in_update_workspace:
                    validate(base_obj, def_master_configuration_schema)
                    validate(latest_obj, def_master_configuration_schema)
                    updated_data = merge(latest_obj, base_obj)
                else:
                    logging.warn("Unsure of how to update this file... skipping")
                    continue

                with open(old_file_in_update_workspace, "w") as outfile:
                        outfile.write(json.dumps(updated_data))

        
        ## verify everything

        
        ## stop running program service
        os.system("systemctl stop grahil.service")


        ## backup everything to a safe location
        Path(program_backup_path).mkdir(parents=True, exist_ok=True)        
        shutil.make_archive(backup_filename, backup_format, root_dir=program_backup_path, base_dir=current_program_path)
        backup_file = os.path.join(program_backup_path, backup_filename + "." + backup_format)
        if os.path.exists(backup_file):
            logging.info("backup created @ %s", backup_file)
        else:
            logging.error("Failed to create backup of existing program")
            sys.exit()

        
        ## overwrite everything from prepared package to program location
        for subdir, dirs, files in os.walk(temp_dir_for_updated.name):
            for file in files:
                    source = os.path.join(subdir, str(file))
                    desitination = source.replace(temp_dir_for_updated.name, current_program_path)
                    shutil.copy2(source, desitination)
        
        # Wait 5 seconmds
        time.sleep(5)

        
        ## Start service
        os.system("systemctl restart grahil.service")


        # Wait for service to start
        time.sleep(15)


        ## verify things are running ok and there are no errors from logs
        TESTED_OK = False    

        error_log = os.path.join(current_program_path, error_log_file)
        if os.path.exists(error_log) and os.path.isfile(error_log):
            file_size = os.path.getsize(error_log)
            if file_size < 20:
                TESTED_OK = True


        ## if anything is not working as expected cancel upgrade and restore backup
        if not TESTED_OK:
            logging.error("Upgrade failed. Reverting")
            
            ## stop service
            os.system("systemctl stop grahil.service")
            
            time.sleep(5)

            for subdir, dirs, files in os.walk(temp_dir_for_existing.name):
                for file in files:
                        source = os.path.join(subdir, str(file))
                        desitination = source.replace(temp_dir_for_existing.name, current_program_path)
                        shutil.copy2(source, desitination)

            time.sleep(5)

            ## start service
            os.system("systemctl restart grahil.service")

    else:
        logging.error("cannot upgrade")

else:
    logging.error("File is not downloadable")
