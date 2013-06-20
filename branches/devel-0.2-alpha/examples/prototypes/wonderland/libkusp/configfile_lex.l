%{
#include <stdio.h>
#include <string.h>
#include <configfile.h>
#define MODNAME "Configfile"
#include <kusp_common.h>
#include "configfile_yacc.h"

int lineno;
int tokenpos;
char linebuf[5000];

// FIXME; is there some way we could not use a fixed size buffer?
// yes, use open_memstream
/**
  * buffer to store characters when building string constants
  */
#define STRING_BUF_SIZE 8192
static char string_buf[STRING_BUF_SIZE];
static char *string_buf_ptr;


static struct keyword {
  char *name;
  int value;
} keywords[] = {
	{"true", TRUE},
	{"false", FALSE},
	{NULL, 0}
};

static int keyword(char *string) {
  /* loop through the keyword list, returning a value
     if the keyword was found. if it wasn't in the list
     return 0.
  */
  struct keyword *ptr = keywords;

  for(; ptr->name; ptr++)
    if (strcmp(ptr->name, string) == 0)
      return ptr->value;
  return 0;
}


%}
%option noyywrap
identifier	[a-zA-Z_][a-zA-Z0-9_\-.]*
comment		#.*
int		[-]{0,1}[0-9]+
double		[-]{0,1}[0-9]+[.][0-9]+
long		[-]{0,1}[0-9]+L
lstring		\"\"\"[^"]*?\"\"\"

%x str

%%
\n		{
			//printf("newline\n");
			lineno++;
		}
^.*		{
			strncpy(linebuf, configfiletext, 4999);
			
			linebuf[4999] = '\0';
			//printf("text read %d:%s\n",lineno,linebuf);
			tokenpos = 0;
			yyless(0);
		}
{double}	{
			configfilelval.doubleval = atof(configfiletext);
			tokenpos += yyleng;
			return DOUBLE;
		}
[@]		{
			tokenpos += yyleng;
			return REFERENCE;
		}
{int}		{	
			configfilelval.intval = atoi(configfiletext);
			tokenpos += yyleng;
			return INTEGER;
		}
{long}		{
			char *s = strdup(configfiletext);
			// snip off the trailing L
			s[strlen(s)-1] = '\0';
			configfilelval.longval = atoll(s);
			free(s);
			tokenpos += yyleng;
			return LONG;
		}
{comment}	{
			tokenpos += yyleng;
		}
[, ]		{
			tokenpos += yyleng;
		}
\t		{
			tokenpos += yyleng * 8;
		}
{identifier}	{	
			configfilelval.cmd = keyword(configfiletext);
			tokenpos += yyleng;
			if (configfilelval.cmd != 0) {
				return configfilelval.cmd;
			} else {
				configfilelval.string = strdup(configfiletext);
				return STRING;
			}
		}

\"      	{ /* opening quote for string */
			tokenpos += yyleng;
			string_buf_ptr = string_buf; 
			BEGIN(str);
		}
<str>\"		{ /* saw closing quote - all done */
        		tokenpos += yyleng;
			BEGIN(INITIAL);
        		*string_buf_ptr = '\0';
			configfilelval.string = strdup(string_buf);
       			return STRING;
		}
<str>\n		{
			tokenpos += yyleng;
			configfileerror("unterminated string constant");
        	}

<str>\\[0-7]{1,3} {
			/* octal escape sequence */
        		int result;
			(void) sscanf( yytext + 1, "%o", &result );

			if ( result > 0xff ) {
				configfileerror("bad escape sequence");
			} else {
                	/* error, constant is out-of-bounds */
        			*string_buf_ptr++ = result;
			}
			tokenpos += yyleng;
        	}
<str>\\[0-9]+	{
        		/* generate error - bad escape sequence; something
         		 * like '\48' or '\0777777'
         		 */
			tokenpos += yyleng;
			configfileerror("bad escape sequence");
        	}

<str>\\n 	{
			*string_buf_ptr++ = '\n';
			tokenpos += yyleng;
		}
<str>\\t	{
			*string_buf_ptr++ = '\t';
			tokenpos += yyleng;
		}
<str>\\r	{
			*string_buf_ptr++ = '\r';
			tokenpos += yyleng;
		}
<str>\\b	{
			*string_buf_ptr++ = '\b';
			tokenpos += yyleng;
		}
<str>\\f	{
			*string_buf_ptr++ = '\f';
			tokenpos += yyleng;
		}
<str>\\(.|\n)	{ /* anything that is escaped */
			*string_buf_ptr++ = yytext[1];
			tokenpos += yyleng;
		}
<str>[^\\\n\"]+	{
        		char *yptr = yytext;
        		while ( *yptr ) {
                		*string_buf_ptr++ = *yptr++;
				tokenpos++;
			}
        	}
{lstring}	{	
			char *v = strdup(configfiletext + 3);
			v[configfileleng-6] = '\0';
			configfilelval.string = v;
			tokenpos += yyleng;
			return STRING;
		}
[<>:{}=\[\]()]	{	
			tokenpos += yyleng;
			return configfiletext[0];
		}
.		{	
			tokenpos += yyleng;
			configfileerror("skipping unknown text");
		}

%%

void configfileerror(const char *s) {
	wprintf("%s at '%s' in line %d:\n",
			s, configfiletext, lineno);
	printf("%s\n", linebuf);
	printf("%*s\n", 1+tokenpos, "^\n");
}

