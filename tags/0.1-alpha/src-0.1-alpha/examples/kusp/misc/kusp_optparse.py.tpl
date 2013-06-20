########################################################
#
# All of the test modules will need the same options front
# end, so this can be imported where one would normally
# place the optparse template. 
#
#

if __name__ == '__main__':
    # imports required if this module is called as a
    # command
    import optparse, sys, os
    from pprint import *
    
    # Define the set of permitted parameters, including the
    # command arguments.  The initialization method creates
    # the parser and defines the defaults. The parse()
    # method actually parses the arguments one the command
    # line. This was done so that the instance of the class
    # could be global and thus available to all
    # routines. and then parse the arguments to this call
    # according to the specification
    class Params_Set:
        USAGE = "usage: %prog [options]"
    
        def __init__(self):
            # Create the argument parser and then tell it
            # about the set of legal arguments for this
            # command. The parse() method of this class
            # calls parse_args of the optparse module
            self.p = optparse.OptionParser(usage=self.USAGE)
    
            # Boring and totally standard verbose and
            # debugging options that should be common to
            # virtually any command
            #
            self.p.add_option("-d", action="store_const", const=1,        
                              dest="debug_level", 
                              help="Turn on diagnostic output at level 1")
            self.p.add_option("-D", action="store", type ="int",    
                              dest="debug_level", 
                              help="Turn on diagnostic output at level DEBUG_LEVEL")
            self.p.add_option("-v", action="store_const", const=1,        
                              dest="verbose_level", 
                              help="Turn on narrative output at level 1")
            self.p.add_option("-V", action="store", type ="int",    
                              dest="verbose_level", 
                              help="Turn on narrative output at level VERBOSE_LEVEL")
            
            # Command specific options. We can specify a
            # configuration file to parse, which defaults to
            # stdin, and an output file name, which defaults
            # to stdout.
            self.p.add_option("-p", "--prefix", action="store", type ="string", 
                              dest="prefix", 
                              help="Search and remove all kusp files (not directories) at PREFIX")
    
    
        
            # Now tell the parser about the default values of all the options
            # we just told it about
            self.p.set_defaults(
                debug_level     = 0,          
                verbose_level   = 0,
                prefix          = '/usr'
                )       
            
        def parse(self):
            self.options, self.args = self.p.parse_args()
            self.debug_level     = self.options.debug_level    
            self.verbose_level   = self.options.verbose_level  
            self.prefix          = self.options.prefix
            
            # Output option details if debugging level is high enough
            if self.debug_level >= 3 :
                print
                print "Options: ", self.options
                print "Args: ", self.args
    
        # Defining this method defines the string representation of the
        # object when given as an argument to str() or the "print" command
        #cd
        def __str__(self):
            param_print_str = \
    """Parameters:
      debug_level    : %d
      verbose_level  : %d
      prefix         : %s
    """ 
    
            str_output = param_print_str % \
                (self.debug_level, 
                 self.verbose_level,
                 self.prefix)  
            
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
        debug_level = Params.debug_level
        if Params.debug_level >= 2:
            print Params
        
        print 'This is the Optparse template!'
        print 'Add your code here.'
            
        
        
        
    
    global Params
    Params = Params_Set()
    
    main()