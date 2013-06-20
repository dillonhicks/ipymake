
clksync_include_dirs = ['../common/include','./include']
clksync_linking_libs = ['kusp', 'pthread', 'dsui', 'm']
clksync_lib_dirs = ['../datastreams/dsui/$env.build_path']

clksyncctl:
    compile_executable('clksync', 'clksyncctl.c', include_dirs=clksync_include_dirs,
                       linking_libs=clksync_linking_libs,)
    pass

libclksyncctl:
    compile_shared_library('clksync', 'clksyncctl.c', include_dirs=clksync_include_dirs,
                       linking_libs=clksync_linking_libs, lib_dirs=clksync_lib_dirs)

    pass

pyclksync:
    ~python setup_clksync.py -v --install --prefix $env.current_build_path --cbd $env.current_build_path 
    pass

clean_clksync:
    rm -rfv $env.current_build_path
    pass

all: libclksyncctl clksyncctl pyclksync
    pass
