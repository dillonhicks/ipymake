"""
--------------------------------------------
# ccsm_tests.py

CCSM regression tests

--------------------------------------------
"""

import sys
import os
import optparse
import signal
import time
import pyccsm.ccsmapi as ccsm
import proc_ccsm

Params = None

def print_verbose(txt):
    if Params is not None:
        if Params.verbose_level > 0:
            time.sleep(10)
            print txt

class CcsmTest():

    def __init__(self):
        self.set_name1 = 'ccsm_test_set1'
        self.set_name2 = 'ccsm_test_set2'
        self.pid = os.getpid()

    def print_ccsm_info(self):
        print_verbose(proc_ccsm.read_proc())

    def create_set(self):
        ccsm_fd = ccsm.ccsm_open()

        ccsm.ccsm_create_set(ccsm_fd, self.set_name1,0)

        self.print_ccsm_info()

        ccsm.ccsm_destroy_set(ccsm_fd, self.set_name1)
        
        self.print_ccsm_info()

        ccsm.ccsm_close(ccsm_fd)

    def create_name(self):
        
        ccsm_fd = ccsm.ccsm_open()

        ccsm.ccsm_create_component_self(ccsm_fd, self.set_name1)

        self.print_ccsm_info()

        ccsm.ccsm_destroy_component_by_name(ccsm_fd, self.set_name1)

        self.print_ccsm_info()

        ccsm.ccsm_close(ccsm_fd)

    def create_pid(self):

        ccsm_fd = ccsm.ccsm_open()

        ccsm.ccsm_create_component_by_pid(ccsm_fd, self.set_name1, self.pid)

        self.print_ccsm_info()

        ccsm.ccsm_destroy_component_by_pid(ccsm_fd, self.pid)   

        self.print_ccsm_info()

        ccsm.ccsm_close(ccsm_fd)

    def name_pid(self):

        ccsm_fd = ccsm.ccsm_open()

        ccsm.ccsm_create_component_self(ccsm_fd, self.set_name1)

        self.print_ccsm_info()

        ccsm.ccsm_destroy_component_by_pid(ccsm_fd, self.pid)

        self.print_ccsm_info()

        ccsm.ccsm_close(ccsm_fd)

    def pid_name(self):

        ccsm_fd = ccsm.ccsm_open()

        ccsm.ccsm_create_component_by_pid(ccsm_fd, self.set_name1, self.pid)

        self.print_ccsm_info()

        ccsm.ccsm_destroy_component_by_name(ccsm_fd, self.set_name1)

        self.print_ccsm_info()

        ccsm.ccsm_close(ccsm_fd)

    def add_name(self):

        ccsm_fd = ccsm.ccsm_open()

        ccsm.ccsm_create_set(ccsm_fd, self.set_name1,0)

        self.print_ccsm_info()

        ccsm.ccsm_create_component_self(ccsm_fd, self.set_name2)
        
        self.print_ccsm_info()

        ccsm.ccsm_add_member(ccsm_fd, self.set_name1, self.set_name2)

        self.print_ccsm_info()

        ccsm.ccsm_remove_member(ccsm_fd, self.set_name1, self.set_name2)

        self.print_ccsm_info()

        ccsm.ccsm_destroy_component_by_name(ccsm_fd, self.set_name2)

        self.print_ccsm_info()

        ccsm.ccsm_destroy_set(ccsm_fd, self.set_name1)

        self.print_ccsm_info()

        ccsm.ccsm_close(ccsm_fd)

    def add_pid(self):

        ccsm_fd = ccsm.ccsm_open()

        ccsm.ccsm_create_set(ccsm_fd, self.set_name1,0)

        self.print_ccsm_info()

        ccsm.ccsm_create_component_by_pid(ccsm_fd, self.set_name1, self.pid)

        self.print_ccsm_info()

        ccsm.ccsm_add_member(ccsm_fd, self.set_name1, self.set_name2)

        self.print_ccsm_info()

        ccsm.ccsm_remove_member(ccsm_fd, self.set_name1, self.set_name2)

        self.print_ccsm_info()

        ccsm.ccsm_destroy_component_by_pid(ccsm_fd, self.pid)

        self.print_ccsm_info()

        ccsm.ccsm_destroy_set(ccsm_fd, self.set_name1)

        self.print_ccsm_info()

        ccsm.ccsm_close(ccsm_fd)


tests = {
    'create_set' : {'help' : 'Create and destroy a set', 'func' : CcsmTest.create_set },
    'create_name' : { 'help' : 'Create a set using name', 'func' : CcsmTest.create_name },
    'create_pid' : {'help' : 'Create a set using pid', 'func' : CcsmTest.create_pid},
    'add_name' : { 'help' : 'Add a set to another set by name', 'func' : CcsmTest.add_name},
    'add_pid' : { 'help' : 'Add a set to another set by pid', 'func' : CcsmTest.add_pid},
    'pid_name' : { 'help' : 'Create using pid/destroy using name', 'func' : CcsmTest.pid_name},
    'name_pid' : { 'help' : 'Create using name/destroy using pid', 'func' : CcsmTest.name_pid}
    }


########################################################
#
# If this module is called as a command then display the
# output to standard out.
########################################################

if __name__ == "__main__":
    # imports required if this module is called as a
    # command
    import optparse, sys
    from pprint import *

    # define the set of permitted parameters, including the
    # command arguments.  The initialization method creates
    # the parser and defines the defaults. The parse()
    # method actually parses the arguements one the command
    # line. This was done so that the instance of the class
    # could be global and thus available to all
    # routines. and then parse the arguments to this call
    # according to the specificaton
    class Params_Set:

        def __init__(self):
            # Create the argument parser and then tell it
            # about the set of legal arguments for this
            # command. The parse() method of this class
            # calls parse_args of the optparse module
            self.p = optparse.OptionParser()

            # Boring and totally standard verbose and
            # debugging options that should be common to
            # virtually any command
            #
            self.p.add_option("-d", action="store_const", const=1,        
                              dest="debug_level", help="Turn on diagnostic output at level 1")
            self.p.add_option("-D", action="store",       type ="int",    
                              dest="debug_level", help="Turn on diagnostic output at level DEBUG_LEVEL")
            self.p.add_option("-v", action="store_const", const=1,        
                              dest="verbose_level", help="Turn on narrative output at level 1")
            self.p.add_option("-V", action="store",       type ="int",    
                              dest="verbose_level", help="Turn on narrative output at level VERBOSE_LEVEL")

            # Command specific options
            # Output to the specified file.
            self.p.add_option("-o", action="store", type ="string", 
                              dest="outfile_name", 
                              help="Output to the file OUTFILE_NAME, over-riding stdout default")
            
            for test in tests:
                self.add_test_opt(test, tests[test]['help'])
        
            # Now tell the parser about the default values of all the options
            # we just told it about
            self.p.set_defaults(
                debug_level     = 0,          
                verbose_level   = 0,          
                outfile         = sys.stdout, 
                outfile_name    = None)       
            
        def add_test_opt(self, name, desc):
            self.p.add_option('--' + name, action='store_true', dest=name, help=desc)
            self.p.add_option('--no_' + name, action='store_false', dest=name, help='Disable the ' + name + ' test')

        def parse(self):
            self.options, self.args = self.p.parse_args()
        
            self.debug_level     = self.options.debug_level    
            self.verbose_level   = self.options.verbose_level  
            self.outfile         = self.options.outfile        
            self.outfile_name    = self.options.outfile_name  

            if self.outfile_name:
                try:
                    tmpf = open(self.outfile_name, 'w')
                    self.outfile = tmpf
                except IOError, earg:
                    print "Error opening Output file: -i %s" % (self.outfile_name)
                    print "Expection argument:", earg

            # Output option details if debugging elve is high enough
            if self.debug_level >= 3 :
                print
                print "Options: ", self.options
                print "Args: ", self.args

        # Defining this method defines the string representation of the
        # object when given as an argument to str() or the "print" command
        def __str__(self):
            param_print_str = \
"""Parameters:
  debug_level    : %d
  verbose_level  : %d
  outfile        : %s
  outfile_name   : %s
""" 

            str_output = param_print_str % \
                (self.debug_level, 
                 self.verbose_level, 
                 self.outfile, 
                 self.outfile_name)  
            return str_output

    def main():
        # Global level params class instance was
        # created before calling main(). We make it
        # global so that other code can access the set
        # of Parameters, simply by accessing the Params
        # instance. Here, however, we call the parse()
        # method to actually get the arguments, since
        # we have been called from the command line.
        Params.parse()
        
        if Params.debug_level >= 2:
            print Params
       
        tester = CcsmTest()

        all = True

        # Check if specific tests are being used.
        for test in tests:
            if vars(Params.options)[test] is True:
                all = False

        # Run the desired tests.
        for test in tests:
            # If specific tests are not enabled and this test was not specified
            # or this test was specified as enabled.
            if (all and vars(Params.options)[test] is None) or vars(Params.options)[test]:
                print 'Testing ' + test + "... "
                tests[test]['func'](tester)
                print "PASSED"

    ######################################################
    # This module was called as a program, and so we call
    # create a parameter class instance and the main()
    # function
    ######################################################

    Params = Params_Set()
    main()
