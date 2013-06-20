import sys

try:
    from pyccsm import ccsmapi
except(ImportError):
    print "ccsm_import_test Error(1): CCSM Python "\
        "module `ccsmapi' not found."
    sys.exit(1)

try:
    from pyccsm import ccsmstructures
except(ImportError):
    print "ccsm_import_test Error(2): CCSM Python "\
        "module `ccsmstructures' not found."
    sys.exit(2)

try:
    from pyccsm import ccsmprocutils
except(ImportError):
    print "ccsm_import_test Error(3): CCSM Python "\
        "module `ccsmprocutils' not found."
    sys.exit(3)

try:
    from pyccsm import ccsmgraphviz
except(ImportError):
    print "ccsm_import_test Error(4): CCSM Python "\
        "module `ccsmgraphviz' not found."
    sys.exit(4)


print "CCSM import test succeeded, all python modules found."
sys.exit(0)
