
import sys
import os

import IPython.ipapi as ipapi
ip = ipapi.get()

if ip is None:
    ip = ipapi.get(allow_dummy=True, dummy_warn=False)

from ipymake.ipymruntimecore import *

IPYM_ORIGINAL_FILE_HASH = "df0e04d6242eb443f17fe4a1dae0f69761789a63" 

IPYM_ORIGINAL_FILE_NAME = """build_subsystems.py"""

IPYM_COMMAND_ARGS = ""







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
def common(**kwargs):
    ip.runlines([
                 """print IPYM_COMMAND_ARGS""",
                 """build_subdir('common', 'build_common.py', cmd_args=IPYM_COMMAND_ARGS)""",
               ])
    pass



@depends_on(common)
@ipym_managed_target
def datastreams(**kwargs):
    ip.runlines([
                 """build_subdir('datastreams', 'build_datastreams.py', cmd_args=IPYM_COMMAND_ARGS)""",
               ])
    pass



@depends_on(common)
@ipym_managed_target
def gsched(**kwargs):
    ip.runlines([
                 """build_subdir('gsched', 'build_gsched.py', cmd_args=IPYM_COMMAND_ARGS)""",
               ])
    pass



@depends_on(common)
@ipym_managed_target
def ccsm(**kwargs):
    ip.runlines([
                 """build_subdir('ccsm', 'build_ccsm.py', cmd_args=IPYM_COMMAND_ARGS)""",
               ])
    pass



@depends_on(common)
@ipym_managed_target
def discovery(**kwargs):
    ip.runlines([
                 """build_subdir('discovery', 'build_discovery.py', cmd_args=IPYM_COMMAND_ARGS)""",
               ])
    pass



@depends_on(common)
@ipym_managed_target
def clksync(**kwargs):
    ip.runlines([
                 """build_subdir('clksync', 'build_clksync.py', cmd_args=IPYM_COMMAND_ARGS)""",
               ])
    pass



@depends_on(common)
@ipym_managed_target
def netspec(**kwargs):
    ip.runlines([
                 """build_subdir('netspec', 'build_netspec.py', cmd_args=IPYM_COMMAND_ARGS)""",
               ])
    pass



@depends_on()
@ipym_managed_target
def clean_subsystems(**kwargs):
    ip.runlines([
                 """KUSP_SUBSYSTEMS = ['common', 'datastreams', 'gsched', 'ccsm', 'discovery', 'clksync', 'netspec']""",
                 """for subsys in KUSP_SUBSYSTEMS:""",
                 """    print subsys""",
                 """    build_subdir(subsys, 'build_%s.py' % subsys, target='clean_%s'% subsys)""",
               ])
    pass



@depends_on(common,datastreams,gsched,ccsm,discovery,clksync,netspec)
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

