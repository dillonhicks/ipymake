%{
#include <stdlib.h>
#include <string.h>
#define MODNAME "configfile preprocessor"
#include <kusp_common.h>
#include <hashtable.h>

static struct hashtable *env = NULL;

// TODO: track line numbers for error messages

#define MAX_INCLUDE_DEPTH 10
YY_BUFFER_STATE include_stack[MAX_INCLUDE_DEPTH];
int include_stack_ptr = 0;
int ifdef_nest = 0;
char *define_key;

%}

ID	[A-Za-z_][A-Za-z0-9_]*
DIGIT	[0-9]

%option noyywrap
%option prefix="preproc"
%option outfile="preproc_lex.c"
%option nostdinit

%x incl define1 define2 define3 ifdef1 ifdef2 ifdef3
%%

[$][1-9][(]{ID}[)]	{
		char numc[2] = {preproctext[1], '\0'};
		int num = atoi(numc) - 1;
		if (num == 0) {
			fprintf(preprocout, "$%s", preproctext+2);
		} else {
			fprintf(preprocout, "$%d%s", num, preproctext+2);
		}
	}

[$][(]{ID}[)]		{
		char *key = strdup(preproctext + 2);
		key[strlen(key) - 1] = '\0';
		char *val = (char*)hashtable_search(env, key);

		if (val == NULL) {
			val = getenv(key);
		}
		
		if (val == NULL) {
			wprintf("variable $(%s) referenced before assignment, and not found in system environment.\n",
				key);
			ECHO;
		} else {
			// we did a replacement, so put the replacement
			// back on the input stream, for possible further
			// processing.
			char *p = val;
			char *q = p + strlen(p);
			while (q > p) {
				unput(*--q);
			}
		}
		free(key);
	}

[@]define		BEGIN(define1);

[@]include		BEGIN(incl);

[@]ifdef		{
	BEGIN(ifdef1);
}

[@]endif		{
		ifdef_nest--;
		if (ifdef_nest < 0) {
			eprintf("@endif without matching ifdef!");
		}
	}
	
.			ECHO;

<ifdef1>[ \t]*
<ifdef1>[A-Za-z][A-Za-z0-9_]*  {
// this state consumes the define's identifier
		char *key = strdup(yytext);

		ifdef_nest++;
		if (hashtable_search(env, key) || getenv(key)) {
			free(key);
			// It is defined
			BEGIN(INITIAL);
		} else {
			free(key);
			BEGIN(ifdef3);
		}
	}
<ifdef3>[@]endif {
		ifdef_nest--;
		if (ifdef_nest < 0) {
			eprintf("@endif without matching ifdef!");
		}
		BEGIN(INITIAL);
	}
<ifdef3>.	{ 
		// Do nothing
	}
<ifdef3>[^\n]* 	{
		// Do nothing
	}


<define1>[ \t]*
<define1>[A-Za-z][A-Za-z0-9_]*  {
		// this state consumes the define's identifier
		define_key = strdup(yytext);
		BEGIN(define2);
	}
<define2>[ \t]*
<define2>[^ \t]		{
		// this state consumes any whitespace between the identifier
		// and the definition
		yyless(0);
		BEGIN(define3);
	}
<define3>[^\n]* 	{
		// this state consumes the definition.
		char *define_val = strdup(yytext);

		hashtable_insert(env, define_key, define_val);
		BEGIN(INITIAL);
	}


<incl>[ \t]*      	/* eat the whitespace */
<incl>[^ \t\n]+   	{ 
		/* got the include file name */
        	if ( include_stack_ptr >= MAX_INCLUDE_DEPTH ) {
            		eprintf("Includes nested too deeply, not including '%s'",
					yytext);
			goto exitrule;
            	}

		FILE *included = fopen(yytext, "r");
		if (included == NULL) {
			eprintf("Unable to find include file '%s'.\n", yytext);
			goto exitrule;
		}
		
        	include_stack[include_stack_ptr] = YY_CURRENT_BUFFER;
		include_stack_ptr++;

        	preprocin = included;
		preproc_switch_to_buffer(
			preproc_create_buffer(preprocin, YY_BUF_SIZE ) );
exitrule:
        	BEGIN(INITIAL);
        }

<<EOF>> 		{
		include_stack_ptr--;
        	if (include_stack_ptr < 0) {
            		yyterminate();
            	} else {
            		preproc_delete_buffer( YY_CURRENT_BUFFER );
            		preproc_switch_to_buffer(include_stack[include_stack_ptr]);
            	}
	}

%%

int preprocess(void) {
	int retval;
	env = create_hashtable(8, hash_string, string_key_equal );
	retval = preproclex();
	hashtable_destroy(env, 1);
	return retval;
}


