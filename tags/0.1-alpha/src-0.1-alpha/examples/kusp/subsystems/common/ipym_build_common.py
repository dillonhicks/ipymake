
import sys
import os

import IPython.ipapi as ipapi
ip = ipapi.get()

if ip is None:
    ip = ipapi.get(allow_dummy=True, dummy_warn=False)

from ipymake.ipymruntimecore import *

IPYM_ORIGINAL_FILE_HASH = "080f7ea9944f1aee0ffc70008826cf83221491c0" 

IPYM_ORIGINAL_FILE_NAME = """build_common.py"""

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
def libkusp_shared(**kwargs):
    ip.runlines([
                 """ldir = os.getcwd()+'/libkusp/'""",
                 """libkusp_files = ['configfile.c',""",
                 """                 'linkedlist.c',""",
                 """                 'hashtable.c',""",
                 """                 'hashtable_types.c',""",
                 """                 'misc.c',""",
                 """                 'kusp_common.c',""",
                 """                 'rdwr.c',""",
                 """                 'vector.c',""",
                 """                 'exception.c',""",
                 """                 'configverify.c',""",
                 """                 'net.c',""",
                 """                 'kusp_private.h',""",
                 """                 'preproc_lex.c',""",
                 """                 'configfile_yacc.c',""",
                 """                 'configfile_lex.c'""",
                 """                 ]""",
                 """libkusp_files = map(lambda s: ldir+s, libkusp_files)""",
                 """libkusp_files = filter(lambda s: s.endswith('.c'), libkusp_files)""",
                 """compile_shared_library('kusp', include_dirs=['./libkusp', './include'], *libkusp_files)""",
               ])
    pass



@depends_on()
@ipym_managed_target
def libkusp_static(**kwargs):
    ip.runlines([
                 """ldir = os.getcwd()+'/libkusp/'""",
                 """libkusp_files = ['configfile.c',""",
                 """                 'linkedlist.c',""",
                 """                 'hashtable.c',""",
                 """                 'hashtable_types.c',""",
                 """                 'misc.c',""",
                 """                 'kusp_common.c',""",
                 """                 'rdwr.c',""",
                 """                 'vector.c',""",
                 """                 'exception.c',""",
                 """                 'configverify.c',""",
                 """                 'net.c',""",
                 """                 'kusp_private.h',""",
                 """                 'preproc_lex.c',""",
                 """                 'configfile_yacc.c',""",
                 """                 'configfile_lex.c'""",
                 """                 ]""",
                 """libkusp_files = map(lambda s: ldir+s, libkusp_files)""",
                 """libkusp_files = filter(lambda s: s.endswith('.c'), libkusp_files)""",
                 """compile_shared_library('kusp', include_dirs=['./libkusp', './include'], *libkusp_files)""",
               ])
    pass



@depends_on()
@ipym_managed_target
def printconfig(**kwargs):
    ip.runlines([
                 """compile_executable('printconfig', 'libkusp/printconfig.c',""",
                 """                   include_dirs=['./libkusp', './include', IPYM_BINARY_DIR], """,
                 """                   libs=['kusp','m'])""",
               ])
    pass



@depends_on()
@ipym_managed_target
def calib(**kwargs):
    ip.runlines([
                 """compile_executable('calib', 'libperf/calib.c', """,
                 """                   include_dirs=['./libperf', './include'],""",
                 """                   libs=['kusp','m'])""",
               ])
    pass



@depends_on()
@ipym_managed_target
def pylibkusp(**kwargs):
    ip.runlines([
                 """execute_critical_command("python setup_libkusp.py -v --build -b $IPYM_BINARY_DIR --cbd=$IPYM_BINARY_DIR", "pylibkusp", "")""",
               ])
    pass



@depends_on()
@ipym_managed_target
def pykusp(**kwargs):
    ip.runlines([
                 """execute_critical_command("python setup_pykusp.py -v --build -b $IPYM_BINARY_DIR --cbd=$IPYM_BINARY_DIR", "pykusp", "")""",
               ])
    pass



@depends_on()
@ipym_managed_target
def clean_common(**kwargs):
    ip.runlines([
                 """rm -rfv $IPYM_BINARY_DIR""",
               ])
    pass



@depends_on(libkusp_shared,libkusp_static,pylibkusp,pykusp,printconfig,calib)
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

