from pykusp import lex
from pykusp import yacc

from pykusp.doubledict import *

import string
import ns_parser_v0 as old_parser
import copy
import os.path

from pykusp.parseexcept import *
from pykusp.configparser import *
from pykusp.namespaces import *

import pprint
import sys
import os

VERSION = "pykusp.parsers.ns_parser_v1"

# ---=== LEX SECTION ===---

tokens = (
    # block types
    'FAMILY',
    'EVENT',
    'HISTOGRAM',
    'OBJECT',
    'COUNTER',
    'INTERVAL',
    'NAMESPACE',
    # literals
    'INT',
    'STRING',
    'LSTRING',
    'VERSION',
    'IDENTIFIER',
    # punctuation
    'OPENDICT',
    'CLOSEDICT',
    'ASSIGNMENT',
    # attribute keywords
    )

keywords = [
    'namespace',
    'family',
    'event',
    'histogram',
    'interval',
    'counter',
    'object'
    ]



def t_VERSION(t):
    r'\A\#\!.*'
    return t


# punctuation
t_OPENDICT = r'\{'
t_CLOSEDICT = r'\}'
t_ASSIGNMENT = r'\='

def t_INT(t):
    r'\d+'
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
    if t.value in keywords:
        t.type = t.value.upper()
        pass
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

# ---=== YACC SECTION ===---


def p_nsfile(p):
    '''nsfile : VERSION namespace'''
    p[0] = p[2]
    p[0].metadata["__writer__"] = VERSION
    pass


#----primitives------------

def p_string(p):
    """string : LSTRING
              | STRING"""
    p[0] = p[1]
    return

def p_assignment(p):
    """assignment : IDENTIFIER ASSIGNMENT string
                  | IDENTIFIER ASSIGNMENT INT"""
    p[0] = (p[1],p[3])
    pass



#-----NAMESPACES-----------



def p_namespace(p):
    '''namespace : NAMESPACE OPENDICT namespacedict CLOSEDICT'''
    p[0] = p[3]
    p[0].__writer__ = VERSION
    pass

# FIXME: put greatest family id in metadata somewhere
def p_namespacedict(p):
    """namespacedict : namespacedict namespaceitem"""
    p[0] = p[1]
    if len(p[2]) == 2:
        # a metadata assignment for the 
        key, value = p[2]
        p[0].metadata[key] = value
    else:
        # a family
        name, id, contents = p[2]
        p[0][name,id] = contents
        pass
    pass
    
def p_namespacedict3(p):
    "namespacedict : empty"
    #print "empty"
    p[0] = create_namespace();
    pass

def p_namespaceitem(p):
    """namespaceitem : assignment
                     | family"""
    p[0] = p[1]
    pass

#-----FAMILIES---------------------

def p_family(p):
    """family : FAMILY IDENTIFIER INT OPENDICT familydict CLOSEDICT"""
    p[5].metadata["name"] = p[2]
    p[5].metadata["id"] = p[3]

    # we need create the metadata for the various types.
    #print "family",p[2]
    for typename in ["event","counter","histogram","interval","object"]:
        greatest = -1
        for ename, eid in p[5][typename]:
            if eid > greatest:
                greatest = eid
                pass
            pass
        p[5][typename].metadata["greatest"] = greatest
        #print p[5].metadata
        pass
    
    p[0] = (p[2],p[3],p[5])
    pass

def p_familydict(p):
    """familydict : familydict familyitem"""
    p[0] = p[1]
    if len(p[2]) == 2:
        # a metadata assignment for the family
        key, value = p[2]
        p[0].metadata[key] = value
    else:
        # an entity
        type, name, id, contents = p[2]
        p[0][type][name,id] = contents
        pass
    pass

def p_familydict3(p):
    """familydict : empty"""
    p[0] = create_family()    
    pass

def p_familyitem(p):
    """familyitem : assignment
                  | entity"""
    p[0] = p[1]
    pass

#------ENTITIES-------------------

def p_entity(p):
    """entity : entitytype IDENTIFIER INT OPENDICT dcontents CLOSEDICT"""
    p[5]["name"] = p[2]
    p[5]["id"] = p[3]
    p[5]["type"] = p[1]
    
    p[0] = (p[1],p[2],p[3],p[5])
    pass


def p_entitytype(p):
    """entitytype : EVENT
                  | OBJECT
                  | COUNTER
                  | HISTOGRAM
                  | INTERVAL"""
    p[0] = p[1]
    pass

def p_dcontents(p):
    '''dcontents : dcontents assignment'''
    p[0] = p[1]
    key, value = p[2]
    p[0][key] = value
    pass


def p_dcontents3(p):
    '''dcontents : empty'''
    p[0] = {}
    pass

# ---=== misc ===---

def p_error(p):
    "error :"
    raise ParseException(p.lineno,"Syntax error. was not expecting "+repr(p.value))
    pass

def p_empty(p):
    'empty :'
    p[0] = None
    pass



def read(filename):
    p = ConcreteParserEngine()
    return p.read(filename)

# if you make more than a few of these very bizarre things
# start to happen. so we make a single instance that everything
# uses.
lexer_instance = lex.lex()
parser_instance = yacc.yacc(debug=0, write_tables=0)
 
def semantic_check(config, debug=False):
    pass

def writer(output_file, dict):

    # helper function
    def write_metadata(dict, output_file, indent):
        keylist = dict.keys()
        keylist.sort()
        for key in keylist:
            if key in ["name","id"]:
                continue

            output_file.write(indent*"\t"+key+" = ")
            value = dict[key]
            if type(value) is str:
                if "\n" in value:
                    output_file.write('"""\n'+value+'\n"""\n')
                else:
                    output_file.write('"'+value+'"\n')
                    pass
                pass
            else:
                output_file.write(str(value)+"\n")
                pass
            pass
        pass

    output_file.write("#!"+VERSION+"\n")

    output_file.write("namespace {\n")
    write_metadata(dict.metadata, output_file, 1)

    # sort by number so it's easy to edit a file by hand
    fkeylist = dict.keys()
    def mycmp(a, b):
        return cmp(a[1], b[1])

    fkeylist.sort(mycmp)

    for fname, fid in fkeylist:
        output_file.write('\tfamily '+fname+' '+str(fid)+' {\n')
        fdict = dict[(fname, fid)]
        write_metadata(fdict.metadata, output_file, 2)
        for f_type in fdict:
            ekeylist = fdict[f_type].keys()
            ekeylist.sort(mycmp)
            for ename, eid in ekeylist:
                output_file.write('\t\t'+f_type+' '+ename+' '+str(eid)+' {\n')
                edict =  fdict[f_type][(ename, eid)]
                write_metadata(edict, output_file, 3)
                output_file.write('\t\t}\n')
                pass
            pass
        output_file.write('\t}\n')
        pass
    output_file.write('}\n')
    pass
   
