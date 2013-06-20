
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
    pass


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
    pass


printconfig:
    compile_executable('printconfig', 'libkusp/printconfig.c',
                       include_dirs=['./libkusp', './include', env.current_build_path], 
                       libs=['kusp','m'])
    pass

calib:
    compile_executable('calib', 'libperf/calib.c', 
                       include_dirs=['./libperf', './include'],
                       libs=['kusp','m'])
    pass

pylibkusp:
    ~python setup_libkusp.py -v --build -b $env.current_build_path --cbd=$env.current_build_path
    pass

pykusp:
    ~python setup_pykusp.py -v --build -b $env.current_build_path --cbd=$env.current_build_path
    pass

clean_common:
    rm -rfv $env.current_build_path
    pass

all: libkusp_shared libkusp_static pylibkusp pykusp printconfig calib
    pass
