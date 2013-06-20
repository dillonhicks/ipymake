#! /bin/env python
"""setup_clksync.py
@author: Dillon Hicks
@summary: This script wraps the old setup script with the new setup_module.py.tpl
    template. This allow there to be extra arguments to the distutils scripts
    without too much extra ad hoc code. For example, you can specify
    extra directories (CMake Binary Dir, kernel path) and force those
    arguments to be defined. The wrapped version also takes care of distutils
    causing errors when extra arguments are passed straight to the setup_<module-name>.py
    scripts.
"""
########################################################
#
# All of the test modules will need the same options front
# end, so this can be imported where one would normally
# place the optparse template. 
#
#

def run_distutils():

    from distutils.core import setup, Extension
    
    build_dir = Params.cmake_binary_dir
    libdsui_dir = "../datastreams/dsui/build"
    libkusp_dir = "../common/build"
    
    clksync_module = Extension('clksync_mod',
        sources = ['clksyncmodule.c'],
        include_dirs = ['include',
                        '../common/include'],
        define_macros = [('CONFIG_DSUI',None)],
        library_dirs = [build_dir, libdsui_dir, libkusp_dir],
        libraries = ['dsui','kusp','pthread','m','z']
    )
    
    setup(name = 'clksync',
          version = "1.0",
          author='(Packager) Dillon Hicks',
          author_email='hhicks@ittc.ku.edu',
          url='http://ittc.ku.edu/kusp',
          description="clocksync",
          package_dir = {'':'..'},
          scripts = ["synchronize"],
          packages = ['clksync'],
         
          ext_modules = [ clksync_module ]
    )
    pass
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
            self.p.add_option("--build", action="store_const", const=True, 
                              dest="run_build", 
                              help="Turns on build mode.")
            self.p.add_option("-b", action="store", type ="string", 
                              dest="build_dir", 
                              help="The build directory path.")
            self.p.add_option("--install", action="store_const", const=True, 
                              dest="run_install", 
                              help="Turns on install mode.")
            
            self.p.add_option("--prefix", action="store", type ="string", 
                              dest="install_prefix", 
                              help="Install Prefix")
            self.p.add_option("--kernel", action="store", type="string",
                              dest="kernel_path",
                              help="Path to the kernel against which you wish to compile.")
            self.p.add_option("--cbd",  action="store", type="string",
                              dest="cmake_binary_dir",
                              help="CMake binary directory in which to look for libraries against which"
                                    " to compile.")
            # Now tell the parser about the default values of all the options
            # we just told it about
            self.p.set_defaults(
                debug_level     = 2,          
                verbose_level   = 0,
                build_dir           = None,
                run_build           = False,
                run_install         = False,
                install_prefix      = None,
                kernel_path         = None,
                cmake_binary_dir    = None
                
                )       
            
        def parse(self):
            self.options, self.args  = self.p.parse_args()
            self.debug_level         = self.options.debug_level    
            self.verbose_level       = self.options.verbose_level  
            self.build_dir           = self.options.build_dir
            self.run_build           = self.options.run_build
            self.run_install         = self.options.run_install
            self.install_prefix      = self.options.install_prefix
            self.kernel_path         = self.options.kernel_path
            self.cmake_binary_dir    = self.options.cmake_binary_dir
            
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
      debug_level        : %d
      verbose_level      : %d
      run_build          : %s
      build_dir          : %s
      run_install        : %s
      install_prefix     : %s
      kernel_path        : %s
      cmake_binary_dir   : %s
    """ 
    
            str_output = param_print_str % \
                (self.debug_level, 
                 self.verbose_level,
                 self.run_build,
                 self.build_dir,
                 self.run_install,
                 self.install_prefix,
                 self.kernel_path,
                 self.cmake_binary_dir)  
            
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
        

################################################
## These are extra options that are only needed by a few
## of the distutils setups to ensure that they run.
##            
        if not Params.cmake_binary_dir:
            # Forcing a check for the CMake binary directory.
            # This needs to be defined in order to find libraries
            # and other files within the build directory.
            #
            print "Must define the CMake binary directory --cbd=<build-dir>"
            sys.exit(1)    
##
##        if not Params.kernel_path:
##            # Forcing a check for the kernel path variable.
##            # Obvisouly used when making something that needs to compile
##            # specifically against the kernel.
##            #
##            print "Must define the kernel path --kernel=<kernel-path>"
##            sys.exit(1)            
##
#################################################

        if (Params.run_install and Params.run_build) or \
            (not Params.run_install and not Params.run_build):
            # This should never be run when both a build and an install, 
            # nor should it be run with nothing to do. So force a check for
            # conflicting install and build arguments True True and False False
            # that will cause inappropriate function, and force an exit.
            #
            print "Conflicting arguments run_build and run_install. XOR."
            sys.exit(1)
        elif Params.run_build:
            # The user has specified to run a build
            # check to make sure they have specified a build directory.
            #
            if not Params.build_dir:
                # Build directory check failed. Exit.
                #
                print "Must define the build directory when running a build -b <build-dir>"
                sys.exit(1)
            # Reset sys.argv with the correct parameters for distutils to parse
            # giving it the options verbose, tell it to build, and the path to the
            # build directory.
            #       
            sys.argv = [sys.argv[0], '-v', 'build', '-b', Params.build_dir]
        elif Params.run_install:
            # The user has specified to run an install.
            # check to make sure that the installation root prefix 
            # has been defined.
            #
            if not Params.install_prefix:
                # Installation prefix is not defined, therefore there cannot
                # be an install, exit.
                print "Must define the installation prefix when "\
                       "running the install --prefix=<install-prefix>."
                sys.exit(1)
            # Reset sys.argv with the correct parameters for distutils to parse
            # giving it the options verbose, tell it to install, and the path to the
            # install directory.
            #                 
            sys.argv = [sys.argv[0], '-v', 'install', '--prefix', Params.install_prefix]
            
        # All the arguments were parsed successfully and sys.argv
        # setup properly for distutils, so run distutils.
        #
        run_distutils()
        
    
    global Params
    Params = Params_Set()
    
    main()
