netspec_include_dirs = ['../common/include', '../common/libkusp', './include']
netspec_link_libs = ['kusp', 'm']

libnetspec:
    compile_shared_library('netspec', './libnetspec/interface.c', include_dirs=netspec_include_dirs)
    pass

ns_syscmd:
    compile_executable('ns_syscmd', './syscmd/syscmd.c', include_dirs=netspec_include_dirs,
                            linking_libs=netspec_link_libs)
    pass    

pynetspec:
    python setup_netspec.py -v --build -b $env.current_build_path
    pass

clean_netspec:
    rm -rfv $env.current_build_path
    pass


all: libnetspec ns_syscmd pynetspec
    pass
