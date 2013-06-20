"""
:mod:`ipymake.ipymcompiler`
================================

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>

"""
import sys, os, warnings, re
#import networkx as nx
#import matplotlib.pyplot as plt
import hashlib


####################
# Error Numbers
####################
PREPROCESSING_ERRNO = 1
WRITE_FILE_ERRNO = 2

######################
# PARSING REGEXS
######################

# (1): Line starting with 'import' then pretty much 
#    anything but a newline, OR
# (2): from _____ import _______
#                       (1)          (2)
IMPORT_REGEX  = r'^((import \w+)|(from \w+ import \w+))'

# Matches (at the begining of the line)
# xxxxxx = xxxxxx
GLOBAL_DEF_REGEX = r'^.+[=].+'


# Matches the format.
# xxxxxxx: 
TARGET_START_REGEX = r'^\w+[:]'

# Matches end of function pass, or the
# next unindented line.
TARGET_END_REGEX = r'(^    pass)|(^\w+)'

# Ignore Tabs newlines and lines that have
# text beginning with '#'
IGNORE_REGEX = r'^(([ \t\n])|([ \t]*#.*))'

INITIALIZE_HOOK_NAME = 'initialize'
CLEANUP_HOOK_NAME = 'cleanup'

#########################

# Header template string.
#
IPYMAKE_HEADER_TEMPLATE = """
import sys
import os

import IPython.ipapi as ipapi
ip = ipapi.get()

if ip is None:
    ip = ipapi.get(allow_dummy=True, dummy_warn=False)

from ipymake.ipymruntimecore import *

IPYM_ORIGINAL_FILE_HASH = "%(IPYM_FILE_HASH)s" 

IPYM_ORIGINAL_FILE_NAME = \"\"\"%(IPYM_FILE_NAME)s\"\"\"

IPYM_COMMAND_ARGS = \"%(IPYM_COMMAND_ARGS)s\"

%(IPMAKE_IMPORTS)s

%(IPMAKE_GLOBALS)s



ip.runlines(\"\"\"
IPYM_INSTALL_PREFIX = '~/tmp'
IPYM_BINARY_PREFIX = '/bin'
IPYM_LIBRARY_PREFIX = '/lib'
IPYM_INCLUDE_PREFIX = '/include'
IPYM_SHARE_PREFIX = '/share'
IPYM_BINARY_DIR = './build'


class DynamicPrefixString:
    def __init__(self, static_suffix):
        self._static_suffix = static_suffix

    def __str__(self):
        return IPYM_INSTALL_PREFIX + self._static_suffix


IPYM_BINARY_INSTALL_PREFIX = DynamicPrefixString(IPYM_BINARY_PREFIX)
IPYM_LIBRARY_INSTALL_PREFIX = DynamicPrefixString(IPYM_LIBRARY_PREFIX)
IPYM_INCLUDE_INSTALL_PREFIX = DynamicPrefixString(IPYM_INCLUDE_PREFIX)
IPYM_SHARE_INSTALL_PREFIX = DynamicPrefixString(IPYM_SHARE_PREFIX)
\"\"\")



"""

# The character that denotes that a command is a command that should
# make ipymake exit if the command fails.  Perhaps this should be a
# default for all bash commands.
CRITICAL_ESCAPE_CHARACTER = '~'


def print_dbg(msg):
    """To be replaced with python logging soon"""
#    print 'DEBUG:', msg
    pass

class IPYTarget:
    TEMPLATE = \
"""

@depends_on(%(TARGET_DEPENDENCIES)s)
@ipym_managed_target
def %(TARGET_NAME)s(**kwargs):
%(TARGET_CODE)s
    pass

"""

    def __init__(self, name, dependencies=[], code_lines=[]):
        """
        Class to ecapsulate target data, namely a target-name,
        depdendencies, and the code.
        """
        self.name = name
        self.dependencies = filter(lambda d: not d == '',dependencies)
        self.code_lines = code_lines

    def __str__(self):
        ustring = 'IPY TARGET:\n'
        ustring += '  Name: %s\n'% self.name
        ustring += '  Dependencies:  %s\n' %self.dependencies
        ustring += '--------------------------------------\n'
        for line in self.code_lines: ustring += '    %s'%line
        return ustring

    def format(self):
        """
        Formats the target into a dictionary keyed by each section.
        """
        target_dict = { 'TARGET_NAME' : self.name,
                        'TARGET_DEPENDENCIES' : ','.join(self.dependencies),
                       
                        }
        
        target_code = '    ip.runlines([\n'
        
        for line in self.code_lines:
            # Transform each of the lines into a IPython command.
            #
            # Remove the trailing whitespace character.
            line = line[:-1]
            if not line == 'pass' and not line.strip() == '':
                # The line is not the end of the target, and is not a
                # blank line.
                if line.strip().startswith(CRITICAL_ESCAPE_CHARACTER):
                    # Line starts with the critical-escape character
                    # so split the line and get the command as necessarily
                    # formatted to exit on bad exit from the command.
                    line_sects = line.split(CRITICAL_ESCAPE_CHARACTER)
                    indent = line_sects[0]
                    command  = line_sects[1]
                    line = indent + "\"\"execute_critical_command(\"%s\", \"%s\", \"%s\")\"\""%(command, self.name, indent)
                    target_code += "                 \"%s\",\n"%line                    
                else:
                    target_code += "                 \"\"\"%s\"\"\",\n"%line
        
        target_code += '               ])'
        # Target code has been formatted correctly, so set the dictionary's target code 
        # to the target_code.
        target_dict['TARGET_CODE'] = target_code
        
        # Return the template filled in with the data from the
        # target_dict, i.e. the TARGET_NAME, TARGET_DEPENDENCIES, and
        # TARGET_CODE.
        return self.TEMPLATE % target_dict

IPYM_INITIALIZE_TARGET = \
"""

def ipym_initialize(**kwargs):
    #print 'Initializing build environment.'
    if kwargs['recompile']:
        ip.runlines("IPYM_COMMAND_ARGS = ' --force-recompile '")
    else:
        ip.runlines("IPYM_COMMAND_ARGS = '' ")

    try:
        initialize(**kwargs)
    except(NameError):
        pass
    pass

"""

IPYM_CLEAN_TARGET = \
"""

#def ipym_clean_build():
#    try:
#        clean()
#    except(NameError):
#        ip.runlines(["rm -rfv $IPYM_BINARY_DIR/* "])
#    pass


"""

IPYM_CLEANUP_TARGET = \
"""

def ipym_cleanup():
    try:
        cleanup()
    except(NameError):
        pass
    #print 'Done!'
    pass

"""        

def parse(filename, force_recompile=False, **kwargs):
    """
    Parse the file into global variables, imports, and targets.
    """
        
    try:
        # Attempt to read in the infile as a list of lines.
        infile = open(filename, 'r')
        file_lines = infile.readlines()
        infile.seek(0)
        file_hash = hashlib.sha1(infile.read()).hexdigest()
        infile.close()
    except(IOError):
        # Unable to read the infile, print error and exit.
        print 'ipmake error: Unable to open file <%s>. ' \
               'Preprocessing failed, exiting...'%filename
        sys.exit(PREPROCESSING_ERRNO)

    if not force_recompile:
        existing_module_path = 'ipym_'+filename
        if os.path.exists(existing_module_path):
            existing_module_name = 'ipym_'+filename.rsplit('.')[-2]
            compiled_module = __import__(existing_module_name)
            if hasattr(compiled_module, 'IPYM_ORIGINAL_FILE_HASH') and \
                    hasattr(compiled_module, 'IPYM_ORIGINAL_FILE_NAME'):
                if compiled_module.IPYM_ORIGINAL_FILE_HASH == file_hash and \
                        compiled_module.IPYM_ORIGINAL_FILE_NAME == filename:
                    # No Change, skip compiling
                    # print 'SKIPPING COMPILING'
                    return
        
    
    
    # Put the variables in the global namespace
    global current_line
    global file_imports
    global file_globals
    global file_targets

    # Set the variables to empty/default values.
    file_imports = []
    file_globals = []
    file_targets = []
    current_line = 0
    
    def process_non_target():
        # Process the non targets, ie the global variables and the
        # module imports.
 
        # Get the variables from the global namespace.
        global current_line
        global file_imports
        global file_globals
        global file_targets
        
        # See if the current line matches the definition of a target.
        target_match = re.match(TARGET_START_REGEX, file_lines[current_line])

    
        while( not target_match ):
            print_dbg('CURRENT_LINE: %s'%file_lines[current_line])
            ignore_match = re.match(IGNORE_REGEX, 
                                file_lines[current_line])
            if ignore_match is None:
                import_match = re.match(IMPORT_REGEX, 
                                    file_lines[current_line])
                if import_match is None:
                    global_def_match = re.match(GLOBAL_DEF_REGEX, 
                                            file_lines[current_line])
                    if global_def_match is None:
                        print_dbg('I Dont know what this is %s' % 
                                  file_lines[current_line])
                    else:
                        # global variable definition
                        file_globals.append(file_lines[current_line])
                else:
                    # is an import statement, add it to the imports list
                    file_imports.append(file_lines[current_line])
                
            current_line += 1

            if not current_line >= len(file_lines) - 1:
                # The next index isn't over the bounds of the list
                # keep attempting to match.
                target_match = re.match(TARGET_START_REGEX, file_lines[current_line])
            else:
                break

    def process_target():
        #  
        global current_line
        global file_imports
        global file_globals
        global file_targets
        
        if current_line < len(file_lines):
            target_match = re.match(TARGET_START_REGEX, file_lines[current_line])
        else:
            return

        print_dbg('CURRENT_LINE: %s'%file_lines[current_line])
        if target_match is None:
            return 
        target_definition = file_lines[current_line].strip()
        target_definition = target_definition.split(':')
        target_name = target_definition[0]
        if len(target_definition) > 1:
            target_dependencies = target_definition[1].strip().split(' ')
        else:
            target_dependencies = []
    
        current_line += 1
        target_code_lines = []
        end_target_match = re.match(TARGET_END_REGEX, file_lines[current_line])

        while(current_line < len(file_lines) and not end_target_match):
            print_dbg('CURRENT_LINE: %s'%file_lines[current_line])
            target_code_lines.append(file_lines[current_line][4:])
            current_line += 1

            if not current_line >= len(file_lines) - 1:
                # The next index isn't over the bounds of the list
                # keep attempting to match.
                end_target_match = \
                    re.match(TARGET_END_REGEX, file_lines[current_line])
            else:
                break
        file_targets.append( IPYTarget(target_name, 
                                       target_dependencies, target_code_lines))

        

    while current_line < len(file_lines):
        process_non_target()
        process_target()


    print_dbg(file_imports)
    print_dbg(file_globals)
    for tg in file_targets:
        print_dbg(tg)

    cmd_args = ""
    if force_recompile:
        cmd_args =  " --force-recompile "

    return {
        'IPMAKE_IMPORTS' : file_imports, 
        'IPMAKE_GLOBALS' : file_globals,
        'IPMAKE_TARGETS' : file_targets,
        'IPYM_FILE_HASH' : file_hash,
        'IPYM_FILE_NAME' : filename,
        'IPYM_COMMAND_ARGS' : cmd_args
        }


def write_file(ipmake_data, filename):
    # Write out the compiled file with using the ipmake_data to fill
    # in the template.
    try:
        # Try to open the file to write.
        outfile = open(filename, 'w')
    except(IOError):
        # IOError of some kind, tell the user and exit.
        print 'ipmake error: Unable to open file <%s>. ' \
               'Writing failed, exiting... ' % filename
        sys.exit(WRITE_FILE_ERRNO)

    
    header_dict = { 'IPMAKE_IMPORTS' : '',
                    'IPMAKE_GLOBALS' : '',
                    'IPYM_FILE_HASH' : '',
                    'IPYM_FILE_NAME' : ''}

    header_dict['IPMAKE_IMPORTS'] = '\n'.join(ipmake_data['IPMAKE_IMPORTS'])
    header_dict['IPYM_FILE_HASH'] = ipmake_data['IPYM_FILE_HASH']
    header_dict['IPYM_FILE_NAME'] = ipmake_data['IPYM_FILE_NAME']
    header_dict['IPYM_COMMAND_ARGS'] = ipmake_data['IPYM_COMMAND_ARGS']


    # Create the defined globals variables for the header.
    # requires the extra 
    defined_globals = []
    for glb in ipmake_data['IPMAKE_GLOBALS']:
        name = glb.split('=')[0]
        defined_globals.append("ip.runlines([\"global %s\"])" % name )
        defined_globals.append("ip.runlines([\"%s\"])"%glb.strip())
        
    
    header_dict['IPMAKE_GLOBALS'] = '\n'.join(defined_globals)
    header = IPYMAKE_HEADER_TEMPLATE % header_dict
                             
    outfile.write(header)
    
    footer_targets = [IPYM_INITIALIZE_TARGET, IPYM_CLEAN_TARGET, IPYM_CLEANUP_TARGET]
    filtered_initialize_target = filter(lambda tg: tg.name == INITIALIZE_HOOK_NAME, ipmake_data['IPMAKE_TARGETS'])
    if filtered_initialize_target:
        initialize_hook = filtered_initialize_target[0]
        ipmake_data['IPMAKE_TARGETS'].remove(initialize_hook)
        footer_targets.append(initialize_hook.format())
    
    filtered_cleanup_target = filter(lambda tg: tg.name == CLEANUP_HOOK_NAME, ipmake_data['IPMAKE_TARGETS'])
    if filtered_cleanup_target:
        cleanup_hook = filtered_cleanup_target[0]
        ipmake_data['IPMAKE_TARGETS'].remove(cleanup_hook)
        footer_targets.append(cleanup_hook.format())

    for tg in ipmake_data['IPMAKE_TARGETS']:
        outfile.write(tg.format())
        
    while footer_targets:
        tg = footer_targets.pop()
        outfile.write(tg)
    

    outfile.flush()
    outfile.close()
#   os.system("chmod 775 %s"%filename)
    

def compile_file(filename, **kwargs):
    """
    Compile the filename
    """
    ipmake_data = parse(filename, **kwargs)
    if ipmake_data is None:
       return
    ipm_module = 'ipym_%s'%filename.split('.')[0]
    ipm_filename = ipm_module + '.py'
    write_file(ipmake_data, ipm_filename)
    
#    # Generate Dependency Graph    
#    graph_file = "%s_%s.svg" % ('%s',ipm_module)
#    dot_file = "%s_%s.dot" % ('%s',ipm_module)
#    graph = nx.MultiDiGraph()
# 
#    for ipt in ipmake_data['IPMAKE_TARGETS']:
#        g_filename = graph_file % ipt.name
#        g_dotfile = dot_file % ipt.name
#        G = nx.DiGraph()
#        nm = ipt.name
#        G.add_node
#        for td in ipt.dependencies:
#            G.add_edge(nm, td)
#            nm = td
#        nx.write_dot(G, g_dotfile)
    


    
