"""

"""
from distutils.core import setup, Extension
import sys
import os

#Build directory index when the command is called.
BUILD_DIR_INDEX = 4

BUILD_DIR = sys.argv[BUILD_DIR_INDEX]

configfile_module = Extension('configfile_mod',
	sources = ['configfilemodule.c'],
	include_dirs = ['include'],
	libraries = ['kusp'],
	library_dirs = [BUILD_DIR],
	extra_compile_args = ["-g"]
	)

setup (name = 'libkusp',
      version = "0.1",
      package_dir = {'':'..'},
      description = "Legacy configuration file parsing module.",
	  author = 'Andrew Boie',
	  ext_modules = [configfile_module])

