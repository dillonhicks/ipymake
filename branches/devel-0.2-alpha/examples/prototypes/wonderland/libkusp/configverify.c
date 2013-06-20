#define _GNU_SOURCE

#include <config.h>

#include <configfile.h>
#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <linkedlist.h>
#include <hashtable.h>
#include <kusp_common.h>
#include <errno.h>
#include <exception.h>
#include <stdarg.h>
#include <stdio.h>


#include "kusp_private.h"


// some globals
hashtable_t *toplevel;
void **varlist;


static struct vexcept *create_vexcept(const char *fmt, ...)
{
	/* Guess we need no more than 100 bytes. */
	int n, size = 100;
	char *p, *np;
	va_list ap;

	if ((p = malloc(size)) == NULL)
		return NULL;

	while (1) {
		/* Try to print in the allocated space. */
		va_start(ap, fmt);
		n = vsnprintf(p, size, fmt, ap);
		va_end(ap);
		/* If that worked, return the string. */
		if (n > -1 && n < size)
			break;
		/* Else try again with more space. */
		if (n > -1)	/* glibc 2.1 */
			size = n + 1;	/* precisely what is needed */
		else		/* glibc 2.0 */
			size *= 2;	/* twice the old size */
		if ((np = realloc(p, size)) == NULL) {
			free(p);
			return NULL;
		} else {
			p = np;
		}
	}

	struct vexcept *ex = malloc(sizeof(*ex));
	ex->message = p;
	ex->next = NULL;

	return ex;
}

void print_vexcept(struct vexcept *ex)
{
	while (ex != NULL) {
		fprintf(stderr, "%s", ex->message);
		ex = ex->next;
	}
	printf("\n");
}

void free_vexcept(struct vexcept *ex)
{
	while (ex != NULL) {
		struct vexcept *n = ex->next;
		free(ex);
		ex = n;
	}
}

valuetype_t get_valuetype_from_name(char *name) {
	if (strcmp(name, "integer") == 0) {
		return INTTYPE;
	}
	if (strcmp(name, "dictionary") == 0) {
		return DICTTYPE;
	}
	if (strcmp(name, "string") == 0) {
		return STRINGTYPE;
	}
	if (strcmp(name, "list") == 0) {
		return LISTTYPE;
	}
	if (strcmp(name, "real") == 0) {
		return DOUBLETYPE;
	}
	if (strcmp(name, "invocation") == 0) {
		return INVOTYPE;
	}
	if (strcmp(name, "boolean") == 0) {
		return BOOLTYPE;
	}
	if (strcmp(name, "long") == 0) {
		return LONGTYPE;
	}
	eprintf("unknown type %s\n", name);
	return 0;
}


static int check_type(valuetype_t t, hashtable_t * spec)
{
	list_t *pos, *types;
	char *typename;
	valuetype_t spectype;

	if (unhash_list(spec, "types", &types)) {
		eprintf
		    ("Unspecified type; use types = [\"any\"] for any type\n");
		return -1;
	}

	list_for_each(pos, types) {
		unlist_string(pos, &typename);
		if (strcmp(typename, "any") == 0) {
			return -1;
		}

		spectype = get_valuetype_from_name(typename);
		if (spectype == t) {
			return -1;
		}
	}
	return 0;
}

static void assign_variable(value_t * val, void *ptr)
{
	switch (val->type) {
	case INTTYPE:
	case BOOLTYPE:
		*((int *)ptr) = val->value.i;
		break;
	case LONGTYPE:
		*((long long *)ptr) = val->value.g;
		break;
	case DOUBLETYPE:
		*((double *)ptr) = val->value.d;
		break;
	case STRINGTYPE:
		*((char **)ptr) = val->value.s;
		break;
	case DICTTYPE:
		*((hashtable_t **) ptr) = val->value.h;
		break;
	case INVOTYPE:
		*((invocation_t **) ptr) = val->value.v;
		break;
	case LISTTYPE:
		*((list_t **) ptr) = val->value.l;
		break;
	case REFTYPE:
		eprintf("Attempted to assign reference\n");
		break;
	}
}
//#define DEBUG_CHECKER


#ifndef DEBUG_CHECKER
#undef debug_action
#undef dprintf
#define debug_action if(0)
#define dprintf(...)
#endif

static int verify_config_list(list_t * config, hashtable_t *spec);
static int verify_config_invocation(invocation_t * invo, hashtable_t * invodef,
		hashtable_t *openinvodef);
static int verify_config_dictionary(hashtable_t * config, hashtable_t * spec,
				    int ignore_unknown);
static int verify_config_opendict(hashtable_t * config, hashtable_t * spec,
				  hashtable_t * dictdef);



/*
 * XXX: spec is not necessarily the toplevel hash of the specification file.
 * This function is recursively called on both item and spec.
 */
static int verify_config_item(value_t * item, hashtable_t * spec)
{

	int maxlen = -1;
	list_t *cur;
	item = follow(item);
	debug_action {
		fflush(stdout);
		printf("#################\nCHECKING ITEM\n");
		fflush(stdout);

		printf("LINE #%d %s\n", item->lineno, get_type_name(item->type));
		prettyprint_value(item);

		//printf("\nAGAINST SPEC\n");
		//fflush(stdout);
		//prettyprint_hash(spec);
		printf("\n\n");
	}

	if (item->context == NULL) {
		dprintf("Creating new list\n");
		item->context = create_list();
	} else {
		list_for_each(cur, item->context) {
			if (cur->item == spec) {
				dprintf
				    ("Skipping value already examined in this context\n");
				return 0;
			}
		}
	}

	list_prepend(item->context, spec);

	try {

	if (!check_type(item->type, spec)) {
		// try to do some re-casting
		if (item->type == STRINGTYPE && check_type(INVOTYPE, spec)) {
			struct invocation_s *i = malloc(sizeof *i);
			i->name = item->value.s;
			i->params = create_dictionary();
			item->type = INVOTYPE;
			item->value.v = i;
		} else if (item->type == INTTYPE && check_type(LONGTYPE, spec)) {
			long long g = item->value.i;
			item->type = LONGTYPE;
			item->value.g = g;
		} else if (item->type == INTTYPE &&
			   check_type(DOUBLETYPE, spec)) {
			double d = (double)item->value.i;
			item->type = DOUBLETYPE;
			item->value.d = d;
		} else if (item->type == LONGTYPE &&
			   check_type(DOUBLETYPE, spec)) {
			double d = (double)item->value.g;
			item->type = DOUBLETYPE;
			item->value.d = d;
		} else if (item->type == INTTYPE && check_type(BOOLTYPE, spec)) {
			item->type = BOOLTYPE;
		} else if (check_type(LISTTYPE, spec)) {
			list_t *l = create_list();
			value_t *v = malloc(sizeof(value_t));
			memcpy(v, item, sizeof(value_t));
			v->context = NULL;
			list_append(l, v);
			item->type = LISTTYPE;
			item->value.l = l;
		} else {
			// can't recast; generate error
#ifdef HAVE_OPEN_MEMSTREAM
			list_t *pos, *types;
			char *typename;
			size_t msg_size;

			FILE *strstream = open_memstream(&msg, &msg_size);

			unhash_list(spec, "types", &types);

			fprintf(strstream, "Type mismatch; expected one of [");
			list_for_each(pos, types) {
				unlist_string(pos, &typename);
				fprintf(strstream, "%s ", typename);
			}

			fprintf(strstream, "] got %s.\n",
				get_type_name(item->type));
			fclose(strstream);
#else
			char *msg;
			msg = strdup("type mismatch");
#endif
			struct vexcept *ex = create_vexcept(msg);
			throw(ex);
		}
	}

	if (hashtable_search(spec, "strlen")) {
		unhash_int(spec, "strlen", &maxlen);
	}

	// TODO: add range checking semantics

	if (hashtable_search(spec, "constraints")) {
		list_t *constraints;
		unhash_list(spec, "constraints", &constraints);
		if (!list_membership_test(constraints, item)) {
			char *msg;
#ifdef HAVE_OPEN_MEMSTREAM
			size_t msg_size;
			list_t *pos;
			FILE *strstream = open_memstream(&msg, &msg_size);

			fprintf(strstream, "Constraint failure; value must be one of [");

			list_for_each(pos, constraints) {
				write_value(strstream, pos->item);
				fprintf(strstream, " ");
			}
			fprintf(strstream, "] got ");
			write_value(strstream, item);
			fprintf(strstream, " instead.\n");
			fclose(strstream);
#else
			msg = strdup("constraint failure");
#endif

			struct vexcept *ex =
			    create_vexcept(msg);
			throw(ex);
		}
	}

	if (item->type == STRINGTYPE && maxlen >= 0) {
		if (strlen(item->value.s) > maxlen) {
			struct vexcept *ex =
				create_vexcept("string exceeds max length of %d",
						maxlen);
			throw(ex);
		}
	}

	// recursively check contents of container types
	if (item->type == LISTTYPE) {
		hashtable_t *listdef = NULL;

		unhash_hashtable(spec, "listdef", &listdef);
		if (listdef) {
			verify_config_list(item->value.l, listdef);
		}
	}
	if (item->type == DICTTYPE) {
		hashtable_t *opendictdef = NULL;
		hashtable_t *dictdef = NULL;

		unhash_hashtable(spec, "opendictdef", &opendictdef);
		unhash_hashtable(spec, "dictdef", &dictdef);

		int ignore_unknown = opendictdef ? 1 : 0;
		if (opendictdef) {
			verify_config_opendict(item->value.h,
					opendictdef, dictdef);
		}
		if (dictdef) {
			verify_config_dictionary(item->value.h, dictdef,
					ignore_unknown);
		}
	}
	if (item->type == INVOTYPE) {
		hashtable_t *invodef = NULL;
		hashtable_t *openinvodef = NULL;
#ifdef UNUSED
		char *implicit_key = NULL;
#endif
		unhash_hashtable(spec, "openinvodef", &openinvodef);
		unhash_hashtable(spec, "invodef", &invodef);

		if (invodef || openinvodef) {
			verify_config_invocation(item->value.v, invodef,
					openinvodef);
		}
	}
	// everything seems ok, go ahead and assign variables
	if (varlist && hashtable_search(spec, "var")) {
		int index;
		unhash_int(spec, "var", &index);
		assign_variable(item, varlist[index]);
	}
	} catch_any {
		if (((struct vexcept *)exception)->next == NULL) {
			struct vexcept *ex =
		    		create_vexcept("(line %d): ", item->lineno);
			ex->next = (struct vexcept *)exception;
			throw(ex);
		} else {
			throw(exception);
		}
	} endtry;

	return 0;
}

static int verify_config_opendict(hashtable_t * opendict,
				  hashtable_t * opendictdef,
				  hashtable_t * dictdef)
{
	hashtable_itr_t itr;

	if (hashtable_count(opendict) == 0) {
		return 0;
	}

	init_iterator(&itr, opendict);
	do {
		char *key = hashtable_iterator_key(&itr);
		// skip keys that are mentioned in the dictdef; they will
		// be checked by verify_config_dictionary
		if (dictdef && hashtable_search(dictdef, key)) {
			continue;
		}

		value_t *val = hashtable_iterator_value(&itr);
		debug_action {
			//printf("Examining open dictionary key %s\n", key);
		}

		try {
			verify_config_item(val, opendictdef);
		} catch_any {
			struct vexcept *ex =
			    create_vexcept("in open dictionary key '%s':\n",
					    key);
			ex->next = (struct vexcept *)exception;
			throw(ex);
		} endtry;
	} while (hashtable_iterator_advance(&itr));
	return 0;
}

static int verify_config_invocation(invocation_t * invo, hashtable_t * invodef,
		hashtable_t *openinvodef)
{
	hashtable_t *spec;
	if (!invodef || unhash_hashtable(invodef, invo->name, &spec) == -ESRCH) {
		// use the open definition if no key-specific one exists
		spec = openinvodef;
	} else {
		dprintf("found invocation spec %s\n", invo->name);
	}

	if (!spec) {
		struct vexcept *ex;
		ex = create_vexcept("invocation of '%s' not defined\n", invo->name);
		throw(ex);
	}

	try {
		verify_config_dictionary(invo->params, spec, 0);
	} catch_any {
		struct vexcept *ex;
		ex = create_vexcept("in invocation of '%s':\n", invo->name);
		ex->next = (struct vexcept *)exception;
		throw(ex);
	} endtry;
	return 0;
}

static int verify_config_list(list_t * list, hashtable_t * listdef)
{
	list_t *pos;
	int ctr = 0;
	list_for_each(pos, list) {
		try {
			verify_config_item(pos->item, listdef);
		} catch_any {
			struct vexcept *ex;
			ex = create_vexcept("at list index %d:\n", ctr);
			ex->next = (struct vexcept *)exception;
			throw(ex);
		} endtry;
		ctr++;
	}
	return 0;
}

static int verify_config_dictionary(hashtable_t * dict, hashtable_t * dictdef,
		int ignore_unknown)
{

	if (hashtable_count(dictdef) == 0) {
		goto emptydictdef;
	}
	hashtable_itr_t itr;
	init_iterator(&itr, dictdef);

	// iterate over all the keys in the dictdef
#if 0
	debug_action {
		dprintf("\nCHECKING DICTIONARY\n");
		prettyprint_hash(dict);
		dprintf("\nAGAINST SPEC\n");
		prettyprint_hash(dictdef);
	}
#endif

	do {
		char *key = hashtable_iterator_key(&itr);

		list_t *exclusive_list = NULL;
		list_t *dependencies = NULL;

		int required = 0;
		hashtable_t *keyspec;
		value_t *cvalue;

		unhash_hashtable(dictdef, key, &keyspec);

		if (unhash_bool(keyspec, "required", &required) == -EINVAL) {
			struct vexcept *ex =
			    create_vexcept
			    ("Spec file problem; required not a bool\n");
			throw(ex);
		}

		if (unhash_list(keyspec, "exclusive", &exclusive_list) ==
		    EINVAL) {
			struct vexcept *ex =
			    create_vexcept
			    ("Spec file problem; exclusive not a list\n");
			throw(ex);
		}

		if (unhash_list(keyspec, "dependencies", &dependencies) ==
		    EINVAL) {
			struct vexcept *ex =
			    create_vexcept
			    ("Spec file problem; dependencies not a list\n");
			throw(ex);
		}

		if (!hashtable_search(dict, key)) {
			if (required) {
				struct vexcept *ex =
				    create_vexcept
				    ("Missing required dictionary key '%s'.\n",
				     key);
				throw(ex);
			}
			if (hashtable_search(keyspec, "default")) {
				value_t *v =
				    copy_value(hashtable_search(keyspec,
								"default"));
				v->toplevel = toplevel;
				hashtable_insert(dict, strdup(key), v);
			} else {
				continue;
			}
		}
		// check to make sure that the keys in the exclusive list
		// aren't also defined
		if (exclusive_list) {
			list_t *pos;
			list_for_each(pos, exclusive_list) {
				char *ename;
				unlist_string(pos, &ename);
				if (hashtable_search(dict, ename)) {
					struct vexcept *ex;
					ex = create_vexcept
					    ("Key '%s' cannot coexist "
					     "with key '%s'.\n", key, ename);
					throw(ex);
				}
			}
		}

		if (dependencies) {
			list_t *pos;
			list_for_each(pos, dependencies) {
				char *dname;
				unlist_string(pos, &dname);
				if (!hashtable_search(dict, dname)) {
					struct vexcept *ex;
					ex = create_vexcept
					    ("Key '%s' requires that '%s' "
					     "also be defined.\n", key, dname);
					throw(ex);
				}
			}
		}
		// looks good, examine the item itself
		cvalue = hashtable_search(dict, key);
		debug_action {
			printf("Examining dictionary key %s.\n", key);
		}
		try {
			verify_config_item(cvalue, keyspec);
		} catch_any {
			struct vexcept *ex;
			ex = create_vexcept("in dictionary key '%s':\n", key);
			ex->next = (struct vexcept *)exception;
			throw(ex);
		} endtry;
	} while (hashtable_iterator_advance(&itr));
emptydictdef:
	if (ignore_unknown || hashtable_count(dict) == 0) {
		return 0;
	}
	init_iterator(&itr, dict);
	do {
		char *key = hashtable_iterator_key(&itr);
		if (!hashtable_search(dictdef, key)) {
			struct vexcept *ex;
			ex = create_vexcept("Unknown dictionary key '%s'.\n", key);
			throw(ex);
		}

	} while (hashtable_iterator_advance(&itr));

	return 0;
}

struct vexcept *verify_config_dict(hashtable_t * config,
		hashtable_t * spec, void **user_varlist)
{
	hashtable_t *specroot;
	unhash_hashtable(spec, "root", &specroot);
	value_t *t = encap_hash(config);
	t->lineno = -2;
	strip_context_lists(t);

	// populate context globals
	varlist = user_varlist;
	toplevel = specroot;

	try {
		verify_config_item(t, specroot);
	} catch_any {
		strip_context_lists(t);
		free(t);
		return (struct vexcept *)exception;
	} endtry;
	strip_context_lists(t);
	free(t);
	return NULL;
}

int check_spec(hashtable_t *spec)
{
	hashtable_t *specspec;

	specspec = parse_config(PREFIX "/share/cspec.cspec");

	if (!specspec) {
		eprintf("Unable to open master specification file. Re-install kusp-base.\n");
		return -1;
	}


	struct vexcept *ex = verify_config_dict(spec, specspec, NULL);
	free_config(specspec);
	if (ex) {
		eprintf("Invalid specification:\n");
		print_vexcept(ex);
		free_vexcept(ex);
		return -1;
	}
	return 0;
}


hashtable_t *parse_spec(char *filename)
{
	hashtable_t *spec;
	spec = parse_config(filename);

	if (!spec) {
		eprintf("Unable to open specification file '%s'.\n",
				filename);
		return NULL;
	}

	if (check_spec(spec)) {
		eprintf("Specification file '%s' not valid.\n", filename);
		free_config(spec);
		return NULL;
	}

	return spec;
}

hashtable_t *parse_spec_string(char *config)
{
	hashtable_t *spec;
	spec = parse_config_string(config);

	if (!spec) {
		eprintf("Unable to parse specification.\n");
		return NULL;
	}

	if (check_spec(spec)) {
		free_config(spec);
		return NULL;
	}

	return spec;

}



hashtable_t *get_config(char *filename, char *specfilename, void **varlist)
{
	hashtable_t *cfg = NULL;
	hashtable_t *spec = NULL;
	struct vexcept *ve = NULL;

	spec = parse_spec(specfilename);
	if (!spec) {
		goto errorout;
	}

	cfg = parse_config(filename);
	if (!cfg) {
		goto errorout;
	}

	ve = verify_config_dict(cfg, spec, varlist);
	if (ve) {
		eprintf("Invalid specification file %s\n", filename);
		print_vexcept(ve);
		free_vexcept(ve);
		goto errorout;
	}

	free_config(spec);
	return cfg;

errorout:
	if (spec) {
		free_config(spec);
	}
	if (cfg) {
		free_config(cfg);
	}
	return NULL;
}

/* Process a configfile stored in a hashtable against a configfile
 * specification (also stored in a hashtable) and modify the variables
 * in the varlist as specified by the configfile.
 *
 * @param cfg		The configfile to parse stored in a hashtable.
 * 			Use the parse_config() functions to parse a raw
 * 			configfile into a hashtable.
 * @param spec		The specification configfile that is used to
 * 			verify cfg. This is also stored in a hashtable.
 * @param varlist	The list of variables the configfile may
 * 			potentially modify.
 */
hashtable_t *process_configfile(hashtable_t *cfg, hashtable_t *spec,
		void **varlist)
{
	if (!spec || !cfg)
		goto errorout;

	struct vexcept *ve = NULL;
	ve = verify_config_dict(cfg, spec, varlist);
	if (ve) {
		print_vexcept(ve);
		free_vexcept(ve);
		goto errorout;
	}

	free_config(spec);
	return cfg;

errorout:
	if (spec) {
		free_config(spec);
	}
	if (cfg) {
		free_config(cfg);
	}
	return NULL;
}


