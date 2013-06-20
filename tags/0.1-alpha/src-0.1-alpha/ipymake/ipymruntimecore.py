import sys, os, signal
import textstyle as style
from pprint import pprint
import IPython.ipapi as ipapi

##################################################
# Global Build Environment Classes/Variables
##################################################

ip = ipapi.get()

class VerbosityLevel:
    NORMAL             = 0
    VERBOSE            = 1
    VERY_VERBOSE       = 2
    EXTREMELY_VERBOSE  = 3


IPYM_LOGFILE = 'ipymake_log.txt'
ip.runlines("logstart -or %s" % IPYM_LOGFILE)

IPYM_C_FLAGS = ['-g', '-c', '-Wall', '-fPIC']
IPYM_CXX_FLAGS = ['-g', '-c', '-Wall', '-fPIC']
IPYM_C_COMPILER = 'gcc '
IPYM_CXX_COMPILER = 'g++ '

def set_c_flags(flags):
    IPYM_C_FLAGS = flags

def set_cxx_flags(flags):
    IPYM_CXX_FLAGS = flags

# Install/Built Lists
#
IPYM_COMPILED_BINARIES = []
IPYM_INSTALL_FILES = []
IPYM_BUILT_TARGETS = {}

# System Variables
IPYM_VERBOSITY_LEVEL = VerbosityLevel.VERBOSE
IPYM_EXPECTED_EXIT_VALUE = '0'

if IPYM_VERBOSITY_LEVEL >= VerbosityLevel.EXTREMELY_VERBOSE:
    ip.runlines("system_verbose 1")


##################################################
# Helper Decorator Functions 
##################################################


def ipym_managed_target(function):
    """
    Used as a decorator for each target as some house keeping.
    Normally, each line of a typical makefile is executed in a
    different subshell, so there isn't any persistence within the
    target.  I think that the lack of environment persistence within
    in the makefile is flawed, the reverting of the environment
    between targets seems perfectly reasonable and desireable.
    """
    def ipym_managed_function(**args):
        target_name = function.__name__
        module_name = function.__module__
        term_width = _get_terminal_width()
        header_string = '%s.%s'%(module_name, target_name)
        print style.intense_black_text('='*term_width)
        print style.bold_text(header_string)
        print style.intense_black_text('='*term_width)
        push_dir = os.getcwd()
        retval = function(**args)
        if not IPYM_BUILT_TARGETS.has_key(target_name):
            IPYM_BUILT_TARGETS[target_name] = [function]
        else:
            IPYM_BUILT_TARGETS[target_name].append(function)
        os.chdir(push_dir)

        
        return retval
    ipym_managed_function.__name__ = function.__name__
    return ipym_managed_function


class depends_on:
    """
    'Decorator class' that wraps a function by sending it a list of
    other functions for which the current function is depenendent.
    When the function is called, this classes __call__ routine is
    executed first, which in turn calls all of the target's
    dependencies in order.
    """
    def __init__(self, *targets):
        self.targets = list(targets)


    def __call__(self, method):
        def resolve_dependencies(**args):
            for target in self.targets:
                target_name = target.__name__
                if not target_name in IPYM_BUILT_TARGETS.keys():
                    target(**args)
                else:
                    if target in IPYM_BUILT_TARGETS[target_name]:
                        print 'Target:', target.__name__, 'already built!'
            return method(**args)
        resolve_dependencies.__name__ = method.__name__
        return resolve_dependencies;


##################################################
# Build File Classes
##################################################

class IPYMBinaryType:
    """
    Just the names of each of the type of compiled binary/install file
    types as defined constants.
    """
    ABSTRACT = "ABSTRACT"
    EXECUTABLE = "Executable"
    SHARED_LIBRARY = "Shared Library"
    STATIC_LIBRARY = "Static Library"

class IPYMFileType:
    INCLUDE_FILE = "Include File"
    SHARE_FILE = "Share File"


class IPYMSourceType:
    C_SOURCE_FILES = ['c']
    C_HEADER_FILES = ['h']
    C_FILES =  [fi for fi in C_SOURCE_FILES+C_HEADER_FILES]
    CXX_SOURCE_FILES = ['cpp', 'cc']
    CXX_HEADER_FILES = ['h', 'hpp']
    CXX_FILES = [fi for fi in CXX_SOURCE_FILES+CXX_HEADER_FILES]

    @staticmethod
    def is_c_source(srcfile):
        return srcfile.split('.')[-1].strip() in IPYMSourceType.C_SOURCE_FILES

    @staticmethod
    def is_cxx_source(srcfile):
        return srcfile.split('.')[-1].strip() in IPYMSourceType.CXX_SOURCE_FILES


class IPYMBinary:
    def __init__(self, name, sources, options, binary):
        self.name = name
        self.sources = sources
        self.options = options
        self.type = IPYMBinaryType.ABSTRACT
        self.binary = binary

    def __str__(self):
        return \
"""
%s : %s
------------------------------------

BINARY     : %s
SOURCES    : %s
OPTIONS    : %s
""" % (self.type, self.name, self.binary,
       ', '.join(self.sources), '\n\t '.join(self.options.items()))
    

class IPYMExecutable(IPYMBinary):
    def __init__(self, name, sources, options, binary):
        IPYMBinary.__init__(self, name, sources, options, binary)
        self.type = IPYMBinaryType.EXECUTABLE

class IPYMSharedLibrary(IPYMBinary):
    def __init__(self, name, sources, options, binary):
        IPYMBinary.__init__(self, name, sources, options, binary)
        self.type = IPYMBinaryType.SHARED_LIBRARY
        

class IPYMStaticLibrary(IPYMBinary):
    def __init__(self, name, sources, options, binary):
        IPYMBinary.__init__(self, name, sources, options, binary)
        self.type = IPYMBinaryType.STATIC_LIBRARY
        
class IPYMInstallFile:
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.type = IPYMBinaryType.ABSTRACT

    def __str__(self):
        return \
"""
%s : %s
------------------------------------

LOCATION : %s
""" % (self.type, self.name, self.location)



class IPYMIncludeFile(IPYMInstallFile):
    def __init__(self, name, location):
       IPYMInstallFile.__init__(self, name, location)
       self.type = IPYMFileType.INCLUDE_FILE

class IPYMShareFile(IPYMInstallFile):
    def __init__(self, name, location):
       IPYMInstallFile.__init__(self, name, location)
       self.type = IPYMFileType.SHARE_FILE



##################################################
# Runtime Core Helper Functions 
##################################################

def _get_compiler(srcfile):
    """
    Determine compiler from source extension.
    """
    if IPYMSourceType.is_c_source(srcfile):
        return IPYM_C_COMPILER
    return IPYM_CXX_COMPILER

def _get_flags(srcfile):
    """
    Get the source dependent flags.
    """
    if IPYMSourceType.is_c_source(srcfile):
        return ' '+' '.join(IPYM_C_FLAGS)+' '
    return ' '+' '.join(IPYM_CXX_FLAGS)+' '

def _get_terminal_size():
    """
    Get the height and width of the terminal.
    """
    rows, columns = os.popen('stty size', 'r').read().split()
    return int(rows), int(columns)

def _get_terminal_width():
    """
    Get the width of the terminal.
    """
    rows, columns = _get_terminal_size()
    return columns

def _get_terminal_height():
    """
    Get the height of the terminal.
    """
    rows, columns = _get_terminal_size()
    return rows


def _push_current_environment(glbs):
    """
    For recursing.
    """
    pass

def _parse_compile_options(options):
    """
    Find the keyword arguments to options flags, include_dirs and libs
    and return them as a tuple.
    """
    FLAGS = 'flags'
    INCLUDE_DIRECTORIES = 'include_dirs'
    LINKING_LIBRARIES = 'libs'
    ALL_OPTIONS = [FLAGS, INCLUDE_DIRECTORIES, LINKING_LIBRARIES]
    
    # Find the options that are not parseable.
    unknown_options = filter(lambda item : not item[0] in ALL_OPTIONS, options.items())
    if len(unknown_options) > 0:
        unknown_keys = map(lambda pair: pair[0], unknown_options) 
        print style.intense_black_text('='*_get_terminal_width())
        print style.bold_intense_yellow_text('[ !!!BUILD WARNING!!! ]: '), \
                style.bold_text('Ignoring unrecognized options: ' +',  '.join(unknown_keys))
        if IPYM_VERBOSITY_LEVEL >= VerbosityLevel.VERBOSE:
            print
            pprint(unknown_options)
        print style.intense_black_text('='*_get_terminal_width())

    # Get the parsable options from options.
    flags = []
    include_dirs = []
    linking_libraries = []
    if options.has_key(FLAGS):
        flags = options[FLAGS]
    if options.has_key(INCLUDE_DIRECTORIES):
        include_dirs = options[INCLUDE_DIRECTORIES]
    if options.has_key(LINKING_LIBRARIES):
        linking_libraries = options[LINKING_LIBRARIES]

    return flags, include_dirs, linking_libraries

def _compile_object_file(source, flags=[], include_dirs=[]):
    """
    Compile component object file for a library.
    """
    name = os.path.basename(source)
    name = ' $IPYM_BINARY_DIR/'+name.rsplit('.')[0] + '.o'
    gcc_string = _get_compiler(source)+_get_flags(source)+source+" "+' '.join(flags)+' '+\
        ''.join([' -I'+id for id in  include_dirs])+" -o "+name
    #ip.runlines([gcc_string])
    if IPYM_VERBOSITY_LEVEL >= VerbosityLevel.VERBOSE:
        print '-->',  style.cyan_text('[ Compiling Object File ]: '), style.bold_text(os.path.basename(name))
    if IPYM_VERBOSITY_LEVEL >= VerbosityLevel.VERY_VERBOSE:
        print '    ',style.italic_text(gcc_string)
    execute_critical_command(gcc_string)
    if IPYM_VERBOSITY_LEVEL >= VerbosityLevel.VERY_VERBOSE:
        print '-->', style.green_text('[ Compiled %s ]'%os.path.basename(name)) 
    return name



##################################################
# Runtime Core Functions 
##################################################

def execute_critical_command(cmd_string, target="", indent=""):
    """
    Execute a system command and raise an error and exit on a bad
    return value from the command.
    """

    r_cmd_string = indent + "retval = !"+cmd_string+" ; echo $?"
    r_if_string = indent + "if retval[-1] != '0':"
    error_msg = "Bad exit value\nTARGET: "+target+\
        " \nCOMMAND: "+cmd_string + "\nRETURN VALUE: %s"
    r_then_string = indent + "    raise RuntimeError(\"\"\""+error_msg+"\"\"\"%retval[-1])"
    
    ip.runlines([r_cmd_string, r_if_string, r_then_string])
    retval =  ip.user_ns['retval']
    if retval[-1] != IPYM_EXPECTED_EXIT_VALUE:
        sys.stderr.write('\n'.join(retval[:-1]))
        my_pid = os.getpid()
        os.kill(my_pid, signal.SIGKILL)
    else:
        retlines = filter(lambda s: s.strip() >0, retval[:-1])
        if len(retlines):
            print '\n'.join(retlines[:-1])
    pass

    
def compile_shared_library(name, *sources, **options):
    """
    Compile a shared object library from sources.
    """
    flags, include_dirs, libs = _parse_compile_options(options)
    comp_lib_sources = []
    compiler = _get_compiler(sources[0])
    libname = 'lib'+name+'.so'
    print style.intense_blue_text('[ Building Shared Library ]:'),\
        style.bold_text(libname)
    ip.runlines("mkdir -p $IPYM_BINARY_DIR") 
    for src in sources:
        comp_lib_sources.append(_compile_object_file(src, flags, include_dirs))

    
    print style.red_text('[ Linking Shared Library  ]:'), \
        style.bold_text(libname)
   
    gcc_string = compiler+" -shared -Wl,-soname,"+libname+" -o $IPYM_BINARY_DIR/"+libname+" "+' '.join(comp_lib_sources)+" -lc"
    if IPYM_VERBOSITY_LEVEL >= VerbosityLevel.VERY_VERBOSE:
        print gcc_string
    
    execute_critical_command(gcc_string)
    print style.green_text('[ Built Shared Library    ]:'), style.bold_text(libname)
    IPYM_COMPILED_BINARIES.append(IPYMSharedLibrary(libname, sources, 
                                           options, os.path.realpath(libname)))
    pass


def compile_executable(name, *sources, **options):
    """
    Compile an executable from the sources.
    """
    print style.intense_blue_text('[ Building Executable ]:'),\
        style.bold_text(name)

    flags, include_dirs, libs = _parse_compile_options(options)
    
    libs = ''.join(map(lambda s: ' -l%s '%s, libs))

    comp_exec_sources = []
    IPYM_GCC_TPL = _get_compiler(sources[0])
    
    ip.runlines("mkdir -p $IPYM_BINARY_DIR") 
       
    for src in sources:
        comp_exec_sources.append(_compile_object_file(src, flags, include_dirs))
    
    gcc_string = IPYM_GCC_TPL + ' '.join(comp_exec_sources)  + ' -L./build  -o $IPYM_BINARY_DIR/'+ name+libs 
    print style.red_text('[ Linking Executable  ]:'), \
        style.bold_text(name)
    if IPYM_VERBOSITY_LEVEL >= VerbosityLevel.VERY_VERBOSE:
        print gcc_string
    execute_critical_command(gcc_string)

    print style.green_text('[ Built Executable    ]:'), style.bold_text(name)
    #ip.runlines([gcc_string])
    IPYM_COMPILED_BINARIES.append(IPYMExecutable(name, sources, 
                                           options, os.path.realpath(name)))
    pass

def compile_static_library(name, *sources, **options):
    """
    Compile static library from sources.
    """
    flags, include_dirs, libs = _parse_compile_options(options)
    comp_lib_sources = []
    libname = 'lib'+name+'.a'
    print style.intense_blue_text('[ Building Static Library ]:'),\
        style.bold_text(libname)

    ip.runlines("mkdir -p $IPYM_BINARY_DIR") 
    for src in sources:
        comp_lib_sources.append(_compile_object_file(src, flags, include_dirs))
    
    ar_string = "ar rcs $IPYM_BINARY_DIR/"+libname+" "+' '.join(comp_lib_sources)

    print style.red_text('[ Linking Static Library  ]:'), \
        style.bold_text(libname)

    if IPYM_VERBOSITY_LEVEL >= VerbosityLevel.VERY_VERBOSE:
        print ar_string

    execute_critical_command(ar_string)
    print style.green_text('[ Built Static Library    ]:'), style.bold_text(libname)
    #ip.runlines([ar_string])
    IPYM_COMPILED_BINARIES.append(IPYMStaticLibrary(libname, sources, 
                                           options, os.path.realpath(libname)))    
    pass


def add_include_file(filename):
    IPYM_INSTALL_FILES.append(
        IPYMIncludeFile(filename, os.path.realpath(filename)))    
    pass

def add_share_file(filename):
    IPYM_INSTALL_FILES.append(
        IPYMShareFile(filename, os.path.realpath(filename)))    
    pass


def build_subdir(subdir, ipym_file, target='all', cmd_args=""):
    RUN_SUBDIR_STRING_TPL = \
        """pushd %(IPYM_SUBDIR)s\nfrom %(IPM_MODULE)s import *\nipym_initialize(recompile=\"%(COMMAND_ARGS)s\")\n%(IPM_TARGET)s()\nipym_cleanup()\npopd\n"""

    
    os.system('ipymakec %s %s' %(cmd_args, ipym_file))
    
    
    subdir_dict = { 'IPM_MODULE' : 'ipym_'+ipym_file.split('.')[0],
                    'IPYM_SUBDIR' : subdir,
                    'IPM_TARGET' : target,
                    'COMMAND_ARGS' : cmd_args }

    
   
    ip.runlines(RUN_SUBDIR_STRING_TPL%subdir_dict)

    
