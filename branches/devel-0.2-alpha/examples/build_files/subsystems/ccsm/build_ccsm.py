
libccsm:
    compile_shared_library('ccsm', 'libccsm/ccsm.c', include_dirs=['./include'])

clean_ccsm:
    rm -rfv $IPYM_BINARY_DIR

all: libccsm
    pass
