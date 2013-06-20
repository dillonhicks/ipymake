/* A Bison parser, made by GNU Bison 2.3.  */

/* Skeleton interface for Bison GLR parsers in C

   Copyright (C) 2002, 2003, 2004, 2005, 2006 Free Software Foundation, Inc.

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2, or (at your option)
   any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor,
   Boston, MA 02110-1301, USA.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.

   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

/* Tokens.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
   /* Put the tokens into the symbol table, so that GDB and other debuggers
      know about them.  */
   enum yytokentype {
     INTEGER = 258,
     DOUBLE = 259,
     LONG = 260,
     TRUE = 261,
     FALSE = 262,
     STRING = 263,
     REFERENCE = 264
   };
#endif


/* Copy the first part of user declarations.  */
#line 1 "/home/hhicks/workspace/kusp/trunk/subsystems/kusp-common/libkusp/configfile_yacc.y"


  /*
   * A parser for namespace files
   */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <configfile.h>
#include <linkedlist.h>
#include <hashtable.h>
#include <sys/types.h>
#include <unistd.h>
#define MODNAME "configfile"
#include <kusp_common.h>
#include <pthread.h>
#include "kusp_private.h"
 
/* store the root of a successful parse here */
static struct hashtable * parse_result;
extern int lineno;
extern char linebuf[5000];
static int hostclobber = 0;

extern int lineno;

static void merge_toplevel(char *name, hashtable_t *target, hashtable_t *source) {
	hashtable_t *shadow = hashtable_merge(target, source);
	
	if (hashtable_count(shadow) > 0) {
		hashtable_itr_t itr;
		init_iterator(&itr, shadow);
		do {
			char *key = hashtable_iterator_key(&itr);
			value_t *value = hashtable_iterator_value(&itr);

			iprintf("In block '%s': key '%s' redefined:\n",
				name, key);
			printf("\twas: ");
			write_value(stdout, value);
			printf("\n\tis now ");
			write_value(stdout, hashtable_search(target, key));
			printf("'\n");
			free_value(value);

		} while (hashtable_iterator_advance(&itr));
	}
	hashtable_destroy(shadow, 0);
}



#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED
typedef union YYSTYPE 
#line 54 "/home/hhicks/workspace/kusp/trunk/subsystems/kusp-common/libkusp/configfile_yacc.y"
{
    void *item;
    int intval;
    long long longval;
    double doubleval;
    struct value_s *value;
    char *string;
    struct hashtable *hash;
    struct list_s *llist;
    invocation_t *invo;
    int cmd;
}
/* Line 2604 of glr.c.  */
#line 124 "/home/hhicks/workspace/kusp/trunk/subsystems/kusp-common/libkusp/configfile_yacc.h"
	YYSTYPE;
# define YYSTYPE_IS_DECLARED 1
# define YYSTYPE_IS_TRIVIAL 1
#endif

#if ! defined YYLTYPE && ! defined YYLTYPE_IS_DECLARED
typedef struct YYLTYPE
{

  char yydummy;

} YYLTYPE;
# define YYLTYPE_IS_DECLARED 1
# define YYLTYPE_IS_TRIVIAL 1
#endif


extern YYSTYPE configfilelval;



