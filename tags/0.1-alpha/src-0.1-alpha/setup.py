from distutils.core import setup, Extension

    
setup(name = 'ipymake',
      version = "0.1-alpha",
      author='Dillon Hicks',
      author_email='hhicks@ittc.ku.edu',
      url='http://code.google.com/',
      description=\
"""
-----------------------------------------------
ipymake -- An IPython Build Language Extention
-----------------------------------------------

Ipymake aims to be an extention to IPython that allows for the
creation of Pythonic Makefiles.  The Ipymake syntax incorporates the
good parts of both python and Make for a clearer more modern build
language syntax.

WARNING: This is the first ALPHA version of this software. It is
likely to be largely untested and have no compatibility with future 
versions.
 
""",
      package_dir = {'':'.'},
      scripts = ['scripts/ipymake', 'scripts/ipymakec'],
      packages = ['ipymake'],
      
      )
