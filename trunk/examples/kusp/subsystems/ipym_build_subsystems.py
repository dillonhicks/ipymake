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
SRC_FILENAME = "build_subsystems.py"
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
def common(**kwargs):

    ip.runlines(
"""
build_subdir('common', 'build_common.py')
""")

    pass





@managed_target
@depends_on(common)
def datastreams(**kwargs):

    ip.runlines(
"""
build_subdir('datastreams', 'build_datastreams.py')
""")

    pass





@managed_target
@depends_on(common)
def gsched(**kwargs):

    ip.runlines(
"""
build_subdir('gsched', 'build_gsched.py')
""")

    pass





@managed_target
@depends_on(common)
def ccsm(**kwargs):

    ip.runlines(
"""
build_subdir('ccsm', 'build_ccsm.py')
""")

    pass





@managed_target
@depends_on(common)
def discovery(**kwargs):

    ip.runlines(
"""
build_subdir('discovery', 'build_discovery.py')
""")

    pass





@managed_target
@depends_on(common)
def clksync(**kwargs):

    ip.runlines(
"""
build_subdir('clksync', 'build_clksync.py')
""")

    pass





@managed_target
@depends_on(common)
def netspec(**kwargs):

    ip.runlines(
"""
build_subdir('netspec', 'build_netspec.py')
""")

    pass





@managed_target
@depends_on()
def clean_subsystems(**kwargs):

    ip.runlines(
"""
KUSP_SUBSYSTEMS = ['common', 'datastreams', 'gsched', 'ccsm', 'discovery', 'clksync', 'netspec']
for subsys in KUSP_SUBSYSTEMS:
    print subsys
    build_subdir(subsys, 'build_%s.py' % subsys, target='clean_%s'% subsys)
""")

    pass





@managed_target
@depends_on(common,datastreams,gsched,ccsm,discovery,clksync,netspec)
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
