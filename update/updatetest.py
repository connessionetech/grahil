from jsonmerge import merge
from jsonschema import validate
import time
from pathlib import Path
import subprocess
import logging



# Configure the logging system
logging.basicConfig(filename ='/home/rajdeeprath/grahil_update.log',
                    level = logging.INFO)


logging.info("hello")
subprocess.Popen(["systemctl", "stop", "grahil.service"])
logging.info("bellow")
time.sleep(2)
logging.info("bellow")
time.sleep(2)
logging.info("bellow")
time.sleep(2)
logging.info("bellow")
time.sleep(2)
logging.info("bellow")
time.sleep(2)
logging.info("bellow")
time.sleep(2)
logging.info("bellow")
time.sleep(2)
logging.info("bellow")
logging.info("end")