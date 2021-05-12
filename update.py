import requests
import tempfile
import os
import zipfile
import pathlib
import shutil
import imp
from jsonmerge import merge


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
url = 'https://www.dropbox.com/s/rxtarcaenlrax3g/grahil-py.zip?dl=0'
current_program_path = "/home/github/grahil-py/"
temp_dir_for_latest = tempfile.TemporaryDirectory()
temp_dir_for_existing = tempfile.TemporaryDirectory()

if is_downloadable(url):
    # download file
    path_to_zip_file = "grahil-latest.zip"
    r = requests.get(url, allow_redirects=True)
    open(path_to_zip_file, 'wb').write(r.content)
    
    # extract file to a tmp location
    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir_for_latest)
    path = os.path.join(temp_dir_for_latest, "run.py")
    if pathlib.Path(str(path)).exists() and path.is_file():
        print ("latest extraction success")
        pass
    
    # copy existing program instalaltion to a tmp location
    shutil.copytree(current_program_path, temp_dir_for_existing)
    path2 = os.path.join(temp_dir_for_existing, "run.py")
    if pathlib.Path(str(path2)).exists() and path2.is_file():
        print ("existing installation copy success")
        pass

    ## compare versions
    versions_module_name = "version.py"
    old_version_module_path = os.path.join(temp_dir_for_existing, "oneadmin", "version.py")
    old_version_module = imp.load_source(versions_module_name, old_version_module_path)
    old_version = int(old_version_module.__version__)

    new_version_module_path = os.path.join(temp_dir_for_latest, "oneadmin", "version.py")
    new_version_module = imp.load_source(temp_dir_for_latest, new_version_module_path)
    new_version = int(new_version_module.__version__)

    if new_version > old_version:
        print ("Ready to upgrade")

else:
    print ("File is not downloadable")
