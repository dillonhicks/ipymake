
libkusp_shared:
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
                     'kusp_private.h',
                     'preproc_lex.c',
                     'configfile_yacc.c',
                     'configfile_lex.c'

                     ]

    libkusp_files = map(lambda s: ldir+s, libkusp_files)
    libkusp_files = filter(lambda s: s.endswith('.c'), libkusp_files)
    compile_shared_library('kusp', include_dirs=['./libkusp', './include'], *libkusp_files)



libkusp_static:
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
                     'kusp_private.h',
                     'preproc_lex.c',
                     'configfile_yacc.c',
                     'configfile_lex.c'
                     ]

    libkusp_files = map(lambda s: ldir+s, libkusp_files)
    libkusp_files = filter(lambda s: s.endswith('.c'), libkusp_files)
    compile_shared_library('kusp', include_dirs=['./libkusp', './include'], *libkusp_files)



printconfig:
    compile_executable('printconfig', 'libkusp/printconfig.c',
                       include_dirs=['./libkusp', './include', IPYM_BINARY_DIR], 
                       libs=['kusp','m'])

calib:
    compile_executable('calib', 'libperf/calib.c', 
                       include_dirs=['./libperf', './include'],
                       libs=['kusp','m'])

pylibkusp:
    ~python setup_libkusp.py -v --build -b $IPYM_BINARY_DIR --cbd=$IPYM_BINARY_DIR

pykusp:
    ~python setup_pykusp.py -v --build -b $IPYM_BINARY_DIR --cbd=$IPYM_BINARY_DIR
    

clean_common:
    rm -rfv $IPYM_BINARY_DIR

all: libkusp_shared libkusp_static pylibkusp pykusp printconfig calib
    pass
