%{

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

%}

%union {
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
};

%token <intval> INTEGER 
%token <doubleval> DOUBLE 
%token <longval> LONG
%token <cmd> TRUE FALSE
%token <string> STRING
%token <item> REFERENCE
%type <hash> dictionary dcontents toplevel
%type <llist> list lcontents
%type <invo> invocation
%type <value> abstractvalue

// we need this to resolve a shift-reduce conflict with invocations.
// with LALR(1), it cannot distinguish between a string and the beginning
// of a dictionary
%glr-parser
%expect 1
%%


/* FIXME: Line numbering is a little wonky. The line number assigned to a value
 * is the line number of the *next* token in the input stream after the value
 * is constructed. This flaw is more annoying than fatal and it might be more
 * tricky to fix than it is worth */

// toplevel is a hashtable
toplevel	: toplevel '<' STRING '>' dcontents {
			$$ = $1;
			hashtable_t *olddict = NULL;
			unhash_hashtable($$, $3, &olddict);
			if (olddict) {
				iprintf("Previous instance of toplevel block '%s' exists; merging values.\n", $3);
				// we already have a toplevel dictionary
				// with this name. we will attempt to merge the two
				// FIXME: make shadowing an option?

				merge_toplevel($3, olddict, $5);
			} else {
				value_t *v = encap_hash($5);
				v->lineno = lineno;
				hashtable_insert($$, $3, v);
			}
		}
		| empty {
			$$ = create_dictionary();
			parse_result = $$;
		}
		;

// dictionary is a hashtable
dictionary	: '{' dcontents '}' {
			$$ = $2;
		}
		;

		
// a value_t, which abstracts away what the actual item is
abstractvalue	: dictionary {
			$$ = encap_hash($1);
			$$->lineno = lineno;
		}
		| list {
			$$ = encap_list($1);
			$$->lineno = lineno;


		}
		| invocation {
			$$ = encap_invoc($1);
			$$->lineno = lineno;

		}
		| STRING {
			$$ = encap_string_ptr($1);
			$$->lineno = lineno;

		}		
		| INTEGER {
			$$ = encap_int($1);
			$$->lineno = lineno;

		}
		| DOUBLE {
			$$ = encap_double($1);
			$$->lineno = lineno;

		}
		| LONG {
			$$ = encap_long($1);
			$$->lineno = lineno;

		}
		| TRUE {
			$$ = encap_bool(1);
			$$->lineno = lineno;

		}
		| FALSE {
			$$ = encap_bool(0);
			$$->lineno = lineno;

		}
		| REFERENCE STRING {
			$$ = encap_reference($2);
			$$->lineno = lineno;

		}
		;

invocation	: STRING '(' dcontents ')' {
			$$ = malloc(sizeof(invocation_t));
			$$->name = $1;
			$$->params = $3;
		}

		| STRING '(' abstractvalue ')' {
			hashtable_t *implicit = create_dictionary();
			$$ = malloc(sizeof(invocation_t));
			$$->name = $1;
			hashtable_insert(implicit, strdup("implicit"), $3);
			$$->params = implicit;
		}
		;

// dcontents is a hashtable
dcontents	: dcontents STRING '=' abstractvalue {
			$$ = $1;

			// duplication of keys in same block will be
			// interpreted as mistake or typo
			if (hashtable_search($$, $2)) {
				configfileerror("Duplicate dictionary key");
				YYABORT;
			} else {
				hashtable_insert($$, $2, $4);
			}				
		}
		| empty {
			$$ = create_hashtable(16, hash_string, string_key_equal);
		}
		;

// list is a linkedlist
list		: '[' lcontents ']' {
			$$ = $2;
		}
		| '[' ']' {
			$$ = create_list();
		}
		;

// lcontents is a linkedlist
// if we wanted to enforce commas between list
// elements, we would have "lcontents : abstractvalue ',' lcontents"

lcontents	: abstractvalue lcontents {
			$$ = $2;
			list_prepend($$, $1);
		}
		| abstractvalue {
			$$ = create_list();
			list_prepend($$, $1);
		}
		;

empty		:
		;


%%

static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
	

struct hashtable* parse_config_file(FILE * infile) {
	hashtable_t *retval = NULL;
	FILE  *exchange_file;

	// lex/yacc are state machines with global variables.
	// i can only imagine horrible things happening if multiple
	// threads tried to use them simulataneously. hence, i guard
	// the whole thing with a mutex.
	pthread_mutex_lock(&mutex);
	
	lineno = 1;
	linebuf[0] = '\0';
	
	exchange_file = tmpfile();
	if (!exchange_file) {
		perror("tmpfile");
		goto exit;
	}

	// preprocess data and store in tmp file
	preprocin = infile;
	preprocout = exchange_file;
	preprocess();
	rewind(exchange_file);

	// parse pre-processed config file
	configfilein = exchange_file;
	if (!configfileparse())
		retval = parse_result;
	
	// done with tmp file
	fclose(exchange_file);

	if (retval) {
		value_t *v = encap_hash(retval);
		v->lineno = -3;
		// update all the toplevel pointers
		fix_toplevel(v, retval);
		free(v);
	}
exit:
	parse_result = NULL;
	pthread_mutex_unlock(&mutex);
	return retval;
}


