"""
--------------------------------------------
# proc_ccsm.py

Format /proc/ccsm to be human readable.

--------------------------------------------
"""

def read_proc():
    f = open('/proc/ccsm', 'r')
    result = f.read(100)
    f.close()
    return result

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
        
            # Now tell the parser about the default values of all the options
            # we just told it about
            self.p.set_defaults(
                debug_level     = 0,          
                verbose_level   = 0,          
                outfile         = sys.stdout, 
                outfile_name    = None)       
            
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

        read_proc()

    ######################################################
    # This module was called as a program, and so we call
    # create a parameter class instance and the main()
    # function
    ######################################################

    Params = Params_Set()
    main()
