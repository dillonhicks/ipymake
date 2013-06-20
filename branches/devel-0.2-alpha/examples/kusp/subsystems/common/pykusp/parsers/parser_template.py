from pykusp.configparser import *
from pykusp.parseexcept import *
from pykusp import lex
from pykusp import yacc

# obviously, change this
VERSION = "lib.parsers.parser_template"

# LEX SECTION
# your lex code goes here

tokens = ( )

# version string
def t_VERSION(t):
    r'\A\#\!.*'
    return t

# ignore comments
def t_COMMENT(t):
    r'\#.*'
    pass

# whitespace
# ignore spaces or tabs
t_ignore = " \t"

# newlines are ignored, but we do like to keep track of line numbers
def t_newline(t):
    r'\n+'
    t.lineno += len(t.value)
    pass

# rule for unexpected characters. may want to modify this to throw
# a parsexception
def t_error(t):
    print "unrecognized char " + t.value[0]
    t.skip(1)


# YACC SECTION
# production rules here
def p_root(p):
    '''config : VERSION list_of_definitions'''
    p[0] = p[1]
    p[0]["__writer__"] = VERSION

    # if your configuration returned an object, rather than a dictionary,
    # you could also do this:

    p[0].__writer__ = VERSION
    pass

# an example of a include rule. we use os.path.join so that the
# included file is located relative to the location of the file
# we are currently reading.
def p_includes(p):
    '''includes : includes INCLUDE STRING'''
    p[0] = p[1]
    
    filename = os.path.join(p.parser.basepath, p[3])
    iconfig = read_file(filename)
    
    p[0].update(iconfig)
    pass


def p_error(p):
    "error :"
    raise ParseException(p.lineno,"Syntax error. was not expecting "+repr(p.value))
    pass

# MISC SECTION

lexer_instance = lex.lex()
parser_instance = yacc.yacc(debug=0, write_tables=0)

def semantic_check(config, debug=False):
    '''perform a semantic check, and raise a SemanticException if any problems are found'''
    return

def writer(configfile, config):
    '''write the datastructure in config to configfile'''
    return
