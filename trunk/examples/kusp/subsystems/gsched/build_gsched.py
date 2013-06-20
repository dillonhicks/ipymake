
gsched_include_dirs = ['./include','../common/include', '$env.current_build_path']

libgsched:
    compile_shared_library('gsched', 'libgsched/gsched.c', 
                           include_dirs=gsched_include_dirs)
    pass


start:
    compile_executable( 'start', 'start.c', include_dirs=gsched_include_dirs, 
                        linking_libs=['gsched'])
    pass


stop:
    compile_executable( 'stop', 'stop.c', include_dirs=gsched_include_dirs, 
                        linking_libs=['gsched'])
    pass


swig_gsched: libgsched
    cp -vu --force ./libgsched/gsched.i $env.current_build_path
    cp -vu --force ./libgsched/gsched.c $env.current_build_path
    ~swig -python $env.current_build_path/gsched.i
    #~python setup_groupsched.py -v --build -b $env.current_build_path --cbd $env.current_build_path
    pass


pygsched: swig_gsched
    gsched_ext = build_python_extension('_gsched',
                           sources=[env.current_build_path+'/gsched_wrap.c', 
                                    env.current_build_path+'/gsched.c'],
                           include_dirs = ['./include'],
                           libraries = ['gsched'],
                           extra_compile_args = ['-fPIC'],
                           library_dirs = [env.current_build_path])

    build_python_package(auto_pkg_dir='pygsched',
                         name='pygsched',
                         version='1.0',
                         description="Group Scheduling Python API bindings.",
                         url='http://www.ittc.ku.edu/kusp',
                         include_dirs = ['./include'],
                         ext_modules = [gsched_ext],
                         scripts = ['tools/gschedctrl',
                                    'tools/gschedexec',
                                    'tools/gschedpprint',
                                    'tools/gschedsnapshot',
                                    'tools/gschedsh',
                                    ])
    pass


clean_gsched:
    rm -rfv $env.current_build_path
    pass

all: libgsched start stop swig_gsched pygsched
    pass
