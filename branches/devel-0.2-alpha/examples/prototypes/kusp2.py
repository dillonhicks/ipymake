
import sys
import os

KUSPROOT = '.'
LOG_PATH = '~/tmp'
KUSPINSTALL = '/tmp/kuspinstall'
KUSPKERNELROOT = '.'


initialize:
    print 'initializing works'
    pass

cleanup:
    print 'cleanup works'
    pass

wonderland:
    build_subdir('wonderland','alice.py','hello')
    pass

kusp_configure:
    print '--> Configuring Kusp'
    if not os.path.exists('./build'):
        mkdir build
    cd $KUSPROOT'/build'
    ~cmake .. -DCMAKE_INSTALL_PREFIX=$KUSPINSTALL -DKERNELROOT=$KUSPKERNELROOT >& cmake.out
    pass

kusp_build: 
    print '--> Building Kusp'
    cd $KUSPROOT'/build'
    ~make VERBOSE=1 
    pass

random_loop:
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
    pass


libkusp:
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
    pass

test_install: libkusp
    IPYM_INSTALL_PREFIX = 'helloworld'
    print IPYM_INSTALL_PREFIX
    print IPYM_BINARY_INSTALL_PREFIX
    for b in IPYM_COMPILED_BINARIES:
        print b
    pass
    

hello: wonderland libkusp
    compile_executable('helloworld', 'libkusp/hello.cpp',potatoes='yes, please', ant_farm="maybe", rutabagas='25kg')

    #for bin in  IPYM_COMPILED_BINARIES:
    #    print bin
    #for fi in  IPYM_INSTALL_FILES:
    #    print fi
    pass

world:
    print 'WORLD!'
    pass


helloworld: hello world
    pass

kusp_install: helloworld
    print '--> Installing Kusp'
    cd $KUSPROOT'/build'
    ~make install VERBOSE=1 

    pass


check_examples_build_dir: 
    print 
    print '--> Checking for previous build directory'
    if os.path.exists(KUSPROOT+'/examples/build'):
        print '----> Examples build directory exists'
    else:
        print '----> Creating new examples build directory'
        mkdir $KUSPROOT'/examples/build'
    pass


examples: check_examples_build_dir
    print '--> Configuring Examples'
    cd $KUSPROOT'/examples/build'
    ~cmake .. -DCMAKE_INSTALL_PREFIX=$KUSPINSTALL >& $LOG_PATH'/kusp_install.out'
    print '--> Configuration Successful'
    print '--> Building Examples'
    ~make VERBOSE=1 >& $LOG_PATH'/kuspmk_build_examples.out'
    print'--> Built Examples'
    pass
    

clean_examples:
    cd $KUSPROOT'/examples'
    rm -rfv build
    
    pass


clean:
    cd $KUSPROOT
    rm -rfv build
    pass

tarball:
    print '--> Removing the build directory'
    rm -rfv $KUSPROOT'/build'
    print '--> Creating the source tarball'
    cd ..
    ~tar -czv kussp > kusp.tar.gz
    print '--> Moving tarball to rpmbuild directory'
    pass

rpm: tarball
    print '--> Executing rpmbuild'
    ~rpmbuild -ba -vv $KUSPROOT'/rpms/kusp.spec' 
    print '--> RPM Created'
    pass

all: kusp_configure kusp_build kusp_install
    pass

