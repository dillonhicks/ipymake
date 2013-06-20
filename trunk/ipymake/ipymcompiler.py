"""
:mod:`ipymcompiler` - The IPyMake Compiler
======================================================

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>


"""
import sys
import os
import ply.lex as lex
from exceptions import SyntaxError
import types
import time
from stat import *
import information as ipyminfo
import compiler


class BuildLanguageLexer:

    states = (
        ('INTARGET', 'exclusive'),
        )

    # Note: This list of tokens only needs to include those returned by
    # the tokenizer to the calling context. Other tokens may be defined by
    # routine that are thrown away as white space.
    #
    tokens = (
        'COLON',
        'NEWLINE',
        'NAME', 

        'NUMBER', 'COMMENT', 'INDENT',
   
        'TARGET_START',
        'TARGET_END',
      
        'CODE',
        'CRITICAL_CODE',
        'DEPENDENCY',
        
        'GLOBAL_VAR',
        'IMPORT'

    )

    

    def t_INDENT(self, t):
        r'[ ]{4}'
        #la_token = self.look_ahead()[0]
        #if la_token.type == 'NAME':
        #    print la_token.value
        #    if la_token.value == 'pass':
        #        t.value += la_token.value
        #        self.lexer.skip(1)
        #        t.type = 'TARGET_END'
        return t
    
    def t_INTARGET_CODE(self, t):
        r'[ ]{4}.+'

        if t.value.strip() == 'pass':
            self.lexer.pop_state()
            t.type = 'TARGET_END'
        elif t.value.strip().startswith('~'):
            t.type = 'CRITICAL_CODE'
            t.value = t.value.replace('~','',1)
        return t
 
    def t_INTARGET_DEPENDENCY(self, t):
        r'[ ]+[a-zA-Z0-9_]+'
        t.value = t.value.strip()
        return t
     
       
    def t_INTARGET_IGNORE(self, t):
        r'[ \t]'
        pass


    def t_INTARGET_NEWLINE(self, t):
        r'\n'
        self.lexer.lineno += 1
        pass


    def t_IMPORT(self, t):
        r'import .+' 
        return t
    
    def t_GLOBAL_VAR(self, t):
        '.+[=].+'
        return t


    def t_TARGET_START(self, t):
        r'[a-zA-Z][a-zA-Z0-9_]*:'
        self.lexer.push_state('INTARGET')
        self.lexer.lineno += 1
        return t



    # Names can begin with any letter, lower or upper case, and
    # include numbers and underscores as well, thereafter.
    #
    def t_NAME(self, t):
        r'[a-zA-Z][a-zA-Z0-9_]*'
        la_token = self.look_ahead()[0]
        if la_token.type == 'COLON':
            t.value += la_token.value
            self.lexer.skip(1)
            t.type = 'TARGET_START'
            self.lexer.push_state('INTARGET')
        return t

    
    
    def t_COLON(self, t):
        r':'
        return t

    def t_IGNORE(self, t):
        r'[ ]'

    def t_COMMENT(self, t):
        r'\#[^\n]*\n'
        t.lexer.lineno += t.value.count("\n")
        


    # We want to keep the lexer's accounting of the line numbers
    # accurate for parsing error reporting purposes
    #
    def t_NEWLINE(self, t):
        r'\n'
        t.lexer.lineno += t.value.count("\n")
        #return t
    
    # Complain about any characters not defined in the
    # tokenizing regular expressions
    #
    def t_error(self, t):
        raise SyntaxError("Syntax error on line %s. %s"%(t.lineno, t.value[0]))
        

    # Complain about any characters not defined in the
    # tokenizing regular expressions.
    #
    def t_INTARGET_error(self, t):
        print self.t_error(t)

        

    def look_ahead(self):
        num_tokens = 1
        seek_lexer = self.lexer.clone()
        seek_tokens = []
        for i in range(num_tokens):
            seek_tokens.append(seek_lexer.token())
        return seek_tokens

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
    
    # Some simple test code for the lexer, which prints out the token
    # stream for curiosity and some low-level learning and debugging
    def test(self, input_string, outfile=None):
        if outfile is None:
            outfile = sys.stdout
        self.lexer.input(input_string)
        while True:
             token = self.lexer.token()
             if not token: 
                 break

             print >>outfile, "T(%d): " % (self.lexer.lineno), token
             

class BuildLanguageParser:

    HEADER = \
"""#!/bin/env python
\"\"\"
################################################################################
#
# =====================================
# IPyMake Generated Python Script  
# =====================================
#
# Created IPyMake Version: %(VERSION)s
# Timestamp: %(TIMESTAMP)s
#
#  
# This Python script was created with IPyMake. To run this script you
# will need to have IPython installed. To install IPython you can use
# your distributions package manager, or the Python easy_install that
# is included in the Python SetupTools "easy_install ipython".
#
################################################################################


IPYMAKE_VERSION = \"%(VERSION)s\"
SRC_FILENAME = \"%(FILENAME)s"
SRC_MODIFICATION_TIME = %(TIMESTAMP)s

\"\"\"
# Import the modules with the heaviest use by default.
#
import sys
import os
# Used for caching the build environment
import cPickle

# Allows each ipym_*.py script to be executed on its own if the user
# so desires.
if __name__ == "__main__":
    # Gets the header information from the docstring and
    # loads it into the module namespace.
    # Gives access to IPYMAKE_VERSION, SRC_FILENAME nad 
    # SRC_MODIFICATION_TIME.
    eval(compile(__doc__, __file__, 'exec'))
    sys.exit(os.system(\"ipymake \"+SRC_FILENAME))
    pass


# Get the IPython API, we need their magic 
# to get everything to run.
import IPython.ipapi as ipapi
ip = ipapi.get()

# There isn't a ipython instance running,
# get a dummy api instance.
if ip is None:
    # The dummy instance allows for use to import the module 
    # as is for analysis and introspection.
    ip = ipapi.get(allow_dummy=True, dummy_warn=False)

from ipymake.runtimecore import *
"""

    FOOTER = \
"""

def init_hook(**kwargs):
    try:
        __init__(**kwargs)
    except(NameError):
        pass
    #print repr(env)
    pass


def install_hook(is_root=False, **kwargs):
    try:
        install()
    except(NameError):
        
        if is_root:
          ip.runlines(\"\"\"

for indir in env.install_dirs:
    mkdir -pv $indir
for cmpbin in env.compiled_binaries: 
    cmpbin.install()
\"\"\")
        #    ip.runlines(\"env = eval(cPickle.unpickle('./.ipym_cache.bin'))\")


def cleanup_hook(is_root=False, **kwargs):
    try:
        cleanup()
    except(NameError):
        env.close()
     
    pass



###############################################################################
#                  END AUTOMATICALLY GENERATED FILE                             
#
# Note: It is best not to edit this file, unless you know what you are 
# doing. Instead, change the input file and rerun ipymake or ipymakec.
#
###############################################################################
"""

    TARGET_TEMPLATE = \
"""


@managed_target
@depends_on(%(DEPENDENCIES)s)
def %(NAME)s(**kwargs):
%(CODE)s
    pass

"""
    

    def __init__(self, filename):
        self.filename = filename
        infile = open(filename, 'r')
        self.parse_str = infile.read()
        infile.close()
        self.lexer = BuildLanguageLexer()
        self.lexer.build()
        self.lexer = self.lexer.lexer
        self.lexer.input(self.parse_str)
        self.token_list = []
        token = self.lexer.token()
        while token:
            #print token
            self.token_list.append(token)
            token = self.lexer.token()

        self.imports = filter(lambda t: t.type == 'IMPORT', 
                              self.token_list)
        self.global_vars = filter(lambda t: t.type == 'GLOBAL_VAR', 
                                  self.token_list)
    
        def gen_targets(t_list):
            target_tokens = []
            while(t_list):
                token = t_list.pop(0)
                if token.type == 'TARGET_START':
                    target_tokens.append(token)
                    while t_list and not token.type == 'TARGET_END':
                        token = t_list.pop(0)
                        target_tokens.append(token)
                    
                    yield target_tokens
                    target_tokens = []
                
            
        
        self.targets = [t for t in gen_targets(self.token_list)]

        

    def get_header(self):
        """
        Just returns the HEADER string now,
        in the future may be used as a configurable HEADER.
        """
        return self.HEADER % dict(VERSION=ipyminfo.VERSION,
                                  TIMESTAMP=os.stat(self.filename)[ST_MTIME],
                                  FILENAME=self.filename)

    def get_footer(self):
        """
        Just returns the FOOTER string now,
        in the future may be used as a configurable footer.
        """
        return self.FOOTER 

    def p_imports(self):
        """
        Parses the **IMPORT** tokens and returns a string
        with all of the import statements separated by line.
        """
        import_strings = map(lambda t: t.value, self.imports)
        return '\n'.join(import_strings)+'\n'
        

    def p_globals(self):
        """
        Format all of the global variables (not declared within
        functions) in the format::
        
            global <var-name>
            <var-name> = <value>
            ...

        """
        global_var_assignments = map(lambda t: t.value, self.global_vars)
        global_var_names = map(lambda t: "global "+t[0:t.index('=')], 
                               global_var_assignments)
        global_vars = zip(global_var_names, global_var_assignments)
        return '\n'.join(['\n'.join(g) for g in global_vars])
        

    def p_target(self, tokens):
        """
        Process the tokens for a specific target and return a string
        where each line of the function is now executed with
        ip.runlines(), where *ip* is an instance of the IPython API.
        The format given to targets is::

            @depends_on(<dep-0,...,dep-n>)
            @managed_target
            def <target-name>(**kwargs):
                ip.runlines(\"\"\"<code>\"\"\"
                ...
                pass

        .. seealso::
        
            :class:`runtimecore.depends_on`
            :func:`runtimecore.managed_target`

        """
        assert tokens[0].type == 'TARGET_START'
        assert tokens[-1].type == 'TARGET_END'
        # first token should always be the TARGET_START token
        name = tokens.pop(0).value[:-1] # gets rid of the ':'
        # format dependencies into a comma seperated list
        dependencies = filter(lambda t: t.type == 'DEPENDENCY', tokens)
        dependencies = map(lambda t: t.value, dependencies)
        dependencies = ",".join(dependencies)        
        

        code_lines = filter(lambda t: t.type.endswith('CODE'), tokens)
        code_lines = map(lambda t: t.value[4:], code_lines)        
        code_lines = '\n'.join(code_lines)
        code_lines = """
    ip.runlines(
\"\"\"
%s
\"\"\")
""" % code_lines

        target_dict = { 'NAME' : name, 
                        'DEPENDENCIES': dependencies,
                        'CODE' : code_lines}
        return self.TARGET_TEMPLATE % target_dict

    def p_targets(self):
        """
        :returns: The string of all of the formatted targets.
        
        .. seealso:: :mod:`BuildLanguageParser.p_target`
        """
        t_strings = []
        for t in self.targets:
            t_strings.append(self.p_target(t))
        return '\n'.join(t_strings)
            



    def parse(self):
        """
        Creates the string that is the resultant Python
        code.
        """
        parsed_string = self.get_header()
        parsed_string += self.p_imports()
        parsed_string += self.p_globals()
        parsed_string += self.p_targets()
        parsed_string += self.get_footer() 
        return parsed_string 




def format_outpath(filename):
    """
    Format the outfile path for ipymake compiled file.
    """
    # Generate the correct output path. 
    odir = os.path.dirname(os.path.abspath(filename))
    ofname = os.path.basename(filename)
    ofname = ofname.split('.')[0]
    ofpath = "%s/ipym_%s.py" %(odir, ofname)
    return ofpath

def needs_recompile(filename):
    """
    Determine if the source filename needs to be recompiled.
    Doesn't save t
    """
    file_mod_time = os.stat(filename)[ST_MTIME]
    filename = os.path.basename(filename)
    module_name = 'ipym_'+os.path.splitext(filename)[0]

    try:
        comp_mod = __import__(module_name)     
        # Gets SRC_MODIFICATION_TIME from the docstring header
        eval(compile(comp_mod.__doc__, filename, 'exec'))
        #print dir()
        recompile = bool(locals()['SRC_MODIFICATION_TIME'] != file_mod_time)
    except(ImportError):
        return True
    
    sys.path.pop()
    return recompile
    

def ipym_compile(filename, force_recompile=False):
    """
    Compile the ipymake-syntaxed filename into a new file python
    source file ipym_<filename>.py and its bytecode compiled
    counterpart ipym_<filename>.pyc
    """
    if not needs_recompile(filename) and not force_recompile:
        return
    
    p = BuildLanguageParser(filename)
    code_string = p.parse()

    ofpath = format_outpath(filename)
    
    outfile = open(ofpath, 'w')
    outfile.write(code_string)
    outfile.close()
    
    # Go ahead and generate the bytecode now, this may speed thigns
    # up in the future.
    compiler.compileFile(ofpath)
    pass





if __name__ == "__main__":
    parser = BuildLanguageParser(sys.argv[1])
    #print parser.parse()
    ipym_compile(sys.argv[1])

