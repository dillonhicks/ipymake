
import sys
import os

import IPython.ipapi as ipapi
ip = ipapi.get()

if ip is None:
    ip = ipapi.get(allow_dummy=True, dummy_warn=False)

from ipymake.ipymruntimecore import *

IPYM_ORIGINAL_FILE_HASH = "992ff940a7bad2ff4e571822e787d6e10878140d" 

IPYM_ORIGINAL_FILE_NAME = """alice.py"""

IPYM_COMMAND_ARGS = ""

import sys

import os






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
def kusp_configure(**kwargs):
    ip.runlines([
                 """print '--> Configuring Kusp'""",
                 """if not os.path.exists('./build'):""",
                 """    mkdir build""",
                 """cd $KUSPROOT'/build'""",
                 """execute_critical_command("cmake .. -DCMAKE_INSTALL_PREFIX=$KUSPINSTALL -DKERNELROOT=$KUSPKERNELROOT >& cmake.out", "kusp_configure", "")""",
               ])
    pass



@depends_on()
@ipym_managed_target
def kusp_build(**kwargs):
    ip.runlines([
                 """print '--> Building Kusp'""",
                 """cd $KUSPROOT'/build'""",
                 """execute_critical_command("make VERBOSE=1 ", "kusp_build", "")""",
               ])
    pass



@depends_on()
@ipym_managed_target
def random_loop(**kwargs):
    ip.runlines([
                 """for x in range(23424):""",
                 """    print x""",
                 """def generate_lolz():""",
                 """    for x in range(2):""",
                 """        for y in range(2):""",
                 """            for z in range(2):""",
                 """                for w in range(2):""",
                 """                    yield 'lol'""",
                 """for lol in generate_lolz():""",
                 """    print lol""",
                 """store""",
                 """from pprint import pprint""",
                 """pprint( _ip.user_ns)""",
               ])
    pass



@depends_on()
@ipym_managed_target
def libkusp(**kwargs):
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
                 """                 'kusp_private.h'""",
                 """                 ]""",
                 """libkusp_files = map(lambda s: ldir+s, libkusp_files)""",
                 """libkusp_files = filter(lambda s: s.endswith('.c'), libkusp_files)""",
                 """compile_shared_library('kusp', include_dirs=['libkusp'], *libkusp_files)""",
                 """compile_static_library('kusp', include_dirs=['libkusp'], *libkusp_files)""",
               ])
    pass



@depends_on(libkusp)
@ipym_managed_target
def test_install(**kwargs):
    ip.runlines([
                 """IPYM_INSTALL_PREFIX = 'helloworld'""",
                 """print IPYM_INSTALL_PREFIX""",
                 """print IPYM_BINARY_INSTALL_PREFIX""",
                 """for b in IPYM_COMPILED_BINARIES:""",
                 """    print b""",
               ])
    pass



@depends_on(libkusp)
@ipym_managed_target
def hello(**kwargs):
    ip.runlines([
                 """compile_executable('helloworld', 'libkusp/hello.cpp',potatoes='yes, please', ant_farm="maybe", rutabagas='25kg')""",
                 """#for bin in  IPYM_COMPILED_BINARIES:""",
                 """#    print bin""",
                 """#for fi in  IPYM_INSTALL_FILES:""",
                 """#    print fi""",
               ])
    pass



@depends_on()
@ipym_managed_target
def world(**kwargs):
    ip.runlines([
                 """print 'WORLD!'""",
               ])
    pass



@depends_on(hello,world)
@ipym_managed_target
def helloworld(**kwargs):
    ip.runlines([
               ])
    pass



@depends_on(helloworld)
@ipym_managed_target
def kusp_install(**kwargs):
    ip.runlines([
                 """print '--> Installing Kusp'""",
                 """cd $KUSPROOT'/build'""",
                 """execute_critical_command("make install VERBOSE=1 ", "kusp_install", "")""",
               ])
    pass



@depends_on()
@ipym_managed_target
def check_examples_build_dir(**kwargs):
    ip.runlines([
                 """print """,
                 """print '--> Checking for previous build directory'""",
                 """if os.path.exists(KUSPROOT+'/examples/build'):""",
                 """    print '----> Examples build directory exists'""",
                 """else:""",
                 """    print '----> Creating new examples build directory'""",
                 """    mkdir $KUSPROOT'/examples/build'""",
               ])
    pass



@depends_on(check_examples_build_dir)
@ipym_managed_target
def examples(**kwargs):
    ip.runlines([
                 """print '--> Configuring Examples'""",
                 """cd $KUSPROOT'/examples/build'""",
                 """execute_critical_command("cmake .. -DCMAKE_INSTALL_PREFIX=$KUSPINSTALL >& $LOG_PATH'/kusp_install.out'", "examples", "")""",
                 """print '--> Configuration Successful'""",
                 """print '--> Building Examples'""",
                 """execute_critical_command("make VERBOSE=1 >& $LOG_PATH'/kuspmk_build_examples.out'", "examples", "")""",
                 """print'--> Built Examples'""",
               ])
    pass



@depends_on()
@ipym_managed_target
def clean_examples(**kwargs):
    ip.runlines([
                 """cd $KUSPROOT'/examples'""",
                 """rm -rfv build""",
               ])
    pass



@depends_on()
@ipym_managed_target
def clean(**kwargs):
    ip.runlines([
                 """cd $KUSPROOT""",
                 """rm -rfv build""",
               ])
    pass



@depends_on()
@ipym_managed_target
def tarball(**kwargs):
    ip.runlines([
                 """print '--> Removing the build directory'""",
                 """rm -rfv $KUSPROOT'/build'""",
                 """print '--> Creating the source tarball'""",
                 """cd ..""",
                 """execute_critical_command("tar -czv kussp > kusp.tar.gz", "tarball", "")""",
                 """print '--> Moving tarball to rpmbuild directory'""",
               ])
    pass



@depends_on(tarball)
@ipym_managed_target
def rpm(**kwargs):
    ip.runlines([
                 """print '--> Executing rpmbuild'""",
                 """execute_critical_command("rpmbuild -ba -vv $KUSPROOT'/rpms/kusp.spec' ", "rpm", "")""",
                 """print '--> RPM Created'""",
               ])
    pass



@depends_on(kusp_configure,kusp_build,kusp_install)
@ipym_managed_target
def all(**kwargs):
    ip.runlines([
               ])
    pass



@depends_on()
@ipym_managed_target
def cleanup(**kwargs):
    ip.runlines([
                 """print 'cleanup works'""",
               ])
    pass



@depends_on()
@ipym_managed_target
def initialize(**kwargs):
    ip.runlines([
                 """print 'initializing works'""",
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

