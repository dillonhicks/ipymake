
python_discovery:
    ~python setup_discovery.py -v --build -b $IPYM_BINARY_DIR
    pass

    
clean_discovery:
    rm -rfv $IPYM_BINARY_DIR
    pass

all: python_discovery
    pass
