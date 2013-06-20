"""
:mod:`runtimecore` - Runtime facilities used by IPyMake Files
===============================================================

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>

"""
import sys
import os
import signal
from distutils.core import setup, Extension

from ipymake.environment import Environment, VerbosityLevels
from ipymake.sourcefiles import *
from ipymake.production  import *
import ipymake.textstyle as style

global env
env = Environment()

from IPython import ipapi
ip = ipapi.get()
    

EXPECTED_EXIT_VALUE = '0'
 
##################################################
# Helper Decorator Functions 
##################################################

def managed_target(function):
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
        push_dir = os.getcwd()
        retval = function(**args)
        if not env.built_targets.has_key(target_name):
            env.built_targets[target_name] = [str(function)]
        else:
            env.built_targets[target_name].append(str(function))
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
                if not target_name in env.built_targets.keys():
                    target(**args)
                else:
                    if target in env.built_targets[target_name]:
                        print 'Target:', target.__name__, 'already built!'
            return method(**args)
        resolve_dependencies.__name__ = method.__name__
        return resolve_dependencies;

        

##################################################
# Runtime Core Helper Functions 
##################################################

def _get_compiler(srcfile):
    """
    Determine compiler from source extension.
    """
    if is_c_source(srcfile):
        return C_COMPILER
    return CXX_COMPILER

def _get_global_flags(srcfile):
    """
    Get the source dependent flags.
    """
    if is_c_source(srcfile):
        return ' '+' '.join(C_FLAGS)+' '
    return ' '+' '.join(CXX_FLAGS)+' '

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


def _parse_compile_options(options):
    """
    Find the keyword arguments to options flags, include_dirs and libs
    and return them as a tuple.
    """
    # Define the constant strings that are used
    # for each of the KWARGS
    FLAGS = 'flags'
    INCLUDE_DIRECTORIES = 'include_dirs'
    LINKING_LIBRARIES = 'linking_libs'
    LIBRARY_DIRECTORIES = 'lib_dirs'
    ALL_OPTIONS = [FLAGS, INCLUDE_DIRECTORIES, LIBRARY_DIRECTORIES, LINKING_LIBRARIES]
    
    # Find the options that are not parsable.
    unknown_options = filter(lambda item : not item[0] in ALL_OPTIONS, options.items())
    
    # Don't completely error out on unrecognized options.  Tell the
    # user verbosely that they have entered unrecognized options.
    if len(unknown_options) > 0:
        unknown_keys = map(lambda pair: pair[0], unknown_options) 
        print style.intense_black_text('='*_get_terminal_width())
        print style.bold_intense_yellow_text('[ !!!BUILD WARNING!!! ]: '), \
                style.bold_text('Ignoring unrecognized options: ' +',  '.join(unknown_keys))
        if env.verbosity_level >= VerbosityLevels.VERBOSE:
            print
            pprint(unknown_options)
        print style.intense_black_text('='*_get_terminal_width())



    flags = []
    include_dirs = []
    lib_dirs = []
    linking_libs = []

    # Get the parsable options from options.
    if options.has_key(FLAGS):
        flags = options[FLAGS]
    if options.has_key(INCLUDE_DIRECTORIES):
        include_dirs = options[INCLUDE_DIRECTORIES]
    if options.has_key(LIBRARY_DIRECTORIES):
        lib_dirs = options[LIBRARY_DIRECTORIES]
    if options.has_key(LINKING_LIBRARIES):
        linking_libraries = options[LINKING_LIBRARIES]

    return flags, include_dirs, lib_dirs, linking_libs

def _format_compile_args(flags=[], include_dirs=[], lib_dirs=[], linking_libs=[] ):
    """
    :returns: tuple(flags, includes, library-dirs, linking-libs)
    """
    fmt_flags = ' '.join(flags) 
    fmt_include_dirs = ' '.join(map(lambda s: ' -I'+s, include_dirs))
    fmt_lib_dirs = ' '.join(map(lambda s: ' -L'+s, lib_dirs))
    fmt_linking_libs = ' '.join(map(lambda s: ' -l'+s, linking_libs))

    return ( fmt_flags, fmt_include_dirs, fmt_lib_dirs, fmt_linking_libs)

def _format_sources(*sources):
    return ' %s '%(' '.join(sources[0]))

def _compile_object_file(source, flags=[], include_dirs=[]):
    """
    Compile component object file for an exectuable or a library.
    """

    if env.verbosity_level >= VerbosityLevels.VERBOSE:
        print '-->',  style.cyan_text('[ Compiling Object File ]: '), \
            style.bold_text(os.path.basename(name))

    outfilename = os.path.basename(source)
    outfilename = ' $env.current_build_path/'+outfilename.rsplit('.')[0] + '.o'
    
    gxx_string = _get_compiler(source)+_get_global_flags(source)
    gxx_string += ' '.join(_format_compile_args(flags=flags, include_dirs=include_dirs))
    gxx_string += source+' -o '+outfilename

    if env.verbosity_level >= VerbosityLevels.VERY_VERBOSE:
        print '    ',style.italic_text(gxx_string)

    execute_critical_command(gxx_string)

    if env.verbosity_level >= VerbosityLevels.VERY_VERBOSE:
        print '-->', style.green_text('[ Compiled %s ]'%os.path.basename(name)) 

    return outfilename


##################################################
# Runtime Core Main User Functions 
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
    if retval[-1] != EXPECTED_EXIT_VALUE:
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
    assert len(sources)

    libname = 'lib'+name+'.so'
    binpath = env.current_build_path+'/'+libname
    gxx_template = "%(COMPILER)s %(FLAGS)s%(LIBNAME)s -o  %(BINPATH)s"\
        " %(SOURCES)s %(LINKING_LIBS)s" 

    # Get the options
    flags, include_dirs, lib_dirs, linking_libs = _parse_compile_options(options)
    

    comp_lib_sources = []
    compiler = _get_compiler(sources[0])
    
    
    print style.intense_blue_text('[ Building Shared Library ]:'),\
        style.bold_text(libname)
 
    ip.runlines("mkdir -p $env.current_build_path")
 
    # compile all of the sources for the library
    for src in sources:
        comp_lib_sources.append(_compile_object_file(src, flags, include_dirs))

    
    print style.red_text('[ Linking Shared Library  ]:'), \
        style.bold_text(libname)


    flags_str, include_dir_str, lib_dirs_str, linking_libs_str = \
        _format_compile_args(flags=['-shared',' -Wl,-soname,'], include_dirs=include_dirs,
                             lib_dirs=lib_dirs, linking_libs=linking_libs+['c'])

    sources_str = _format_sources(comp_lib_sources)

    gxx_string = gxx_template % {'COMPILER':compiler, 'FLAGS':flags_str, 
                                 'LIBNAME':libname, 'SOURCES':sources_str,
                                 'LINKING_LIBS':linking_libs_str,
                                 'BINPATH' : binpath}
    
    if env.verbosity_level >= VerbosityLevels.VERY_VERBOSE:
        print gxx_string
    
    execute_critical_command(gxx_string)
    
    print style.green_text('[ Built Shared Library    ]:'), style.bold_text(libname)

    env.compiled_binaries.append(SharedLibrary(libname, sources, options, binpath))

    pass


def compile_executable(name, *sources, **options):
    """
    Compile an executable from the sources.
    """

    binpath = env.current_build_path+'/'+name
    print style.intense_blue_text('[ Building Executable ]:'),\
        style.bold_text(name)


    gxx_template = "%(COMPILER)s %(FLAGS)s -o $env.current_build_path/%(BINNAME)s"\
        " %(SOURCES)s %(LINKING_LIBS)s" 

    # Get the options
    flags, include_dirs, lib_dirs, linking_libs = _parse_compile_options(options)
    

    comp_exec_sources = []
    compiler = _get_compiler(sources[0])
    
    
    ip.runlines("mkdir -p $env.current_build_path") 
       
    for src in sources:
        comp_exec_sources.append(_compile_object_file(src, flags, include_dirs))
    
    print style.red_text('[ Linking Executable  ]:'), \
        style.bold_text(name)

    flags_str, include_dir_str, lib_dirs_str, linking_libs_str = \
        _format_compile_args(flags=['-shared',' -Wl,-soname,'], include_dirs=include_dirs,
                             lib_dirs=lib_dirs, linking_libs=linking_libs+['c'])

    sources_str = _format_sources(comp_exec_sources)

    gxx_string = gxx_template % {'COMPILER':compiler, 'FLAGS':flags_str, 
                                 'BINNAME':name, 'SOURCES':sources_str,
                                 'LINKING_LIBS':linking_libs_str}
    
    if env.verbosity_level >= VerbosityLevels.VERY_VERBOSE:
        print gxx_string
    
    execute_critical_command(gxx_string)

    print style.green_text('[ Built Executable    ]:'), style.bold_text(name)

    env.compiled_binaries.append(Executable(name, sources, options, binpath))

    pass

def compile_static_library(name, *sources, **options):
    """
    Compile static library from sources.
    """
    flags, include_dirs, lib_dirs, libs = _parse_compile_options(options)
    comp_lib_sources = []
    libname = 'lib' + name + '.a'
    binpath = env.current_build_path+'/'+libname

    print style.intense_blue_text('[ Building Static Library ]:'),\
        style.bold_text(libname)

    ip.runlines("mkdir -p $env.current_build_path") 
    for src in sources:
        comp_lib_sources.append(_compile_object_file(src, flags, include_dirs))
    
    ar_string = "ar rcs $env.current_build_path/"+libname+" "+' '.join(comp_lib_sources)

    print style.red_text('[ Linking Static Library  ]:'), \
        style.bold_text(libname)

    if env.verbosity_level >= VerbosityLevels.VERY_VERBOSE:
        print ar_string

    execute_critical_command(ar_string)
    print style.green_text('[ Built Static Library    ]:'), style.bold_text(libname)

    env.compiled_binaries.append(StaticLibrary(libname, sources, options, binpath))
 
    pass

def add_include_file(filename):
    env.install_files.append(
        IncludeFile(filename, os.path.realpath(filename)))    
    pass

def add_share_file(filename):
    env.install_files.append(
        ShareFile(filename, os.path.realpath(filename)))    
    pass


###################################################################
# 
# Code from  http://wiki.python.org/moin/Distutils/Cookbook
#
###################################################################

def non_python_files(path):
    """
    Return all non-python-file filenames in path
    """
    result = []
    all_results = []
    module_suffixes = [info[0] for info in imp.get_suffixes()]
    ignore_dirs = ['cvs','.svn']
    for item in os.listdir(path):
        name = os.path.join(path, item)
        if (
            os.path.isfile(name) and
            os.path.splitext(item)[1] not in module_suffixes
            ):
            result.append(name)
        elif os.path.isdir(name) and item.lower() not in ignore_dirs:
            all_results.extend(non_python_files(name))
    if result:
        all_results.append((path, result))
    return all_results



def is_package(path):
    """
    Determine if the path is a python package.
    """
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
        )

def find_packages(path, base="" ):
    """
    Find all packages in path. 
    """
    packages = {}
    for item in os.listdir(path):
        dir = os.path.join(path, item)
        if is_package( dir ):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir
            packages.update(find_packages(dir, module_name))
    return packages

###### END Distutils Cookbook Code #######


def build_python_package(auto_pkg_dir=None,**kwargs):
    """
    
    """
    if not auto_pkg_dir is None:
        packages = find_packages(auto_pkg_dir)
        kwargs['package_dir'] = packages
        kwargs['packages'] = packages.keys()

    # You have to trick distutils by
    # resetting the command line arguments to what distutils
    # expects. (i.e. <script>.py build ), so store the arguments
    # temporarily, and then set them back later.
    temp_args = sys.argv
    # TODO: incorporate the env.verbosity_level here somehow to
    # specify a -v if verbosity is high enough.
    sys.argv = ['build_python_package', 'build', '-b', env.current_build_path]
    setm = setup(**kwargs)
    # reset the args back to the original values.
    sys.argv = temp_args 
    env.compiled_binaries.append(PythonPackage(**kwargs))
    pass



def build_python_extension(name, **kwargs):
    """
    Compile an extension that serves as the backend for some python
    module. This uses the :class:`Entension` class from 
    :mod:`distutils.core` module.  
    :returns: The Extension instance describing the
        compiled extension.
    """
    # You have to trick distutils by resetting the command line
    # arguments to what distutils expects. (i.e. <script>.py build ),
    # so store the arguments temporarily, and then set them back
    # later.
    temp_args = sys.argv
    sys.argv = ['build_python_package', 'build', '-b', env.current_build_path]
    ext = Extension(name, **kwargs)
    # reset the args back to the original values.
    sys.argv = temp_args 
    return ext
    



def build_subdir(subdir, ipym_file, target='all', cmd_args=""):
    """
    Continue running ipymake starting in the directory **subdir** with
    target **target**.
    """
    RUN_SUBDIR_STRING_TPL = \
        """pushd %(_SUBDIR)s\nfrom %(IPM_MODULE)s import *\ninit_hook()\n%(IPM_TARGET)s()\npopd\n"""

    
    os.system('cd %s\nipymakec %s %s' %(subdir,cmd_args, ipym_file))
    
    
    subdir_dict = { 'IPM_MODULE' : 'ipym_'+ipym_file.split('.')[0],
                    '_SUBDIR' : subdir,
                    'IPM_TARGET' : target,
                    'COMMAND_ARGS' : cmd_args }

    
   
    ip.runlines(RUN_SUBDIR_STRING_TPL%subdir_dict)

    
