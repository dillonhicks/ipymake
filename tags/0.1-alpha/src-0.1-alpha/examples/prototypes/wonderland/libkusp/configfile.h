/** @file */


#ifndef __CONFIGFILE_H__
#define __CONFIGFILE_H__

#include <stdio.h>
#include "hashtable.h"
#include "linkedlist.h"

/**
 * This ia an enumeration of the various datatypes that
 * can be stored within a value_t.
 */
typedef enum valuetype_e {
	/** Dictionary, which is implemented as hashtable_t */
	DICTTYPE,

	/** String, represented by pointer to char */
	STRINGTYPE,

	/** Integer */
	INTTYPE ,

	/** Linked list, implemented as list_t in linkedlist.h */
	LISTTYPE,

	/** Floating point, using double */
	DOUBLETYPE,

	/** Invocation, which is a string name
	 * and a dictionary of parameters associated
	 * with the 'invocation' of that name */
	INVOTYPE,

	/** Boolean true/false, represented by an int that is
	 * zero or nonzero */
	BOOLTYPE,

	/** Long integer, represented by long long type */
	LONGTYPE,

	/** reference to other value stored in top-level
	 * hashtable */
	REFTYPE

} valuetype_t;

/**
 * An invocation is like a function call, with
 * a name that is 'invoked' with a set of parameters.
 * What an invocation _means_ is entirely situational
 * and application dependent.
 */
typedef struct invocation_s {
	/** The name being invoked. For example,
	 * a call to foo() the name is "foo" */
	char *name;

	/** A set of parameters associated with the
	 * invocation. This is a configfile dictionary. */
	hashtable_t *params;
} invocation_t;

/**
 * All data placed in configfile container datastructures
 * is encapsulated in these value_t structures. This allows
 * for a form of introspection; you do not need to know in
 * advance what the type of the stored data is.
 *
 * the unhash_*, unlist_*, and encap_* family of functions
 * perform operations on these value_t structures so that
 * you won't have to deal with them directly.
 *
 * this is an opaque type which should never be used directly
 */
struct value_s;
typedef struct value_s value_t;

/* ########## FILE I/O ###############
 * read a config file and return a datastructure */
hashtable_t *parse_config_file(FILE * infile);
hashtable_t *parse_config(char *filename);
hashtable_t *parse_config_string(char *config);

int check_spec(hashtable_t *spec);
hashtable_t *parse_spec(char *filename);
hashtable_t *parse_spec_string(char *config);


hashtable_t *get_config(char *filename, char *specfilename,
		void **varlist) __attribute__((deprecated));
hashtable_t *process_configfile(hashtable_t *cfg, hashtable_t *spec,
		void **varlist);



/* FIXME: we need a function to parse a config file
 * without using the preprocessor */


/* uses the various prettyprint functions to write the config back to disk */
int write_config(FILE *fil, hashtable_t *config);
void config_to_string(hashtable_t *config, size_t *size, char **ptr);


/* recursively frees everything */
void free_config(hashtable_t *config);

/* verification functions */
struct vexcept *verify_config_dict(hashtable_t *config, 
		hashtable_t *spec,
		void **varlist);
void print_vexcept(struct vexcept *ex);

void free_vexcept(struct vexcept *ex);

/* ######## dictionary functions ############ */

/* these functions extract pointers to stored values in a hashtable */
int unhash_int(hashtable_t *h, char *key, int *val);
int unhash_bool(hashtable_t *h, char *key, int *val);
int unhash_double(hashtable_t *h, char *key, double *val);
int unhash_string(hashtable_t *h, char *key, char **val);
int unhash_hashtable(hashtable_t *h, char *key, hashtable_t **val);
int unhash_list(hashtable_t *h, char *key, list_t **val);
int unhash_invoc(hashtable_t *h, char *key, invocation_t **invo);
int unhash_long(hashtable_t *h, char *key, long long *val);


// XXX; NOT IMPLEMENTED
#if 0
int hashval_int(hashtable_t *h, char *key, int *retval);
int hashval_bool(hashtable_t *h, char *key, int *retval);
double hashval_double(hashtable_t *h, char *key, int *retval);
char *hashval_string(hashtable_t *h, char *key, int *retval);
hashtable_t *hashval_hashtable(hashtable_t *h, char *key, int *retval);
list_t *hashval_list(hashtable_t *h, char *key, int *retval);
invocation_t *hashval_invoc(hashtable_t *h, char *key, int *retval);
long long *hashval_long(hashtable_t *h, char *key, int *retval);
#endif

valuetype_t hashtable_get_type(hashtable_t *h, char *key);

/* creates an empty configuration hashtable */
hashtable_t *create_dictionary(void);

void prettyprint_hash(hashtable_t *hash);

/* ########## list functions ############# */

/* these functions get a pointer to the stored value at the current list
 * location. use these within a list_for_each block. */
int unlist_int(list_t *list, int *val);
int unlist_bool(list_t *list, int *val);
int unlist_double(list_t *list, double *val);
int unlist_string(list_t *list, char **val);
int unlist_hashtable(list_t *list, hashtable_t **val);
int unlist_list(list_t *list, list_t **val);
int unlist_invoc(list_t *list, invocation_t **invo);
int unlist_long(list_t *list, long long *val);




/* new style extraction functions, can be used in expressions */
// XXX NOT IMPLEMENTED
#if 0
int listval_int(list_t *list, int *retval);
int listval_bool(list_t *list, int *retval);
double listval_double(list_t *list, int *retval);
char *listval_string(list_t *list, int *retval);
hashtable_t *listval_hashtable(list_t *list, int *retval);
list_t *listval_list(list_t *list, int *retval);
invocation_t *listval_invoc(list_t *list, int *retval);
long long listval_long(list_t *list, int *retval);
#endif

#define list_for_each_int(pos, head, x) \
	for (pos = (head)->next, x = (pos->item ? ((value_t*)(pos->item)).i : 0); \
		pos != (head); pos = pos->next)


/* returns the type of the item at the current list position.
 * useful if you are iterating over a list's contents and are uncertain
 * about the type of values it contains. */
valuetype_t listitem_type(list_t *list);

/* is this value in a list? */
int list_membership_test(list_t *head, const value_t *v);
int string_inside_list(list_t *head, char *string);

/* print the list nicely to stdout */
void prettyprint_list(list_t *list);

/* ######## value_t functions ########### */


valuetype_t value_type(value_t *val);

/* creation of value_t is handled by these encapsulation functions. */

/* these encapsulation methods allocate memory for a copy
 * of the data, and return a value_t that holds it. */
value_t *encap_int(int value);
value_t *encap_bool(int value);
value_t *encap_double(double value);
value_t *encap_long(long long value);
/* copies the string; does not take ownership */
value_t *encap_string(const char *value);
/* takes ownership of the string */
value_t *encap_string_ptr(const char *value);
value_t *encap_hash(hashtable_t *hash); 
value_t *encap_invoc(invocation_t *invoc);
value_t *encap_list(list_t *list);
value_t *encap_reference(char *ref);


// Extraction functions.
long long as_long_long(value_t *v);
char *as_string(value_t *v);
struct hashtable *as_hashtable(value_t *v);
list_t *as_list(value_t *v);
int as_bool(value_t *v);
int as_int(value_t *v);



int valcmp(const value_t *v1, const value_t *v2);

/* destroys the value container and the item stored within it,
 * recursively in the case of lists and hashtables */
void free_value(value_t *value);

void prettyprint_value(value_t *value);
void write_value(FILE *fil, value_t *value);
value_t *copy_value(value_t *v);
void fix_toplevel(value_t *v, hashtable_t *toplevel);
void strip_context_lists(value_t *v) ;

/* ########### MISC ############### */
char *get_type_name(valuetype_t v);

/* stuff that lex/yacc needs */
extern FILE* configfilein;
void configfileerror(const char *s);
int configfilelex(void);
int preprocess(void);
extern FILE* preprocin;
extern FILE* preprocout;

/* stuff python module needs */
value_t *follow(const value_t *v);
#endif
