
python_discovery:
    build_python_package(auto_pkg_dir='.',
        name='discovery',
          version='1.0',
          description="Discovery!",
          url='http://ittc.ku.edu/kusp',
          scripts = ['tools/daemonTrace', 
                     'tools/traceme',
             'tools/ccsmTest',
                     'tools/nofilter',
                     'tools/smartgdb',
                     'tools/syscall_trace',
                     'tools/systemMonitor', 'tools/systemMonitorExit'])
    pass

clean_discovery:
    rm -rfv $env.current_build_path
    pass

all: python_discovery
    pass
