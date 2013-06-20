
libccsm:
    compile_shared_library('ccsm', 'libccsm/ccsm.c', include_dirs=['./include'])
    pass

swig_ccsm:
    cp -vu --force ./libccsm/ccsm.i $env.current_build_path
    cp -vu --force ./libccsm/ccsm.c $env.current_build_path
    ~swig -python $env.current_build_path/ccsm.i
    pass

pyccsm: swig_ccsm
    ccsm_ext = build_python_extension('_ccsm',
                           sources=[env.current_build_path+'/ccsm_wrap.c', 
                                    env.current_build_path+'/ccsm.c'],
                           include_dirs = ['./include'],
                           libraries = ['ccsm'],
                           extra_compile_args = ['-fPIC'],
                           library_dirs = [env.current_build_path])

    build_python_package(auto_pkg_dir='pyccsm',
                         name='pyccsm',
                         version='1.0',
                         description="CCSM  Python API bindings.",
                         url='http://www.ittc.ku.edu/kusp',
                         include_dirs = ['include'],
                         scripts = ['tools/ccsmsh'],
                         ext_modules = [ccsm_ext])
    pass




clean_ccsm:
    rm -rfv $env.current_build_path
    pass

all: libccsm swig_ccsm pyccsm
    pass
