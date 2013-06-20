"""
:mod:`makefilecompiler` -
======================================================

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>


"""
import sys
import os
import ply.lex as lex
from exceptions import SyntaxError
import types
import operator as op



class MakefileLexer:
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
        'NUMBER',

        'PLUS',
        'MINUS',
        'PERIOD',
        'ASTERISK',
        'COLON',
        'DOLLARSIGN',
        'QUOTE',
        'TILDA',
        'BACK_SLASH',
        'FORWARD_SLASH',
        'ACCENT',
        'AMPERSAND',
        'ATSIGN',
        'TAB'
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
    t_PLUS         = r'[+]'
    t_MINUS        = r'[-]'
    t_PERIOD       = r'[.]'
    t_ASTERISK     = r'[*]'
    t_COLON        = r'[:]'
    t_DOLLARSIGN   = r'[$]'
    t_QUOTE        = r"[']"
    t_TILDA        = r'[~]'
    t_BACK_SLASH   = r'[\\]'
    t_FORWARD_SLASH= r'[/]'
    t_ACCENT       = r'[`]'
    t_AMPERSAND    = r'[&]'
    t_ATSIGN       = r'[@]'
    t_TAB          = r'\t'

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
    t_ignore = " "

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
    def test(self, input_string, outfile=sys.stdout):
        self.lexer.input(input_string)
        while True:
             token = self.lexer.token()
             if not token: 
                 break

             print >>outfile, "T(%d): " % (self.lexer.lineno), token


if __name__ == "__main__":
    from pprint import pprint
    make_string = open(sys.argv[1], 'r').read()
    makelexer = MakefileLexer()
    makelexer.build()
    makelexer.test(make_string)

  

