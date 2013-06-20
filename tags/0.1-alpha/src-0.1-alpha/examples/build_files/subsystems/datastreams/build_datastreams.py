
dski:
    pass

dsui:
    build_subdir('dsui','build_dsui.py')
    pass

swig_setup:
    ~swig -python pydsui_backend.i
    pass

pydatastreams: dsui swig_setup
    ~python setup_datastreams.py -v --build -b $IPYM_BINARY_DIR --kernel $IPYM_BINARY_DIR --cbd $IPYM_BINARY_DIR
    pass

clean_datastreams:
    rm -rfv $IPYM_BINARY_DIR

all: dski dsui swig_setup pydatastreams
    pass
