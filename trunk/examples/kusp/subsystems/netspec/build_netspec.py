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
    build_python_package(auto_pkg_dir='.',
                         name = "netspec",
                         version = "2.0",
                         description = "NETSPEC!",
                         scripts = ["netspecd", "ns_control"])


    pass

clean_netspec:
    rm -rfv $env.current_build_path
    pass


all: libnetspec ns_syscmd pynetspec
    pass
