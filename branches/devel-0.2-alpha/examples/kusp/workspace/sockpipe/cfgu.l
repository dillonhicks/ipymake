%{

#include <stdlib.h>
#include <string.h>
#include "cfgu.h"
#include "cfgu_y.hpp"

#define YY_SKIP_YYWRAP

int cfgu_wrap(yyscan_t scanner) { return 1; }

static struct cfguVal* cfgu_new_str(const char* text, int slen)
{
        /* Remove double quotes on each end */
        int to_copy = slen - 2;
        /* Make room for the null byte */
        int new_size = to_copy + 1;

        struct cfguVal* val = (struct cfguVal*)malloc(sizeof(struct cfguVal));
	
        if (!val) {
                return NULL;
        }

        char* copy = (char*)malloc(new_size * sizeof(char));

        /* Copy the string data */
        memcpy(copy, text + 1, to_copy);

        /* Write the null byte */
        copy[new_size - 1] = '\0';

        val->type = CFGU_STRING;
        val->value.str = copy;

        return val;
}

struct cfguVar* cfgu_new_var(const char* name, struct cfguVal* val)
{
	char* name_copy;
	struct cfguVar* var;

	if (!name)
		return NULL;

	name_copy = strdup(name);

	if (!name_copy)
		return NULL;
	
	var = (struct cfguVar*)malloc(sizeof(struct cfguVar));
	
	if (!var) 
		return NULL;
	
	var->name = name_copy;
	var->val = val;
	return var;
}

struct cfguVal* cfgu_new_real(double v)
{
	struct cfguVal* val = (struct cfguVal*)malloc(sizeof(struct cfguVal));
	
	if (!val) {
		return NULL;
	}
	
	val->type = CFGU_REAL;
	val->value.real = v;
	return val;
}

struct cfguVal* cfgu_new_true()
{
	struct cfguVal* val = (struct cfguVal*)malloc(sizeof(struct cfguVal));
	
	if (!val) {
		return NULL;
	}
	
	val->type = CFGU_TRUE;
	return val;
}

struct cfguVal* cfgu_new_false()
{
	struct cfguVal* val = (struct cfguVal*)malloc(sizeof(struct cfguVal));
	
	if (!val) {
		return NULL;
	}
	
	val->type = CFGU_FALSE;
	return val;
}

#define YY_DECL int cfgu_lex(YYSTYPE* yylval_param, yyscan_t yyscanner, struct cfguConfig* config)

%}

%option noinput
%option nounput
%option reentrant
%option bison-bridge

letter      [a-zA-Z]
digit       [0-9]

%%

true {
                yylval->value = cfgu_new_true(); 
                if (yylval->value) {
                       yylval->value->pos = config->pos;
                }
                config->pos.col += yyleng;
                return TRUE;
     }

false {
                yylval->value = cfgu_new_false(); 
                if (yylval->value) {
                       yylval->value->pos = config->pos;
                }
                config->pos.col += yyleng;
                return FALSE;
      }

{letter}({letter}|[-_]|{digit})+ { 
                yylval->var = cfgu_new_var(yytext, NULL);
                if (yylval->var) {
                        yylval->var->pos = config->pos;
                }
                config->pos.col += yyleng;
                return IDENTIFIER; 
        }

{digit}+([.]{digit}+)? { 
                yylval->value = cfgu_new_real(atof(yytext)); 
                if (yylval->value) {
                       yylval->value->pos = config->pos;
                }
                config->pos.col += yyleng;
                return NUMBER; 
        }

["]([^"\\]|\\.)*["] { 
                yylval->value = cfgu_new_str(yytext, yyleng);
                if (yylval->value) { 
                        yylval->value->pos = config->pos;
                }
                config->pos.col += yyleng;
                return STRING; 
        }

\[|\]|[{}=,] { yylval->pos = config->pos; ++config->pos.col; return *yytext; }

[\n] { ++config->pos.line; config->pos.col = 0; }

[ ] ++config->pos.col;

[\t] config->pos.col += 8;

. { ++config->pos.col; }

%%

