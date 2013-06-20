"""
================================================================
:mod:`datastreams_import_test` 
================================================================
    :synopsis: Checks for all of the major modules in Data
        Streams:
        
        * `dsui` 
        * `dski`
        * `namespaces`
        * `postprocess`

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>


This is a straight forward testing script for the four major Python
modules in Data Streams. The DSUI (Data Streams User Interface), and
related Post Processing tools, can work independently of DSKI (Data
Streams Kernel Interface). Meaning, that if DSKI fails, and all of the
other tests succeed then DSUI is still operational.

Execution and Error Codes
============================

The `dsui` and `dski` modules are both Python wrappers of the
respective DSUI and DSKI C libraries. If tests for both of these fail
then it is likely that libdsui and libdski are not being compiled of
installed correctly, and their C to Python bindings `dsui_mod` and
`dski_mod` built successfully. Furthermore, libdski is built against
the Data Streams Kernel Interface kernel module (dski.ko), such that
if you are compiling against a kernel that does not have DSKI, the
generation of libdski and the `dski` module will fail. This leads to
`dski` import test being the test with the highest probability of
failure, and can be disregarded if you do not with to use `dski` or
`dski` related tools subsystems(i.e. `dskictrl` and `Discovery`).

The `namespaces` and `postprocess` datastreams modules provide the
Post Processing frame work for all of Data Streams. If these are not
found, this likely indicates a larger problem, like a failed KUSP
install or that `datastreams` is not located on your
**PYTHONPATH**. These are the most critical of the errors, since they
have no way to fail by compilation, thereby signaling a more systemic
error.
"""
import sys

class DSImportErrorFlags:
    """
    Contains each of the possible exit flags
    for the Data Streams Import Test.

    +--------------------+-----------+
    |  Flag Name         |   Value   | 
    +--------------------+-----------+
    | NO_ERROR           | 0x0000    |
    +--------------------+-----------+
    | DSUI               | 0x0001    |
    +--------------------+-----------+
    | DSKI               | 0x0002    |
    +--------------------+-----------+
    | NAMESPACES         | 0x0004    |
    +--------------------+-----------+
    | POSTPROCESS        | 0x0008    |
    +--------------------+-----------+
    """
    NO_ERRORS   = 0x0000
    DSUI        = 0x0001   
    DSKI        = 0x0002    
    NAMESPACES  = 0x0004    
    POSTPROCESS = 0x0008      

if __name__ == "__main__":
    exit_error_flags = DSImportErrorFlags.NO_ERRORS
    
    try:
        from datastreams import dsui
    except(ImportError):
        print "datastreams_import_test Error(1): Data Streams Python "\
            "module `dsui' not found."
        exit_error_flags |= DSImportErrorFlags.DSUI

    try:
        from datastreams import dski
    except(ImportError):
        print "datastreams_import_test Error(2): Data Streams Python "\
            "module `dski' not found."
        exit_error_flags |= DSImportErrorFlags.DSKI

    try:
        from datastreams import namespaces
    except(ImportError):
        print "datastreams_import_test Error(4): Data Streams Python "\
            "module `namespaces' not found."
        exit_error_flags |= DSImportErrorFlags.NAMESPACES

    try:
        from datastreams import postprocess
        
    except(ImportError):
        print "datastreams_import_test Error(8): Data Streams Python "\
            "module `postprocess' not found."
        exit_error_flags |= DSImportErrorFlags.POSTPROCESS



    if exit_error_flags == DSImportErrorFlags.NO_ERRORS: 
        print "Data Streams import test succeeded, all python modules found."
    else:
        print "Data Streams import test FAILED! Please Review the error codes."
        print "Exit Code: %d" % exit_error_flags

    sys.exit(exit_error_flags)
