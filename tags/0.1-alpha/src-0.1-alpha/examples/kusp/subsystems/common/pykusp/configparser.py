#!/usr/bin/env python
#
# $Id: configparser.py,v 1.3 2005/03/04 07:19:18 boie Exp $
#

import pprint
import os
from StringIO import StringIO
import sys
import getopt
import copy
import yacc
import lex
from pykusp.parseexcept import *

#if you would like for configparser to automatically detect what parser should be used to
#write a configuration back to the disk, the dictionary returned by your parser should
#define the key "__writer__" which indicates what parser to use.

# please see parser_template.py for a sample parser module

def read_string(config_string, module_name=None):
    sio = StringIO(config_string)
    result = read_file(sio, module_name)
    sio.close()
    return result

def rewrite(filename, module_name=None):
    config = read_file(filename)
    write_file(filename, config, module_name)
    pass


def read_file(input_file, module_name=None, debug=False, skip_check=False):
    """read an input file and return the configuration dictionary

    input_file can either be a string filename or a file object
    """
    
    closeflag, input_file = _to_object(input_file)
    
    if not module_name:
	# Examine the version string and instantiate
	# the proper parser
	header = input_file.readline()
	input_file.seek(0)      
	if not header.startswith("#!"):
	    raise Exception("I don't know what parser to use on this file, it has no version string.")
	
	module_name = header[2:]
	pass
	    
    try:
	parsermod = fimport(module_name)
    except Exception, e:
	print "Unable to instantiate parser '"+`module_name`+"'."
	raise
    
    # now that we have the proper parser module, retrieve
    # the PLY lexer and parser objects from it.
    lexer = copylexer(parsermod.lexer_instance)
    parser = copyparser(parsermod.parser_instance)
        
    # try to set the base path. this is used when configuration files
    # recursively read other configuration files. it makes sense for
    # files mentioned within a configuration to be given relative
    # to the location of the configuration.
    if hasattr(input_file, "name"):
        parser.basepath = os.path.dirname(os.path.abspath(input_file.name))
        if debug:
            sys.stderr.write("base path: "+str(parser.basepath)+"\n")
            pass
        pass
    else:
        if debug:
            sys.stderr.write("WARNING: file object passed to parse() is not a regular file. recursive calls may b0rk.\n")
            pass
        parser.basepath = os.getcwd()
        pass
    
    input_filestring = input_file.read()
    lexer.input(input_filestring)

    # debug: print the tokens to the screen
    if debug:
        sys.stderr.write("\nlex tokens:\n")
        while True:
            token = lexer.token()
            if token:
                sys.stderr.write(str(token)+"\t")
            else:
                break
            pass
        sys.stderr.write("\n")
        pass
    
    # parse the file.
    config = parser.parse(input_filestring, lexer=lexer)
    
    if not skip_check:
	parsermod.semantic_check(config, debug)
	pass
    
    if closeflag:
	input_file.close()
	pass
    
    return config


def write_file(output_file, config, module_name=None, skip_check=False, debug=False):
    
    if not module_name:
        if hasattr(config, "__writer__"):
            module_name = config.__writer__
        else:
            try:
                module_name = config["__writer__"]
            except KeyError, ke:
                raise Exception("Write unable to write configuration dictionary: key '__writer__' not defined.")
            pass
        pass
    
    try:
	parsermod = fimport(module_name)
    except Exception, e:
	raise Exception("Unable to write configuration: parser module "+`module_name`+" not found or invalid.")
    
    if not skip_check:
	parsermod.semantic_check(config, debug)
	pass
    
    closeflag = False
    
    if type(output_file) is str:
	output_file = file(output_file, 'w')
	closeflag = True
	pass
    
    parsermod.writer(output_file, config)
    
    if closeflag:
	output_file.close()
	pass
    return


## -- private helper functions

def test(filename, debug=False, module_name=None):
    pp = pprint.PrettyPrinter(indent=3)
    
    try:
	print "Reading file..."
	config = read_file(filename, module_name, debug)
    except ParseException, p:
	print "Syntax error!"
	print "Line number:",p.line
	print p.message
	return
    except SemanticException, s:
	print "Semantic error!"
	print s.data
	print s.message
	return
    
    sys.stderr.write("\nDatastructure from parsing config file:\n")
    pp.pprint(config)

        
    # write file, then read back in again
    buff = os.tmpfile()
    if debug:
	sys.stderr.write("\nOutput from write() on preceding datastructure:\n")
	write_file(sys.stderr, config, module_name)
	buff.seek(0)
	pass
    
    write_file(buff, config, module_name)
    buff.seek(0)
    config2 = read_file(buff, module_name, debug)
    buff.close()
    
    # compare first and second datastructures
    if not config == config2:
	print "ERROR! recycled configuration does not match original!"
	return False
    else:
	print "Recycled file datastructure matches original."
	return True
    pass


def copyparser(parser):
    pc = yacc.Parser("xyzzy")
    pc.productions = parser.productions
    pc.errorfunc = parser.errorfunc
    pc.action = parser.action
    pc.goto = parser.goto
    pc.method = parser.method
    pc.require = parser.require
    return pc

def copylexer(lexer):
    c = lex.Lexer()
    c.lexre = lexer.lexre
    c.lexdata = lexer.lexdata
    c.lexpos = lexer.lexpos
    c.lexlen = lexer.lexlen
    c.lexindexfunc = lexer.lexindexfunc
    c.lexerrorf = lexer.lexerrorf
    c.lextokens = lexer.lextokens
    c.lexignore = lexer.lexignore
    c.lineno = lexer.lineno
    c.optimize = lexer.optimize
    c.token = lexer.realtoken
    return c


def fimport(name):
    
    if '.' in name:
        namelist = name.split('.')
        #print "namelist",namelist
        last = namelist[-1].strip()
        #print "last",last
        newname = ""
        for name in namelist[:-1]:
            newname = newname + name + "."
            pass

        #print "newname",newname
        mod = __import__(newname[:-1], globals(), {}, [last])    
        #print "mod",mod
        mod = getattr(mod, last)
    else:
        mod = __import__(name, globals(), {})
        pass
    
    return mod 


def _to_object(input_file):
    if type(input_file) is str:
	input_file = file(input_file)
	closeflag = True
    else:
	closeflag = False
	pass
    
    return closeflag, input_file

    
