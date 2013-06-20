
#################################################################################
#
# =====================================
# IPyMake Generated Python Script  
# =====================================
#
# Created IPyMake Version: 0.2-alpha
# Timestamp: Mon Dec 14 00:46:53 2009
#
# This Python script was created with IPyMake. To run this script you
# will need to have IPython installed. To install IPython you can use
# your distributions package manager, or the Python easy_install that is
# included in the Python SetupTools "easy_install python".
#
#################################################################################

# Standard/Useful imports
import sys
import os

# Get the IPython API, we need their magic 
# to get everything to run.
import IPython.ipapi as ipapi
ip = ipapi.get()

# There isn't a ipython instance running,
# get a dummy api instance.
if ip is None:
    ip = ipapi.get(allow_dummy=True, dummy_warn=False)

from ipymake.runtimecore import *


import sys
import os
global KUSPROOT 
KUSPROOT = '.'
global LOG_PATH 
LOG_PATH = '~/tmp'
global KUSPINSTALL 
KUSPINSTALL = '/tmp/kuspinstall'
global KUSPKERNELROOT 
KUSPKERNELROOT = '.'

@depends_on()
@managed_target
def initialize(**kwargs):

    ip.runlines(
"""
print 'initializing works'
""")

    pass




@depends_on()
@managed_target
def cleanup(**kwargs):

    ip.runlines(
"""
print 'cleanup works'
""")

    pass




@depends_on()
@managed_target
def wonderland(**kwargs):

    ip.runlines(
"""
build_subdir('wonderland','alice.py','hello')
""")

    pass




@depends_on()
@managed_target
def kusp_configure(**kwargs):

    ip.runlines(
"""
print '--> Configuring Kusp'
if not os.path.exists('./build'):
    mkdir build
cd $KUSPROOT'/build'
cmake .. -DCMAKE_INSTALL_PREFIX=$KUSPINSTALL -DKERNELROOT=$KUSPKERNELROOT >& cmake.out
""")

    pass




@depends_on()
@managed_target
def kusp_build(**kwargs):

    ip.runlines(
"""
print '--> Building Kusp'
cd $KUSPROOT'/build'
make VERBOSE=1 
""")

    pass




@depends_on()
@managed_target
def random_loop(**kwargs):

    ip.runlines(
"""
for x in range(23424):
    print x
def generate_lolz():
    for x in range(2):
        for y in range(2):
            for z in range(2):
                for w in range(2):
                    yield 'lol'
for lol in generate_lolz():
    print lol
""")

    pass




@depends_on()
@managed_target
def libkusp(**kwargs):

    ip.runlines(
"""
ldir = os.getcwd()+'/libkusp/'
libkusp_files = ['configfile.c',
                 'linkedlist.c',
                 'hashtable.c',
                 'hashtable_types.c',
                 'misc.c',
                 'kusp_common.c',
                 'rdwr.c',
                 'vector.c',
                 'exception.c',
                 'configverify.c',
                 'net.c',
                 'kusp_private.h'
                 ]
libkusp_files = map(lambda s: ldir+s, libkusp_files)
libkusp_files = filter(lambda s: s.endswith('.c'), libkusp_files)
compile_shared_library('kusp', include_dirs=['libkusp'], *libkusp_files)
#compile_static_library('kusp', include_dirs=['libkusp'], *libkusp_files)
""")

    pass




@depends_on(libkusp)
@managed_target
def test_install(**kwargs):

    ip.runlines(
"""
IPYM_INSTALL_PREFIX = 'helloworld'
print IPYM_INSTALL_PREFIX
print IPYM_BINARY_INSTALL_PREFIX
for b in IPYM_COMPILED_BINARIES:
    print b
""")

    pass




@depends_on(wonderland,libkusp)
@managed_target
def hello(**kwargs):

    ip.runlines(
"""
compile_executable('helloworld', 'libkusp/hello.cpp',potatoes='yes, please', ant_farm="maybe", rutabagas='25kg')
#for bin in  IPYM_COMPILED_BINARIES:
#    print bin
#for fi in  IPYM_INSTALL_FILES:
#    print fi
""")

    pass




@depends_on()
@managed_target
def world(**kwargs):

    ip.runlines(
"""
print 'WORLD!'
""")

    pass




@depends_on(hello,world)
@managed_target
def helloworld(**kwargs):

    ip.runlines(
"""

""")

    pass




@depends_on(helloworld)
@managed_target
def kusp_install(**kwargs):

    ip.runlines(
"""
print '--> Installing Kusp'
cd $KUSPROOT'/build'
make install VERBOSE=1 
""")

    pass




@depends_on()
@managed_target
def check_examples_build_dir(**kwargs):

    ip.runlines(
"""
print 
print '--> Checking for previous build directory'
if os.path.exists(KUSPROOT+'/examples/build'):
    print '----> Examples build directory exists'
else:
    print '----> Creating new examples build directory'
    mkdir $KUSPROOT'/examples/build'
""")

    pass




@depends_on(check_examples_build_dir)
@managed_target
def examples(**kwargs):

    ip.runlines(
"""
print '--> Configuring Examples'
cd $KUSPROOT'/examples/build'
cmake .. -DCMAKE_INSTALL_PREFIX=$KUSPINSTALL >& $LOG_PATH'/kusp_install.out'
print '--> Configuration Successful'
print '--> Building Examples'
make VERBOSE=1 >& $LOG_PATH'/kuspmk_build_examples.out'
print'--> Built Examples'
""")

    pass




@depends_on()
@managed_target
def clean_examples(**kwargs):

    ip.runlines(
"""
cd $KUSPROOT'/examples'
rm -rfv build
""")

    pass




@depends_on()
@managed_target
def clean(**kwargs):

    ip.runlines(
"""
cd $KUSPROOT
rm -rfv build
""")

    pass




@depends_on()
@managed_target
def tarball(**kwargs):

    ip.runlines(
"""
print '--> Removing the build directory'
rm -rfv $KUSPROOT'/build'
print '--> Creating the source tarball'
cd ..
tar -czv kussp > kusp.tar.gz
print '--> Moving tarball to rpmbuild directory'
""")

    pass




@depends_on(tarball)
@managed_target
def rpm(**kwargs):

    ip.runlines(
"""
print '--> Executing rpmbuild'
rpmbuild -ba -vv $KUSPROOT'/rpms/kusp.spec' 
print '--> RPM Created'
""")

    pass




@depends_on(kusp_configure,kusp_build,kusp_install)
@managed_target
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
    pass


def install_hook():
    try:
        install()
    except(NameError):
        pass


def cleanup_hook():
    try:
        cleanup()
    except(NameError):
        pass
    pass


if __name__ == "__main__":
    COMMAND_STRING_TPL = """
ipython -p sh -c "from %s import *; init_hook(); %s; cleanup_hook();"
"""

    filepath = sys.argv[0] # by definition
    target = sys.argv[1]  # use optparse
    filename = os.path.basename(filepath)
    module_name = filename.split('.')[0]
    cmd_str = COMMAND_STRING_TEMPLATE % (module_name, target)
    sys.exit(os.system(cmd_str))
    


#################################################################################
#                  END AUTOMATICALLY GENERATED FILE                             
#
# Note: It is best not to edit this file, unless you know what you are 
# doing. Instead, change the input file and rerun ipymake or ipymakec.
#
#################################################################################
