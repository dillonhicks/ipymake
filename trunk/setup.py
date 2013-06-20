from distutils.core import setup, Extension
import ipymake.information as info
    
setup(name = 'ipymake',
      version = info.VERSION,
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
 
""",
      package_dir = {'':'.'},
      scripts = ['scripts/ipymake', 'scripts/ipymakec'],
      packages = ['ipymake'],
      
      )
