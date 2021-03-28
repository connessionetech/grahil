from distutils.core import extension, setup
from cython.build import cythonize
from cython.compiler import options
#__file__ Contains magic variables should be excluded,Although cython has a compilation parameter,But only static can be set.
exclude_so=["__init__.py", "mixins.py"]
sources=["oneadmin", "libs"]
extensions=[]
for source in sources:
  for dirpath, foldernames, filenames in os.walk (source):
    for filename in filter (lambda x:re.match (r". * [.] py $", x), filenames):
      file_path=os.path.join (dirpath, filename)
      if filename not in exclude_so:
        extensions.append (
            extension (file_path [:-3] .replace ("/", "."), [file_path], extra_compile_args=["-os", "-g0"],                 extra_link_args=["-wl,-strip-all"]))
options.docstrings=false
compiler_directives={"optimize.unpack_method_calls":false}
setup (
    #cythonize exclude full path matching,Inflexible, it is better to exclude in the previous step.
    ext_modules=cythonize (extensions, exclude=none, nthreads=20, quiet=true, build_dir="./build",                language_level=2 or 3, compiler_directives=compiler_directives))

