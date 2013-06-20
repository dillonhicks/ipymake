

common:
    print IPYM_COMMAND_ARGS
    build_subdir('common', 'build_common.py', cmd_args=IPYM_COMMAND_ARGS)
    pass

datastreams: common
    build_subdir('datastreams', 'build_datastreams.py', cmd_args=IPYM_COMMAND_ARGS)
    pass

gsched: common
    build_subdir('gsched', 'build_gsched.py', cmd_args=IPYM_COMMAND_ARGS)
    pass

ccsm: common
    build_subdir('ccsm', 'build_ccsm.py', cmd_args=IPYM_COMMAND_ARGS)
    pass

discovery: common
    build_subdir('discovery', 'build_discovery.py', cmd_args=IPYM_COMMAND_ARGS)
    pass

clksync: common
    build_subdir('clksync', 'build_clksync.py', cmd_args=IPYM_COMMAND_ARGS)
    pass

netspec: common
    build_subdir('netspec', 'build_netspec.py', cmd_args=IPYM_COMMAND_ARGS)
    pass

clean_subsystems:
    KUSP_SUBSYSTEMS = ['common', 'datastreams', 'gsched', 'ccsm', 'discovery', 'clksync', 'netspec']
    for subsys in KUSP_SUBSYSTEMS:
        print subsys
        build_subdir(subsys, 'build_%s.py' % subsys, target='clean_%s'% subsys)
    pass

all: common datastreams gsched ccsm discovery clksync netspec
    pass


