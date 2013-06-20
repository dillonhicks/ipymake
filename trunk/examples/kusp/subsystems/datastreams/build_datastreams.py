
dski:
    pass

dsui:
    build_subdir('dsui','build_dsui.py')
    pass

swig_setup:
    ~swig -python pydsui_backend.i
    pass

pydatastreams: dsui swig_setup
    ~python setup_datastreams.py -v --build -b $env.current_build_path --kernel $env.current_build_path --cbd $env.current_build_path
    pass

pydstream:
    libdsui_dir = env.current_build_path
    libkusp_dir = "../common/build"
    
    pydsui_backend_module = build_python_extension('_pydsui_backend',
                        sources = ['pydsui_backend.c', 
                                   'pydsui_backend_wrap.c'],
        include_dirs = ['./include', 
                        './pydstream',
                        './dsui/libdsui', 
                        "../common/include", 
                        "../common/libkusp"],
        libraries = ['dsui', 'kusp', 'pthread','m','z'],
        library_dirs = [libdsui_dir, libkusp_dir] )
    

    dsui_module = build_python_extension('dsui_mod',
        sources = ['pydstream/dsuimodule.c'],
        include_dirs = ['./include', 
                        './pydstream',
                        './dsui/libdsui', 
                        "../common/include", 
                        "../common/libkusp"],
        libraries = ['dsui', 'kusp', 'pthread','m','z'],
        library_dirs = [libdsui_dir, libkusp_dir] )
    
    
    dski_module = build_python_extension('dski_mod',
            sources = ['pydstream/dskimodule.c'],
            include_dirs = ['include',
                            'dski/linux', 
                            'pydstream',
                            'dski/libdski'
                            'dski/linux/ccsm_filters',
                            'dski/linux/tools', 
                            "../common/include", 
                            "../common/libkusp",],
                            #Params.kernel_path+'/include'],
            libraries = [ 'pthread','m','z'],
            library_dirs = [ env.current_build_path] )
       
    build_python_package(auto_pkg_dir='.',
          name = "datastreams",
          version = "1.0",
          author='(Packager) Dillon Hicks',
          author_email='hhicks@ittc.ku.edu',
          url='http://ittc.ku.edu/kusp',
          description="Datastreams Python Tools.",

          scripts = ["postprocess/postprocess",
                   "dsui/tools/dsui-header",
                   "dski/dskid/dskid",
                   "dski/dskid/dskictrl",
                   "dski/dskid/dskitrace" ],
                              
          ext_modules = [ pydsui_backend_module,
                          dsui_module, 
                          dski_module ] )


    pass

clean_datastreams:
    rm -rfv $env.current_build_path
    pass

all: dski dsui swig_setup pydstream
    pass
