
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
    libdsui_dir = "../datastreams/dsui/build"
    libkusp_dir = "../common/build"
    
    clksync_module = build_python_extension('clksync_mod',
        sources = ['clksyncmodule.c'],
        include_dirs = ['include',
                        '../common/include'],
        define_macros = [('CONFIG_DSUI',None)],
        library_dirs = [env.current_build_path, libdsui_dir, libkusp_dir],
        libraries = ['dsui','kusp','pthread','m','z']
    )
    
    build_python_package(auto_pkg_dir='.',
          name = 'clksync',
          version = "1.0",
          author='(Packager) Dillon Hicks',
          author_email='hhicks@ittc.ku.edu',
          url='http://ittc.ku.edu/kusp',
          description="clocksync",
          scripts = ["synchronize"],
          ext_modules = [ clksync_module ]
    )
 

    pass

clean_clksync:
    rm -rfv $env.current_build_path
    pass

all: libclksyncctl clksyncctl pyclksync
    pass
