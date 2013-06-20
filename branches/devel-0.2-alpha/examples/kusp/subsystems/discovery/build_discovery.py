
python_discovery:
    ~python setup_discovery.py -v --build -b $env.current_build_path
    pass

clean_discovery:
    rm -rfv $env.current_build_path
    pass

all: python_discovery
    pass
