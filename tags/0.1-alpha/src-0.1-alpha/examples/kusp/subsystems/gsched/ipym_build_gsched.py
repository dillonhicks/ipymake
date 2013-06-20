
import sys
import os

import IPython.ipapi as ipapi
ip = ipapi.get()

if ip is None:
    ip = ipapi.get(allow_dummy=True, dummy_warn=False)

from ipymake.ipymruntimecore import *

IPYM_ORIGINAL_FILE_HASH = "92dcd6bee2609e22df8f5618a9cc02dc679494e8" 

IPYM_ORIGINAL_FILE_NAME = """build_gsched.py"""

IPYM_COMMAND_ARGS = ""



ip.runlines(["global gsched_include_dirs "])
ip.runlines(["gsched_include_dirs = ['./include','../common/include']"])



ip.runlines("""
IPYM_INSTALL_PREFIX = '~/tmp'
IPYM_BINARY_PREFIX = '/bin'
IPYM_LIBRARY_PREFIX = '/lib'
IPYM_INCLUDE_PREFIX = '/include'
IPYM_SHARE_PREFIX = '/share'
IPYM_BINARY_DIR = './build'


class DynamicPrefixString:
    def __init__(self, static_suffix):
        self._static_suffix = static_suffix

    def __str__(self):
        return IPYM_INSTALL_PREFIX + self._static_suffix


IPYM_BINARY_INSTALL_PREFIX = DynamicPrefixString(IPYM_BINARY_PREFIX)
IPYM_LIBRARY_INSTALL_PREFIX = DynamicPrefixString(IPYM_LIBRARY_PREFIX)
IPYM_INCLUDE_INSTALL_PREFIX = DynamicPrefixString(IPYM_INCLUDE_PREFIX)
IPYM_SHARE_INSTALL_PREFIX = DynamicPrefixString(IPYM_SHARE_PREFIX)
""")





@depends_on()
@ipym_managed_target
def libgsched(**kwargs):
    ip.runlines([
                 """compile_shared_library('gsched', 'libgsched/gsched.c', include_dirs=gsched_include_dirs)""",
               ])
    pass



@depends_on()
@ipym_managed_target
def start(**kwargs):
    ip.runlines([
                 """compile_executable( 'start', 'start.c', include_dirs=gsched_include_dirs, libs=['gsched'])""",
               ])
    pass



@depends_on()
@ipym_managed_target
def stop(**kwargs):
    ip.runlines([
                 """compile_executable( 'stop', 'stop.c', include_dirs=gsched_include_dirs, libs=['gsched'])""",
               ])
    pass



@depends_on(libgsched)
@ipym_managed_target
def swig_gsched(**kwargs):
    ip.runlines([
                 """cp -vu --force ./libgsched/gsched.i $IPYM_BINARY_DIR/""",
                 """cp -vu --force ./libgsched/gsched.c $IPYM_BINARY_DIR/""",
                 """execute_critical_command("swig -python $IPYM_BINARY_DIR/gsched.i", "swig_gsched", "")""",
                 """execute_critical_command("python setup_groupsched.py -v --build -b $IPYM_BINARY_DIR --cbd $IPYM_BINARY_DIR", "swig_gsched", "")""",
               ])
    pass



@depends_on()
@ipym_managed_target
def clean_gsched(**kwargs):
    ip.runlines([
                 """rm -rfv $IPYM_BINARY_DIR""",
               ])
    pass



@depends_on(libgsched,start,stop,swig_gsched)
@ipym_managed_target
def all(**kwargs):
    ip.runlines([
               ])
    pass



def ipym_cleanup():
    try:
        cleanup()
    except(NameError):
        pass
    #print 'Done!'
    pass



#def ipym_clean_build():
#    try:
#        clean()
#    except(NameError):
#        ip.runlines(["rm -rfv $IPYM_BINARY_DIR/* "])
#    pass




def ipym_initialize(**kwargs):
    #print 'Initializing build environment.'
    if kwargs['recompile']:
        ip.runlines("IPYM_COMMAND_ARGS = ' --force-recompile '")
    else:
        ip.runlines("IPYM_COMMAND_ARGS = '' ")

    try:
        initialize(**kwargs)
    except(NameError):
        pass
    pass

