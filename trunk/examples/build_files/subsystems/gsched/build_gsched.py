
gsched_include_dirs = ['./include','../common/include']

libgsched:
    compile_shared_library('gsched', 'libgsched/gsched.c', include_dirs=gsched_include_dirs)
    pass


start:
    compile_executable( 'start', 'start.c', include_dirs=gsched_include_dirs, libs=['gsched'])
    pass


stop:
    compile_executable( 'stop', 'stop.c', include_dirs=gsched_include_dirs, libs=['gsched'])
    pass


swig_gsched: libgsched
    cp -vu --force ./libgsched/gsched.i $IPYM_BINARY_DIR/
    cp -vu --force ./libgsched/gsched.c $IPYM_BINARY_DIR/
    ~swig -python $IPYM_BINARY_DIR/gsched.i
    ~python setup_groupsched.py -v --build -b $IPYM_BINARY_DIR --cbd $IPYM_BINARY_DIR
    pass


clean_gsched:
    rm -rfv $IPYM_BINARY_DIR

all: libgsched start stop swig_gsched
    pass
