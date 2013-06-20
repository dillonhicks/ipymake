#!/usr/bin/env python
# $Id$
#
# AUTHOR(s):  Andrew Boie
#
# Copyright 2005(C), The University of Kansas
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from pykusp import lex
from pykusp import yacc

from pykusp.configparser import *
from group_scheduling.group_lib import *

import copy
import pprint
VERSION="pykusp.parsers.group_sched_parser"

#FIXME: implement checking for circular includes
#FIXME: line numbers aren't being reported properly in error conditions

# ---- LEX SECTION ----

keywords = {
    'computation'        : 'COMPUTATION',
    'group'         : 'GROUP',
    'sdf'           : 'SDF',
    'ssdf'          : 'SSDF',
    
    'string'        : 'STRING_TYPE',
    'integer'       : 'INT_TYPE',
    'long'          : 'LONG_TYPE',
    'float'         : 'FLOAT_TYPE',
    'longlong'      : 'LONG_LONG_TYPE',
    
    'include'       : 'INCLUDE',
    }

tokens = (
    'COMPUTATION',
    'GROUP',
    'SDF',
    'SSDF',
    'INCLUDE',

    'OPAREN',
    'CPAREN',
    'OBRACE',
    'CBRACE',
    'OBRACKET',
    'CBRACKET',
    'OANGLE',
    'CANGLE',
    'COLON',
    'VERSION',
    'EQUALS',
  
    'INT',
    'STRING',
    
    'STRING_TYPE',
    'INT_TYPE',
    'LONG_TYPE',
    'FLOAT_TYPE',
    'LONG_LONG_TYPE',
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
t_COLON  = r'[:]'


def t_INT(t):
    r'[-]{0,1}\d+L{0,1}'
    try:
        t.value = int(t.value)
    except ValueError:
        t.value = long(t.value)
        pass
    return t


def t_VERSION(t):
    r'\A\#\!.*'
    return t

def t_STRING(t):
    r'["\'].*?["\']'
    t.value = t.value[1:-1]
    return t

def t_KEYWORD(t):
    r'\w+'
    if t.value in keywords:
        t.type = keywords[t.value]
        return t
    else:
        print "unrecognized keyword", t.value
        pass
    pass


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

# -- YACC SECTION ------


def p_config_file(p):
    '''config_file : VERSION includes component_def_list'''
    p[0] = {"computation":{},
	    "__writer__":VERSION,
            "sdf":{},
            "ssdf":{},
            "group":{},
            "included":p[2],
            "allsyms":{"computation":{},
                       "sdf":{},
                       "ssdf":{},
                       "group":{}
                       }
            }
    
    for filename, included_dict in p[2]:
        for ict in ["computation","sdf","ssdf","group"]:
            idict = included_dict["allsyms"][ict]
            p[0]["allsyms"][ict].update(idict)
            pass
        pass

    for ict in ["computation","sdf","ssdf","group"]:
        idict = p[3][ict]
        p[0]["allsyms"][ict].update(idict)
        p[0][ict].update(idict)
        pass
    pass



def p_component_def_list(p):
    '''component_def_list : component_def_list definition
                          | empty'''
    if len(p) == 3:
        p[0] = p[1]
        component_type, component_dict = p[2]
        p[0][component_type].update(component_dict)
    else:
        p[0] = {"computation":{},
                "sdf":{},
                "ssdf":{},
                "group":{},
                }
        pass
    pass

def p_includes(p):
    '''includes : includes INCLUDE STRING'''
    p[0] = p[1]
    
    filename = os.path.join(p.parser.basepath, p[3])
    iconfig = read_file(filename)
    
    p[0].append((filename,iconfig))
    pass

def p_includes2(p):
    '''includes : empty'''
    p[0] = []
    pass

def p_type(p):
    '''type : COMPUTATION
            | GROUP
            | SDF
            | SSDF'''
    p[0] = p[1]
    pass




def p_definition(p):
    '''definition : type STRING dictionary'''
    if "comment" not in p[3]:
        p[3]["comment"] = ""
        pass

    
    
    p[0] = (p[1], {p[2]:p[3]})
    p[3]["name"] = p[2]
    p[3]["type"] = p[1]
    if "id" not in p[3]:
        p[3]["id"] = None
        pass
    
    pass

def p_invocation(p):
    '''invocation : type OPAREN STRING CPAREN dictionary
                  | type OPAREN STRING CPAREN'''
    if len(p) == 6:
        p[0] = (p[1], p[3], p[5])
    else:
        p[0] = (p[1], p[3], {})
        pass
    pass


# -- parameter definition
def p_param_dict(p):
    '''paramspec : OANGLE paramcontents CANGLE'''
    p[0] = p[2]
    pass

def p_paramcontents(p):
    '''paramcontents : paramcontents INT datatype STRING COLON STRING
                     | empty'''
    if len(p) == 2:
        p[0] = {}
    else:
        p[0] = p[1]
        # order, type, comment
        p[0][p[4]] = (p[2],p[3],p[6])
        pass
    pass

# -- key/value mapping
def p_dictionary(p):
    '''dictionary : OBRACE dcontents CBRACE'''
    p[0] = p[2]
    pass

def p_dcontents(p):
    '''dcontents : dcontents STRING EQUALS value
                 | empty'''
    if len(p) != 5:
        p[0] = {}
    else:
        p[0] = p[1]
        p[0][p[2]] = p[4]
        pass
    pass

# ordered list of values

def p_list(p):
    '''list : OBRACKET lcontents CBRACKET'''
    p[0] = p[2]
    pass

def p_lcontents(p):
    '''lcontents : lcontents invocation
                 | empty'''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[1]
        p[0].append(p[2])
        pass
    pass


def p_value(p):
    '''value : STRING
             | INT
             | invocation
             | paramspec
             | list'''
    p[0] = p[1]
    pass

def p_datatype(p):
    '''datatype : INT_TYPE
                | STRING_TYPE
                | LONG_TYPE
                | FLOAT_TYPE
                | LONG_LONG_TYPE'''
    p[0] = p[1]
    pass

def p_error(p):
    "error :"
    print p
    raise ParseException(p.lineno,"Syntax error. was not expecting "+repr(p.value))
    pass

def p_empty(p):
    'empty :'
    p[0] = None
    pass



# these MUST be here.
# if you make more than a few of these very bizarre things
# start to happen. so we make a single instance that everything
# uses.
lexer_instance = lex.lex()
parser_instance = yacc.yacc(debug=0, write_tables=0)
print "instances created"

def semantic_check(config_param, debug=False):
    
    config = config_param["allsyms"]
    
    def check_sdf(name):
        #print config["sdf"]
        if name not in config["sdf"]:
            raise SemanticException(
                name, "SDF "+repr(name)+" does not exist.")
        sdf_dict = config["sdf"][name]
        return sdf_dict
    
    def check_computation(name):
        computation_dict = config["computation"][name]
        if "joiner_type" not in computation_dict:
            raise SemanticException(
                computation_dict,
                "Computation does not specify joiner type.")
        jt = computation_dict["joiner_type"]
        if jt not in comp_types:
            raise SemanticException(
                computation_dict,
                "Unknown joiner type "+`jt`+". Known types: "+`comp_types.keys()`
                )
        
        for key, value in computation_dict.iteritems():
            if key in task_param_vals:
                if value not in task_param_vals[key].keys():
                    raise SemanticException(
                        computation_dict,
                        "Key "+key+" only accepts values "+
                        `task_param_restrict[key].keys()`)
                pass
            pass
        pass
    
    def check_group(name, ancestors):
        
        
        ancestors.append(name)
        group_dict = config["group"][name]
        sdf_dict = check_sdf(group_dict["sdf"][1])
        
        match_param(sdf_dict["group"], group_dict["sdf"][2])
        for type, member_name, member_dict in group_dict["members"]:
            if type == "computation":
                if member_name not in config["computation"]:
                    raise SemanticException(member_dict, "Unknown computation "+
                                            repr(member_name)+".")
                check_computation(member_name)
                pass
            elif type == "group":
                if member_name in ancestors:
                    raise SemanticException(
                        ancestors,
                        "Circular reference detected when trying to use "+
                        repr(member_name)+".")
                if member_name not in config["group"]:
                    raise SemanticException(
                        group_dict, "group "+repr(name)+" does not exist.")
                check_group(member_name, ancestors)
                pass
            
            match_param(sdf_dict["member"], member_dict)
            pass
        pass
        
        
    def match_param(paramdict, instancedict):
        typemap = {"integer":int,
                   "string":str,
                   "long":long,
                   "float":float}
        
        for pname in paramdict:
            order, ptype, pval = paramdict[pname]
            if pname not in instancedict:
                raise SemanticException(instancedict,
                                        "Required parameter "+repr(pname)
                                        +" missing.")
            if type(instancedict[pname]) is not typemap[ptype]:
                raise SemanticException(pname,
                                        "Parameter type mismatch. Expecting "
                                        +ptype)
            pass
        pass
    
    
    for ssdf in config["ssdf"]:
        ssdf_dict = config["ssdf"][ssdf]
        if not ssdf_dict.has_key("root"):
            raise SemanticException(ssdf_dict,
                                    "SSDF Does not declare root group!")
        check_group(ssdf_dict["root"][1],[])
        pass
    pass


def writer(output, cdict):
    def writeitem(i, level):
        if type(i) is tuple:
            return writeinvocation(i, level+1)
        elif type(i) is str:
            return repr(i)
        elif type(i) is float or type(i) is int or type(i) is long:
            return str(i)
        elif type(i) is list:
            return writelist(i, level+1)
        elif type(i) is dict:
            return writespec(i, level+1)
        pass
    
    
    def writespec(s, level):
        if not s:
            return "<>"
        
        result = "<\n"
        for key in s:
            result = result + "\t"*level + str(s[key][0]) + " " + str(s[key][1]) + " " + \
                     repr(key) + " : " + repr(s[key][2]) + "\n"
            pass
        result = result + "\t" *(level-1) + ">"
        return result

    def writedict(d, level):
        if not d:
            return "{}"

        result = "{\n"
        #print d
        for key in [item for item in d if item not in ["name","id","type"]]:
            result = result + "\t"*level + repr(key) + " =  " + \
                     writeitem(d[key], level) + "\n"
            pass
        result = result + "\t"*(level-1) + "}"
        return result

    def writelist(l, level):
        if not l:
            return "[]"

        result = "[\n"
        for item in l:
            result = result + "\t"*level + writeitem(item, level) + "\n"
            pass
        result = result + "\t"*(level-1) + "]"
        return result

    def writeinvocation(t, level):
        return t[0]+"("+repr(t[1])+") " + writedict(t[2], level)


    output.write("#!"+VERSION+"\n")

    for filename, idict in cdict["included"]:
        output.write("include " + repr(filename) + "\n")
        pass


    for blockkey in ["computation", "sdf", "group", "ssdf"]:
        for item in cdict[blockkey]:
            output.write(blockkey + " " + repr(item) + " " +
                         writedict(cdict[blockkey][item], 1) + "\n")
            pass 
        pass
    pass
pass
