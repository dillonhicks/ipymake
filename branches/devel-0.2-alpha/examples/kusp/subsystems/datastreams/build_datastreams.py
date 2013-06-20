
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

clean_datastreams:
    rm -rfv $env.current_build_path
    pass

all: dski dsui swig_setup pydatastreams
    pass
