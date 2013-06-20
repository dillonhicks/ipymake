
libccsm:
    compile_shared_library('ccsm', 'libccsm/ccsm.c', include_dirs=['./include'])
    pass

clean_ccsm:
    rm -rfv $env.current_build_path
    pass

all: libccsm
    pass
