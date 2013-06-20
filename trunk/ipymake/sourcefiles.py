"""
:mod:`sourcefiles`
=======================

"""

from os.path import splitext
FILENAME, EXTENTION = range(2)

ASM_SOURCE_FILES = ('.asm')
ASM_HEADER_FILES = ('.h')
ASM_FILES = ASM_SOURCE_FILES + ASM_HEADER_FILES

def is_asm_source(srcfile):
    return splitext(srcfile)[EXTENTION] in ASM_SOURCE_FILES


C_SOURCE_FILES = ('.c')
C_HEADER_FILES = ('.h')
C_FILES =  C_SOURCE_FILES + C_HEADER_FILES
C_COMPILER = 'gcc '
C_FLAGS = ('-g','-c', '-fPIC' ,'-Wall ')

def is_c_source(srcfile):
    return splitext(srcfile)[EXTENTION] in C_SOURCE_FILES

CXX_SOURCE_FILES = ('.cpp', '.cc')
CXX_HEADER_FILES = ('.h', '.hpp')
CXX_FILES =  CXX_SOURCE_FILES + CXX_HEADER_FILES
CXX_COMPILER = ' g++ '
CXX_FLAGS = ('-g','-c','-Wall ')

def is_cxx_source(srcfile):
    return splitext(srcfile)[EXTENTION] in CXX_SOURCE_FILES

HASKELL_SOURCE_FILES = ('.hs','.hsc','.lhs')
HASKELL_FILES = HASKELL_SOURCE_FILES
HASKELL_COMPILER = 'ghc '
HASKELL_FLAGS = ()

def is_haskell_source(srcfile):
    return splitext(srcfile)[EXTENTION] in HASKELL_SOURCE_FILES

JAVA_SOURCE_FILES = ('.java',)
JAVA_COMPILED_FILES = ('.class',)
JAVA_FILES =  JAVA_SOURCE_FILES + JAVA_COMPILED_FILES
JAVA_COMPILER = 'javac '


def is_java_source(srcfile):
    return splitext(srcfile)[EXTENTION] in JAVA_SOURCE_FILES

PYTHON_SOURCE_FILES = ('.py',)
SWIG_SOURCE_FILES = ('.i',)

