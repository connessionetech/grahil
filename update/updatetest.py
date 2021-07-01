import requests
import tempfile
import os
import zipfile
import pathlib
import shutil
import imp
from jsonmerge import merge
from jsonschema import validate
import json
import sys
import time
from pathlib import Path

import logging


# Configure the logging system
logging.basicConfig(filename ='grahil_update.log',
                    level = logging.ERROR)


logging.info("hello")
os.system('systemctl restart grahil.service')
logging.info("bellow")
