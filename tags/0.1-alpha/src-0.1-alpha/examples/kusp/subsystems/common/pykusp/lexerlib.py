from lex import *

# literals
t_REAL = r'\d+\.\d+'

def t_INT(t):
    r'\d+L{0,1}'
    try:
        t.value = int(t.value)
    except ValueError:
        t.value = long(t.value)
        pass
    return t

# for strings spanning more than 1 line. using python """ convention.
def t_LSTRING(t):
    r'"""(\n|.)*?"""'
    for char in t.value:
        if char == '\n':
            t.lineno = t.lineno+1
            pass
        pass

    # get rid of quottation at ends and beginnings of token
    t.value = t.value[3:-3]
    
    linelist = t.value.split('\n')
    result = ''
    for line in linelist:
        line = line.strip()
        if not line:
            result = result[:-1] + "\n"
        else:
            result = result + line + " "
            pass
        pass
    
    t.value = result.strip()
    return t

def t_STRING(t):
    r'".*?"'
    t.value = t.value[1:-1]
    return t

def t_IDENTIFIER(t):
    r'\w+'
    return t

# comment
def t_COMMENT(t):
    r'\#.*'
    pass

# whitespace
t_ignore = " \t"
def t_newline(t):
    r'\n+'
    t.lineno += len(t.value)
    pass

def t_error(t):
    print "unrecognized char " + t.value[0]
    t.skip(1)
