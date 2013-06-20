#!/bin/env python
"""
################################################################################
#
# =====================================
# IPyMake Generated Python Script  
# =====================================
#
# Created IPyMake Version: 0.2-beta
# Timestamp: 1262151599
#
#  
# This Python script was created with IPyMake. To run this script you
# will need to have IPython installed. To install IPython you can use
# your distributions package manager, or the Python easy_install that
# is included in the Python SetupTools "easy_install ipython".
#
################################################################################


IPYMAKE_VERSION = "0.2-beta"
SRC_FILENAME = "build_discovery.py"
SRC_MODIFICATION_TIME = 1262151599

"""
# Import the modules with the heaviest use by default.
#
import sys
import os
# Used for caching the build environment
import cPickle

# Allows each ipym_*.py script to be executed on its own if the user
# so desires.
if __name__ == "__main__":
    # Gets the header information from the docstring and
    # loads it into the module namespace.
    # Gives access to IPYMAKE_VERSION, SRC_FILENAME nad 
    # SRC_MODIFICATION_TIME.
    eval(compile(__doc__, __file__, 'exec'))
    sys.exit(os.system("ipymake "+SRC_FILENAME))
    pass


# Get the IPython API, we need their magic 
# to get everything to run.
import IPython.ipapi as ipapi
ip = ipapi.get()

# There isn't a ipython instance running,
# get a dummy api instance.
if ip is None:
    # The dummy instance allows for use to import the module 
    # as is for analysis and introspection.
    ip = ipapi.get(allow_dummy=True, dummy_warn=False)

from ipymake.runtimecore import *




@managed_target
@depends_on()
def python_discovery(**kwargs):

    ip.runlines(
"""
build_python_package(auto_pkg_dir='.',
    name='discovery',
      version='1.0',
      description="Discovery!",
      url='http://ittc.ku.edu/kusp',
      scripts = ['tools/daemonTrace', 
                 'tools/traceme',
         'tools/ccsmTest',
                 'tools/nofilter',
                 'tools/smartgdb',
                 'tools/syscall_trace',
                 'tools/systemMonitor', 'tools/systemMonitorExit'])
""")

    pass





@managed_target
@depends_on()
def clean_discovery(**kwargs):

    ip.runlines(
"""
rm -rfv $env.current_build_path
""")

    pass





@managed_target
@depends_on(python_discovery)
def all(**kwargs):

    ip.runlines(
"""

""")

    pass



def init_hook(**kwargs):
    try:
        __init__(**kwargs)
    except(NameError):
        pass
    #print repr(env)
    pass


def install_hook(is_root=False, **kwargs):
    try:
        install()
    except(NameError):
        
        if is_root:
          ip.runlines("""

for indir in env.install_dirs:
    mkdir -pv $indir
for cmpbin in env.compiled_binaries: 
    cmpbin.install()
""")
        #    ip.runlines("env = eval(cPickle.unpickle('./.ipym_cache.bin'))")


def cleanup_hook(is_root=False, **kwargs):
    try:
        cleanup()
    except(NameError):
        env.close()
     
    pass



###############################################################################
#                  END AUTOMATICALLY GENERATED FILE                             
#
# Note: It is best not to edit this file, unless you know what you are 
# doing. Instead, change the input file and rerun ipymake or ipymakec.
#
###############################################################################
