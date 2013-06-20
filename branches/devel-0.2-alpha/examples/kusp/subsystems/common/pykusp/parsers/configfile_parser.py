from lib.configparser import *
from lib.parseexcept import *
from lib import lex
from lib import yacc

# obviously, change this
VERSION = "lib.parsers.parser_template"

# LEX SECTION
# your lex code goes here

keywords = {
    'true' : 'TRUE',
    'false' : 'FALSE'
    }

tokens = (
    'DOUBLE',
    'INTEGER',
    'STRING',

# various punctutation
    'OANGLE',
    'CANGLE',
    'OBRACKET',
    'CBRACKET',
    'OPAREN',
    'CPAREN',
    'OBRACE',
    'CBRACE',
    'EQUALS',

# keywords
    'TRUE',
    'FALSE'
    )

t_OBRACE = r'\{'
t_CBRACE = r'\}'
t_OPAREN = r'\('
t_CPAREN = r'\)'
t_OBRACKET = r'\['
t_CBRACKET = r'\]'
t_EQUALS = r'\='
t_OANGLE = r'[<]'
t_CANGLE = r'[>]'

# version string
def t_VERSION(t):
    r'\A\#\!.*'
    pass

# ignore comments
def t_COMMENT(t):
    r'\#.*'
    pass

def t_IDENTIFIER(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    if t.value in keywords:
        t.type = keywords[t.value]
    else:
        t.type = 'STRING'
        pass
    return t

def t_STRING(t):
    r'\"[^"\n]*["\n]'
    t.value = t.value[1:-1]
    return t

def t_LSTRING(t):
    r'\"\"\"[^"]*?\"\"\"'
    t.value = t.value[3:-3]
    t.type = 'STRING'
    return t

def t_DOUBLE(t):
    r'[-]{0,1}[0-9]+\.[0-9]+'
    t.value = float(t.value)
    return t



def t_INTEGER(t):
    r'[-]{0,1}[0-9]+'
    try:
        t.value = int(t.value)
    except ValueError:
        t.value = long(t.value)
        pass
    return t




# whitespace
# ignore spaces or tabs
t_ignore = ", \t"

# newlines are ignored, but we do like to keep track of line numbers
def t_newline(t):
    r'\n+'
    t.lineno += len(t.value)
    pass

# rule for unexpected characters. may want to modify this to throw
# a parsexception
def t_error(t):
    raise ParseException(t.lineno, "unrecognized char " + t.value[0])
    pass



# ---- YACC SECTION ------
def p_toplevel(p):
    '''toplevel : toplevel OANGLE STRING CANGLE dcontents'''
    p[0] = p[1]
    p[0][p[3]] = p[5]
    pass

def p_toplevel2(p):
    '''toplevel : empty'''
    p[0] = {}
    pass

def p_abstractvalue(p):
    '''abstractvalue : dictionary
                     | list
                     | invocation
                     | STRING
                     | INTEGER
                     | DOUBLE'''
    p[0] = p[1]
    pass

def p_abstractvalue2(p):
    '''abstractvalue : TRUE'''
    p[0] = True
    pass

def p_abstractvalue3(p):
    '''abstractvalue : FALSE'''
    p[0] = False
    pass

def p_invocation(p):
    '''invocation : STRING OPAREN dcontents CPAREN'''
    p[0] = (p[1],p[3])
    pass

def p_dictionary(p):
    '''dictionary : OBRACE dcontents CBRACE'''
    p[0] = p[2]
    pass

def p_dcontents(p):
    '''dcontents : dcontents STRING EQUALS abstractvalue'''
    p[0] = p[1]
    if p[2] in p[0]:
        raise ParseException(p.lineno,"Key "+`p[2]`+" already defined.");
    p[0][p[2]] = p[4]
    pass

def p_dcontents2(p):
    '''dcontents : empty'''
    p[0] = {}
    pass

def p_list(p):
    '''list : OBRACKET lcontents CBRACKET'''
    p[0] = p[2]
    pass

def p_list2(p):
    '''list : OBRACKET CBRACKET'''
    p[0] = []
    pass

def p_lcontents(p):
    '''lcontents : abstractvalue lcontents'''
    p[0] = p[2]
    p[0].insert(0, p[1])
    pass

def p_lcontents2(p):
    '''lcontents : abstractvalue'''
    p[0] = [p[1]]
    pass

def p_empty(p):
    '''empty :'''
    pass

def p_error(p):
    '''error :'''
    raise ParseException(p.lineno,"Syntax error. was not expecting "+repr(p.value))
    pass

# MISC SECTION

lexer_instance = lex.lex()
parser_instance = yacc.yacc(debug=0, write_tables=0)

def semantic_check(config, debug=False):
    '''perform a semantic check, and raise a SemanticException if any problems are found'''
    return

def writer(output, config):
    '''write the datastructure in config to output'''

    
    return
