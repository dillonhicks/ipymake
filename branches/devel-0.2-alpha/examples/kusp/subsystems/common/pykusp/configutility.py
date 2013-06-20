"""--------------------------------------------
 configutility.py

 A new module to replace the previous KUSP configuration
 language parsing. This step is a simplification to
 implement the language as a straight PLY based module
 without the specification file that describes semantic
 constraints on the data specified which should properly be
 in a separate application-specific routine checking the
 consistency of the data structure contents provided by the
 parsing.

 Ideally, this will permit near-transparent replacement for
 all existing uses. Near-transparent as the calls using the
 parser are now different since we no longer need the
 specification file.


--------------------------------------------
"""

import ply.lex as lex
import types

class KUSP_Config_Lexer:
    # Note: This list of tokens only needs to include those returned by
    # the tokenizer to the calling context. Other tokens may be defined by
    # routine that are thrown away as white space.
    #
    tokens = (
        'COMMA', 'EQUAL',
        'LEFT_ANGLE', 'RIGHT_ANGLE', 
        'LEFT_BRACE', 'RIGHT_BRACE',
        'LEFT_SQUARE', 'RIGHT_SQUARE', 
        'LEFT_PAREN', 'RIGHT_PAREN', 
        'NAME', 'STRING_LITERAL', 
        'NUMBER'
    )

    # Obvious one-character tokens. Those with a backslash in
    # the pattern are characters used in the specification of
    # regular expressions and which must, thus, be escaped as
    # "literal".
    #
    t_COMMA        = r','
    t_EQUAL        = r'='
    t_LEFT_ANGLE   = r'<'
    t_RIGHT_ANGLE  = r'\>'
    t_LEFT_BRACE   = r'\{'
    t_RIGHT_BRACE  = r'\}'
    t_LEFT_SQUARE  = r'\['
    t_RIGHT_SQUARE = r'\]'
    t_LEFT_PAREN   = r'\('
    t_RIGHT_PAREN  = r'\)'
    
    # Names can begin with any letter, lower or upper case, and
    # include numbers and underscores as well, thereafter.
    #
    t_NAME           = r'[a-zA-Z][a-zA-Z0-9_\-\.]*'

    # This regex was copied from a CPP Preprocessing in PLY
    # example, which copied it from somewhere else. It was cited
    # as not working for string literals with an embedded '"'
    # character escaped with a backslash. Good to fix
    # eventually, but I doubt the issue will arise with KUSP
    # configuration languages.
    #
    t_STRING_LITERAL = r'"([^"\\]|\\.)*"'

    # Ignored these characters
    #
    t_ignore = " \t"

    #
    # Comments start at a '#' and end with a newline
    #
    def t_comment(self, t):
        r'\#[^\n]*\n'
        t.lexer.lineno += t.value.count("\n")
        
    # Integer numbers. Not sure how to do floating point yet
    # 
    def t_NUMBER(self, t):
        r'\d+'
        try:
            t.value = int(t.value)
        except ValueError:
            print "Integer value too large", t.value
            t.value = 0

        return t

    # We want to keep the lexer's accounting of the line numbers
    # accurate for parsing error reporting purposes
    #
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    # Complain about any characters not defined in the
    # tokenizing regular expressions
    #
    def t_error(self, t):
        print "Illegal character '%s'" % t.value[0]
        t.lexer.skip(1)

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
    
    # Some simple test code for the lexer, which prints out the token
    # stream for curiosity and some low-level learning and debugging
    def test(self, input_string, outfile):
        self.lexer.input(input_string)
        while True:
             token = self.lexer.token()
             if not token: 
                 break

             print >>outfile, "T(%d): " % (self.lexer.lineno), token

##########################################################
#
# This section defines the parser, which will user the lexer
# created by the code above.
# 
# config_defn      : dict_list
#
# topdict_list     : topdict_list topdict_defn
#                  | topdict_defn
#  
# topdict_defn     : LEFT_ANGLE NAME RIGHT_ANGLE dict_element_list
# 
# list_defn        : LEFT_SQUARE list_elem_list RIGHT_SQUARE
# 
# list_elem_list   : list_elem_list data_defn
#                  | data_defn
#                  | empty 
# 
# dict_defn        : LEFT_BRACE dict_elem_list RIGHT_BRACE
# 
# dict_elem_list   : dict_elem_list dict_member_defn
#                  | dict_member_defn
#                  | empty 
# 
# dict_member_defn : NAME EQUAL data_defn
# 
# data_defn        : NAME
#                  | NUMBER
#                  | STRING_LITERAL
#                  | list_defn 
#                  | dict_defn
# 
import ply.yacc as yacc

# Note: This list of tokens only needs to include those returned by
# the tokenizer to the calling context. Other tokens may be defined by
# routine that are thrown away as white space.
#
tokens = (
    'NAME', 'STRING_LITERAL', 
    'COMMA', 'EQUAL', 'NUMBER',
    'LEFT_SQUARE', 'RIGHT_SQUARE', 
    'LEFT_BRACE', 'RIGHT_BRACE',
    'LEFT_ANGLE', 'RIGHT_ANGLE', 
    'LEFT_PAREN', 'RIGHT_PAREN', 
)

start = 'config_defn'

###############
# Start Symbol
###############
def p_config_defn(p):
    'config_defn : topdict_list'
    p[0] = p[1]

########################################
# List of Top Level Dictionary Elements
########################################
def p_topdict_list1(p):
    'topdict_list : topdict_list topdict_defn'
    p[1].update(p[2])
    p[0] = p[1]
 
def p_topdict_list2(p):
    'topdict_list : topdict_defn'
    p[0] = p[1]
 
def p_topdict_list3(p):
    'topdict_list : empty'
    p[0] = {}
 
#########################################
# Top-Level Way of Defining a Dictionary
#########################################
def p_topdict_defn(p):
    'topdict_defn : LEFT_ANGLE NAME RIGHT_ANGLE dict_elem_list'
    p[0] = { p[2] : p[4] }

########################################
# Pythonic Way of Defining a Dictionary
########################################
def p_dict_defn(p):
    'dict_defn : LEFT_BRACE dict_elem_list RIGHT_BRACE'
    p[0] = p[2]

##########################
# Dictionary Element List
##########################
def p_dict_elem_list1(p):
    'dict_elem_list : dict_elem_list dict_member_defn'
    p[1].update(p[2])
    p[0] = p[1]

def p_dict_elem_list2(p):
    'dict_elem_list : dict_member_defn '
    p[0] = p[1]

def p_dict_elem_list3(p):
    'dict_elem_list : empty' 
    p[0] = {}

def p_dict_member_defn(p):
    'dict_member_defn : NAME EQUAL data_defn'
    p[0] = { p[1] : p[3] }

##################
# List definition
##################

def p_list_defn(p):
    'list_defn : LEFT_SQUARE list_elem_list RIGHT_SQUARE'
    p[0] = p[2]
    
def p_list_elem_list_1(p):
    'list_elem_list : list_elem_list COMMA data_defn'
    if type(p[3]) == type([]):
        p[0] = p[1] + p[3]
    else:
        p[0] = p[1] + [ p[3] ]

def p_list_elem_list_4(p):
    'list_elem_list : list_elem_list data_defn'
    if type(p[2]) == type([]):
        p[0] = p[1] + p[2]
    else:
        p[0] = p[1] + [ p[2] ]

def p_list_elem_list_2(p):
    'list_elem_list : data_defn'
    if type(p[1]) == type([]):
        p[0] = p[1]
    else:
        p[0] = [ p[1] ]

def p_list_elem_list_3(p):
    'list_elem_list : empty '
    p[0] = []

##################
# Tuple definition
##################

def p_tuple_defn(p):
    'tuple_defn : NAME LEFT_PAREN dict_elem_list RIGHT_PAREN'
    p[0] = ( p[1], p[3] )

##########################
# Data Element Definition
##########################
def p_data_defn(p):
    '''data_defn : NAME
                 | NUMBER
                 | string
                 | tuple_defn
                 | list_defn
                 | dict_defn'''
    p[0] = p[1]

def p_string(p):
    'string : STRING_LITERAL'
    p[0] = p[1][1:-1]

def p_empty(p):
   'empty :'
   pass



def parse_configfile(configfile):
    """ Parses a configuration file to a Python dictionary.
    
    @param configfile: The configuration file to parse 
        to obtain the dictionary defined by the configuration 
        file's contents.
        
    @type configfile: Either a string file path of the configfile,
        or a readable file object.
    
    @raise TypeError: If configfile is not a string or a file object.
    
    @rtype: dict
    """
    
    # Determines whether configfile is a file or
    # a string (filepath). If configfile is a string it opens the 
    # file using the configfile string as a filepath. 
    # If neither a stirng or a fileobject, it raises a
    # TypeError. 
    if not type(configfile) is types.FileType:
        if type(configfile) is types.StringType:
            try:
                configfile = open(configfile)
            except IOERROR:
                print "Error: cannot open ", configfile
        else:
            raise TypeError('Argument: %s not a string filepath'
                                ' or a file object.' % configfile) 
                            
    config_lexer = KUSP_Config_Lexer()
    config_lexer.build()
    config_parser = yacc.yacc()
    parse_str = configfile.read()
    retval = config_parser.parse(parse_str, lexer=config_lexer.lexer)
    return retval
    
#####################################################################
#
#          OLD CONFIGFILE.PY COMPATIBILITY FUNCTIONS
#
# NOTE: DO NOT USE THESE IN NEW CODE!
#####################################################################
def parse_config(configfile):
    """This is a name wrapper for parseConfigFile to provide a functional
    equivalent to the old 'configfile.py' module. This will allow there to
    be a simple name change of:
        from pykusp import configfile 
    TO:
        import pykusp.configutility as configfile
    when using configfile.parse_config()
    """
    return parse_configfile(configfile)

def get_spec(filename):
    """This is a compatibility function to provide a near functional
    equivalent to the old 'configfile.py' module. This will allow there to
    be a simple name change of:
        from pykusp import configfile 
    TO:
        import pykusp.configutility as configfile
    when using configfile.get_spec()
    
    @note: This version does not actually check against
        a specfile since we are transitioning away from
        using the old cspec/configfile_mod method of parsing.
    """
    return parse_configfile(filename)            

def check_config(config_dict, spec):
    """Replaces configfile.check_config to provide a functional
    smoke and mirrors equivalent to the old 'configfile.py' module. 
    This will allow there to be a simple name change of:
        from pykusp import configfile 
    TO:
        import pykusp.configutility as configfile
    when using configfile.check_config()
    
    @note: This will always return true, it is here to provide
        partial backwards compatibility as we transition away from the 
        old configfile_mod parser.
    """
    if Params.debug_level >= 2:
        print 'DEBUG_2: Using depriciated function configutility.check_config.'
        print 'DEBUG_2: Called with config_dict=%s  , spec=%s ' % (config_dict, spec)
        print 'DEBUG_2: ALWAYS RETURNS TRUE!'
    return True

def check_spec(spec_dict):
    """Replaces configfile.check_spec to provide a functional
    smoke and mirrors equivalent to the old 'configfile.py' module. 
    This will allow there to be a simple name change of:
        from pykusp import configfile 
    TO:
        import pykusp.configutility as configfile
    when using configfile.check_spec()
    
    @note: This will always return true, it is here to provide
        partial backwards compatibility as we transition away from the 
        old configfile_mod parser.
    """
    if Params.debug_level >= 2:
        print 'DEBUG_2: Using depriciated function configutility.check_spec.'
        print 'DEBUG_2: Called with spec_dict=%s ' % (spec_dict)
        print 'DEBUG_2: ALWAYS RETURNS TRUE!'
    return True



##################################################################

########################################################
#
# If this module is called as a command, then open the
# file, parse it, and 

if __name__ == "__main__":
    # imports required if this module is called as a
    # command
    import optparse, sys
    from pprint import *

    # define the set of permitted parameters, including the
    # command arguments.  The initialization method creates
    # the parser and defines the defaults. The parse()
    # method actually parses the arguments one the command
    # line. This was done so that the instance of the class
    # could be global and thus available to all
    # routines. and then parse the arguments to this call
    # according to the specification
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

            # Command specific options. We can specify a
            # configuration file to parse, which defaults to
            # stdin, and an output file name, which defaults
            # to stdout.
            self.p.add_option("-c", action="store", type ="string", 
                              dest="configfile_name", 
                              help="Parse the file CONFIGFILE_NAME, over-riding stdin default")
            self.p.add_option("-o", action="store", type ="string", 
                              dest="outfile_name", 
                              help="Output to the file OUTFILE_NAME, over-riding stdout default")

            # Four levels of diagnostic output. First, print
            # the input file with line numbers as a sanity
            # check and to assist with parsing errors.
            # Second, print the set of tokens. More for
            # interest and education, but may be useful for
            # debugging. Third, structural printing, which
            # prints the data structures extracted by
            # parsing the configuration file. Fourth, the
            # "pretty printing" of the data structures in
            # standard output format.
            self.p.add_option("-n", action="store_const", const=True,     
                              dest="lineno_print", help="Print input-file with line numbers")
            self.p.add_option("-t", action="store_const", const=True,     
                              dest="token_print", help="Print the stream of tokens extracted fromt he input-file")
            self.p.add_option("-s", action="store_const", const=True,     
                              dest="struct_print", help="Print the dta structures derived by parsing the input-file")
            self.p.add_option("-p", action="store_const", const=True,     
                              dest="pretty_print", help="Pretty printing of the input file")
        
            # Now tell the parser about the default values of all the options
            # we just told it about
            self.p.set_defaults(
                debug_level     = 0,          
                verbose_level   = 0,          
                configfile      = sys.stdin,  
                configfile_name = None,       
                outfile         = sys.stdout, 
                outfile_name    = None,
                lineno_print    = False,       
                pretty_print    = False)       
            
        def parse(self):
            self.options, self.args = self.p.parse_args()
        
            self.debug_level     = self.options.debug_level    
            self.verbose_level   = self.options.verbose_level  
            self.configfile      = self.options.configfile         
            self.configfile_name = self.options.configfile_name    
            self.outfile         = self.options.outfile        
            self.outfile_name    = self.options.outfile_name  
            self.lineno_print    = self.options.lineno_print
            self.token_print     = self.options.token_print
            self.struct_print    = self.options.struct_print
            self.pretty_print    = self.options.pretty_print

            # Check to see if input or output file names have been
            # specified. If so, then try to open them, and if that is
            # successful, replace the default configfile and outfile file
            # descriptors.
            if self.configfile_name:
                try:
                    tmpf = open(self.configfile_name, 'r')
                    self.configfile = tmpf
                except IOError, earg:
                    print "Error opening Input file: -i %s" % (self.configfile_name)
                    print "Expection argument:", earg
                    sys.exit()

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
  configfile     : %s
  configfile_name: %s
  outfile        : %s
  outfile_name   : %s
  lineno_print   : %s
  token_print    : %s 
  struct_print   : %s 
  pretty_print   : %s 
""" 

            str_output = param_print_str % \
                (self.debug_level, 
                 self.verbose_level, 
                 self.configfile, 
                 self.configfile_name, 
                 self.outfile, 
                 self.outfile_name,
                 self.lineno_print,
                 self.token_print,
                 self.struct_print,
                 self.pretty_print)  
            return str_output

    # for each line available on the inport, output it to output prefixed
    # with a line number. Note that the print version has to use negative
    # indexing to cut off the newline terminating the line, while the
    # version using the outport.write method() can output the prefixed
    # string directly
    def number_lines(inport, outport):
        line_number = 1
        for line in inport:
            #print >>outport, "%d: %s" % (line_number, line[:-1])
            outport.write("%d: %s" % (line_number, line))
            line_number = line_number + 1


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

        # Print the input file with line numbers. A sanity
        # check of option parsing and perhaps an aid in
        # debugging parse errors Rewind the file afterward
        # so other options will work.
        if Params.lineno_print:
            number_lines(Params.configfile, Params.outfile)
            Params.configfile.seek(0)

        # Print the set of tokens extracted from the input
        # file. Mostly for curiosity and education, but it
        # may be of some help in debugging and language
        # design.
        #
        if Params.token_print:
            # Make an instance of the lexer class to
            # tokenize the input. Read the entire input file
            # as a string. This is how the lexer requires
            # its input.
            #
            # Afterward, rewind the file handle to the
            # beginning of the file to make sure later
            # options will still work.
            #
            config_lexer = KUSP_Config_Lexer()
            config_lexer.build()

            lex_str = Params.configfile.read()
            config_lexer.test(lex_str, Params.outfile)

            Params.configfile.seek(0)

        # Print the structures derived by parsing the input
        # file.
        if Params.struct_print:
            # Make an instance of the lexer class for the
            # parser to use. Read the entire input file as a
            # string. This is how the lexer requires its
            # input, as passed through the parser, which we
            # also make here.
            #
            # Afterward, rewind the file handle to the
            # beginning of the file to make sure later
            # options will still work.
            #
            config_lexer = KUSP_Config_Lexer()
            config_lexer.build()

            config_parser = yacc.yacc()

            parse_str = Params.configfile.read()

            retval = config_parser.parse(parse_str, lexer=config_lexer.lexer)
            print "Parsing Returned: \n", type(retval)
            pprint(retval)
            
            Params.configfile.seek(0)
            
        # Print the input file with line numbers. A sanity
        # check and perhaps an aid in debugging parse errors
        #
        if Params.pretty_print:
            print "Pretty Print (-p) option not imlemented yet"

    ######################################################
    # This module was called as a program, and so we call
    # create a parameter class instance and the main()
    # function
    ######################################################

    Params = Params_Set()
    main()
