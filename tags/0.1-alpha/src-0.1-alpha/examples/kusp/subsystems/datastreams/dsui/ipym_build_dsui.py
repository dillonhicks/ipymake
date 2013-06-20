
import sys
import os

import IPython.ipapi as ipapi
ip = ipapi.get()

if ip is None:
    ip = ipapi.get(allow_dummy=True, dummy_warn=False)

from ipymake.ipymruntimecore import *

IPYM_ORIGINAL_FILE_HASH = "60fd4e70c89fb2c68f94148d8a906577a223b9ff" 

IPYM_ORIGINAL_FILE_NAME = """build_dsui.py"""

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
def libdsui(**kwargs):
    ip.runlines([
                 """libdsui_files = [""",
                 """    'dstrm_buffer.c', """,
                 """    'dstrm_buffer.h', """,
                 """    'buffer_thread.c', """,
                 """    'buffer_thread.h', 	""",
                 """    'logging_thread.c', """,
                 """    'logging_thread.h',""",
                 """    'pool.c',""",
                 """    'pool.h',""",
                 """    'buffer_queue.c',""",
                 """    'buffer_queue.h', """,
                 """    'dsui.c',""",
                 """    'filters.h',""",
                 """    'filters.c', """,
                 """    'entity.c',""",
                 """    'entity.h', """,
                 """    'datastream.c',""",
                 """    'datastream.h',""",
                 """    'clksyncapi.c',""",
                 """    'dstream_header.c',""",
                 """    'log_functions.c' ]""",
                 """libdsui_files = filter(lambda s: not s.endswith('.h'), libdsui_files)""",
                 """libdsui_files = map(lambda s: './libdsui/'+s, libdsui_files)""",
                 """compile_static_library('dsui', include_dirs=['libdsui', '../include', '../../common/include'], *libdsui_files)""",
               ])
    pass



@depends_on(libdsui)
@ipym_managed_target
def all(**kwargs):
    ip.runlines([
                 """print 'HELLO WORLD'""",
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

