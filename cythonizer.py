from setuptools import Extension, setup
from Cython.Build import cythonize

ext_modules = cythonize("oneadmin/modules/*.py",
                        "communications.py", 
                        "application.py",
                        "configurations.py",
                        "responsebuilder.py",
                        "oneadmin/handlers/*.py",
                        "oneadmin/security/*.py")
 
setup(name='Grahil', ext_modules=cythonize(ext_modules))