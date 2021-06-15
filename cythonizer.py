from setuptools import Extension, setup
from Cython.Build import cythonize

ext_modules = cythonize("oneadmin/modules/*.py")
 
setup(name='Hello world app',
      ext_modules=cythonize(ext_modules))