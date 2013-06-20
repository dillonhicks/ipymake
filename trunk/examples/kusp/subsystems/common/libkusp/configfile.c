/**
 * This is a module for parsing configuration files
 *  
 * @file
 * @author Andrew Boie
 * @addtogroup libkusp libkusp
 */
// for fmemopen()
#define _GNU_SOURCE
#include <stdio.h>

#include <configfile.h>
#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <linkedlist.h>
#include <hashtable.h>
#include <kusp_common.h>
#include <errno.h>



#include "kusp_private.h"

valuetype_t value_type(value_t *val)
{
	return follow(val)->type;
}


long long as_long_long(value_t *v) {
	v = follow(v);
	assert (v->type == LONGTYPE);
	return v->value.g;
}

char *as_string(value_t *v) {
	v = follow(v);
	assert (v->type == STRINGTYPE);
	return v->value.s;
}

struct hashtable *as_hashtable(value_t *v) {
	v = follow(v);
	assert (v->type == DICTTYPE);
	return v->value.h;
}

list_t *as_list(value_t *v) {
	v = follow(v);
	assert (v->type == LISTTYPE);
	return v->value.l;
}

int as_bool(value_t *v) {
	v = follow(v);
	assert (v->type == BOOLTYPE);
	return v->value.i;
}

int as_int(value_t *v) {
	v = follow(v);
	assert (v->type == INTTYPE);
	return v->value.i;
}

/**
 * Encapsulate a long long into a newly allocated value_t, and return
 * the value_t.
 * @param	value	The data to encapsulate
 * @retval	A pointer to a newly allocated value_t
 */
value_t *encap_long(long long value) {
	value_t *v = malloc(sizeof(value_t));
	v->type = LONGTYPE;
	v->value.g = value;
	v->toplevel = NULL;
	v->context = NULL;
	v->lineno = -1;
	return v;
}





/**
 * Encapsulate an integer into a newly allocated value_t, and return
 * the value_t.
 * @param	value	The data to encapsulate
 * @retval	A pointer to a newly allocated value_t
 */

value_t *encap_int(int value) {
	value_t *v = malloc(sizeof(value_t));
	v->type = INTTYPE;
	v->value.i = value;
	v->toplevel = NULL;
	v->context = NULL;
	v->lineno = -1;
	return v;
}

value_t *encap_bool(int value) {
	value_t *v = malloc(sizeof(value_t));
	v->type = BOOLTYPE;
	v->value.i = value;
	v->toplevel = NULL;
	v->context = NULL;
	v->lineno = -1;
	return v;
}

/**
 * Encapsulate a double into a newly allocated value_t, and return
 * the value_t.
 * @param	value	The data to encapsulate
 * @retval	A pointer to a newly allocated value_t
 */

value_t *encap_double(double value) {
	value_t *v = malloc(sizeof(value_t));
	v->type = DOUBLETYPE;
	v->value.d = value;
	v->toplevel = NULL;
	v->context = NULL;
	v->lineno = -1;
	return v;
}
/**
 * Encapsulate a string into a newly allocated value_t, and return
 * the value_t.
 * @param	value	The data to encapsulate
 * @retval	A pointer to a newly allocated value_t
 */

value_t *encap_string_ptr(const char *value) {
	value_t *v = malloc(sizeof(value_t));
	v->type = STRINGTYPE;
	v->value.s = (char *)value;
	v->toplevel = NULL;
	v->context = NULL;
	v->lineno = -1;
	return v;
}
/**
 * Encapsulate a string into a newly allocated value_t, and return
 * the value_t. A copy of the string will be encapsulated, not the
 * string itself
 * @param	value	The data to copy and encapsulate
 * @retval	A pointer to a newly allocated value_t
 */

value_t *encap_string(const char *value) {
	return encap_string_ptr(strdup(value));
}

value_t *encap_reference(char *value) {
	value_t *v = encap_string_ptr(value);
	v->type = REFTYPE;
	v->context = NULL;
	v->lineno = -1;
	return v;
}


/**
 * Encapsulate a hashtable into a newly allocated value_t, and return
 * the value_t.
 * @param	hash	The data to encapsulate
 * @retval	A pointer to a newly allocated value_t
 */
value_t *encap_hash(hashtable_t *hash) {
	value_t *v = malloc(sizeof(value_t));
	v->type = DICTTYPE;
	v->value.h = hash;
	v->toplevel = NULL;
	v->context = NULL;
	v->lineno = -1;
	return v;
}


/**
 * Encapsulate an invocation into a newly allocated value_t, and return
 * the value_t.
 * @param	invoc	The data to encapsulate
 * @retval	A pointer to a newly allocated value_t
 */
value_t *encap_invoc(invocation_t *invoc) {
	value_t *v = malloc(sizeof(value_t));
	v->type = INVOTYPE;
	v->value.v = invoc;
	v->toplevel = NULL;
	v->context = NULL;
	v->lineno = -1;
	return v;
}
/**
 * Encapsulate a linked list into a newly allocated value_t, and return
 * the value_t.
 * @param	list	The data to encapsulate
 * @retval	A pointer to a newly allocated value_t
 */

value_t *encap_list(list_t *list) {
	value_t *v = malloc(sizeof(value_t));
	v->type = LISTTYPE;
	v->value.l = list;
	v->toplevel = NULL;
	v->context = NULL;
	v->lineno = -1;
	return v;
}

/**
 * Given a link in a linkedlist, return the type of the stored value within it.
 * useful if you are iterating over a list's contents and are uncertain
 * about the type of values it contains.
 *
 * @param	list	A pointer to a list entry. This must not be the head of the list.
 * @retval	The type of the stored value, which is one of the valuetype_t enumeration
 */
valuetype_t listitem_type(list_t *list) {
	value_t *v = (value_t*)list->item;
	return v->type;
}

/**
 * Create a new hashtable that accepts string keys
 *
 * @retval A pointer to a new hashtable_t datastructure that uses char* keys
 */
hashtable_t *create_dictionary() {
	return create_hashtable(16, hash_string, string_key_equal);
}


/**
 * Free a config hashtable, recursively diving into it to free stored values.
 * @param config Config to free
 */
void free_config(hashtable_t *config) {
	value_t *v = encap_hash(config);
	free_value(v);
}

/**
 * Free a value_t pointer, as well as any data stored within it. Container types
 * will be recursively freed.
 * @param value	value_t pointer to free
 */
void free_value(value_t *value) {
	list_t *listval, *cur, *temp;
	hashtable_t *hashval;
	hashtable_itr_t *itr;
	value_t *tempv;

	switch(value->type) {
	case INTTYPE:
	case BOOLTYPE:
	case LONGTYPE:
	case DOUBLETYPE:
		break;
	case STRINGTYPE:
	case REFTYPE:
		free(value->value.s);
		break;
	case INVOTYPE:
		free(value->value.v->name);
		tempv = encap_hash(value->value.v->params);
		free_value(tempv);
		break;
	case LISTTYPE:
		listval = value->value.l;
		list_for_each_safe(cur, temp, listval) {
			free_value((value_t*)cur->item);
			free(cur);
		}
		free(listval);
		break;
	case DICTTYPE:
		hashval = value->value.h;
		if (hashtable_count(hashval) > 0) {
			itr = hashtable_iterator(hashval);
			do {
				free_value((value_t*)hashtable_iterator_value(itr));
			} while (hashtable_iterator_advance(itr));
			free(itr);
		}
		hashtable_destroy(hashval, 0);
		break;
	}

	if (value->context) {
		list_free(value->context);
	}

	free(value);
}

static hashtable_t *copy_dictionary(hashtable_t *d)
{
	hashtable_t *c = create_dictionary();
	hashtable_itr_t itr;
	if (hashtable_count(d) == 0) {
		return c;
	}

	init_iterator(&itr, d);
	do {
		char *key = strdup(hashtable_iterator_value(&itr));
		value_t *v = copy_value(hashtable_iterator_value(&itr));
		hashtable_insert(c, key, v);
	} while (hashtable_iterator_advance(&itr));
	return c;
}

value_t *copy_value(value_t *v)
{
	list_t *pos;
	value_t *c = malloc(sizeof (*c));
	memcpy(c, v, sizeof(*v));
	c->toplevel = NULL;
	c->context = NULL;

	switch (v->type) {
	case INTTYPE:
	case BOOLTYPE:
	case LONGTYPE:
	case DOUBLETYPE:
		break;
	case STRINGTYPE:
	case REFTYPE:
		c->value.s = strdup(v->value.s);
		break;
	case INVOTYPE:
		c->value.v = malloc(sizeof(c->value.v));
		c->value.v->name = strdup(v->value.v->name);
		c->value.v->params = copy_dictionary(v->value.v->params);
		break;
	case LISTTYPE:
		c->value.l = create_list();
		list_for_each(pos, v->value.l) {
			list_append(c->value.l, pos->item);
		}
		break;
	case DICTTYPE:
		c->value.h = copy_dictionary(v->value.h);
		break;
	}
	return c;
}

static void fix_dict_toplevel(hashtable_t *d, hashtable_t *toplevel)
{
	hashtable_itr_t itr;
	if (hashtable_count(d) == 0) {
		return;
	}

	init_iterator(&itr, d);
	do {
		fix_toplevel(hashtable_iterator_value(&itr), toplevel);
	} while (hashtable_iterator_advance(&itr));
}

void fix_toplevel(value_t *v, hashtable_t *toplevel)
{
	v->toplevel = toplevel;
	list_t *pos;
	switch (v->type) {
	case INTTYPE:
	case BOOLTYPE:
	case LONGTYPE:
	case DOUBLETYPE:
	case STRINGTYPE:
	case REFTYPE:
		break;
	case INVOTYPE:
		fix_dict_toplevel(v->value.v->params, toplevel);
		break;
	case LISTTYPE:
		list_for_each(pos, v->value.l) {
			fix_toplevel(pos->item, toplevel);
		}
		break;
	case DICTTYPE:
		fix_dict_toplevel(v->value.h, toplevel);
		break;
	}
}

static void strip_dict_context(hashtable_t *d)
{
	hashtable_itr_t itr;
	if (hashtable_count(d) == 0) {
		return;
	}

	init_iterator(&itr, d);
	do {
		strip_context_lists(hashtable_iterator_value(&itr));
	} while (hashtable_iterator_advance(&itr));
}


void strip_context_lists(value_t *v)
{
	list_t *pos;
	if (v->context) {
		list_free(v->context);
		v->context = NULL;
	}

	switch (v->type) {
	case INTTYPE:
	case BOOLTYPE:
	case LONGTYPE:
	case DOUBLETYPE:
	case STRINGTYPE:
	case REFTYPE:
		break;
	case INVOTYPE:
		strip_dict_context(v->value.v->params);
		break;
	case LISTTYPE:
		list_for_each(pos, v->value.l) {
			strip_context_lists(pos->item);
		}
		break;
	case DICTTYPE:
		strip_dict_context(v->value.h);
		break;
	}
}


value_t *follow(const value_t *v)
{
	hashtable_t *toplevel;
	value_t *nv;

	if (v == NULL) {
		return NULL;
	}

	if (v->type != REFTYPE) {
		return (value_t *)v;
	}

	if (v->toplevel == NULL) {
		eprintf("Attempt to follow null reference\n");
		return NULL;
	}

	toplevel = v->toplevel;
	nv = hashtable_search(toplevel, v->value.s);
	if (!nv) {
		eprintf("Invalid reference %s.\n", v->value.s);
		return NULL;
	}
	return follow(nv);
}


/**
 * Extract a stored integer value from a configuration dictionary (i.e. a hashtable
 * that encapsulates all its data in value_t datastructures)
 * @param	h	Configuration hashtable
 * @param	key	String key of stored value
 * @param	val	Pointer to write stored value to
 * @retval	0	Success
 * @retval	-ESRCH	Key not found in dictionary
 * @retval	-EINVAL	Key found, but stored data is of incorrect type
 */
int unhash_int(hashtable_t *h, char *key, int *val)
{
	value_t *value = follow((value_t*)(hashtable_search(h, key)));
	if (value == NULL) {
		return -ESRCH;
	}
	if (value->type != INTTYPE) {
		return -EINVAL;
	}
	*val = value->value.i;
	return 0;
}


int unhash_bool(hashtable_t *h, char *key, int *val)
{
	value_t *value = follow((value_t*)(hashtable_search(h, key)));
	if (value == NULL) {
		return -ESRCH;
	}
	if (value->type != BOOLTYPE) {
		return -EINVAL;
	}
	*val = value->value.i;
	return 0;
}

/**
 * Extract a stored long long value from a configuration dictionary (i.e. a hashtable
 * that encapsulates all its data in value_t datastructures)
 * @param	h	Configuration hashtable
 * @param	key	String key of stored value
 * @param	val	Pointer to write stored value to
 * @retval	0	Success
 * @retval	-ESRCH	Key not found in dictionary
 * @retval	-EINVAL	Key found, but stored data is of incorrect type
 */

int unhash_long(hashtable_t *h, char *key, long long *val)
{
	value_t *value = follow((value_t*)(hashtable_search(h, key)));
	if (value == NULL) {
		return -ESRCH;
	}
	if (value->type != LONGTYPE) {
		return -EINVAL;
	}
	*val = value->value.g;
	return 0;
}
/**
 * Extract a stored double value from a configuration dictionary (i.e. a hashtable
 * that encapsulates all its data in value_t datastructures)
 * @param	h	Configuration hashtable
 * @param	key	String key of stored value
 * @param	val	Pointer to write stored value to
 * @retval	0	Success
 * @retval	-ESRCH	Key not found in dictionary
 * @retval	-EINVAL	Key found, but stored data is of incorrect type
 */

int unhash_double(hashtable_t *h, char *key, double *val)
{
	value_t *value = follow((value_t*)(hashtable_search(h, key)));
	if (value == NULL) {
		return -ESRCH;
	}
	if (value->type != DOUBLETYPE) {
		return -EINVAL;
	}
	*val = value->value.d;
	return 0;
}
/**
 * Extract a stored string value from a configuration dictionary (i.e. a hashtable
 * that encapsulates all its data in value_t datastructures)
 * @param	h	Configuration hashtable
 * @param	key	String key of stored value
 * @param	val	Pointer to write stored value to
 * @retval	0	Success
 * @retval	-ESRCH	Key not found in dictionary
 * @retval	-EINVAL	Key found, but stored data is of incorrect type
 */

int unhash_string(hashtable_t *h, char *key, char **val)
{
	value_t *value = follow((value_t*)(hashtable_search(h, key)));

	if (value == NULL) {
		return -ESRCH;
	}
	if (value->type != STRINGTYPE) {
		return -EINVAL;
	}

	*val = value->value.s;
	return 0;
}
/**
 * Extract a stored hashtable value from a configuration dictionary (i.e. a hashtable
 * that encapsulates all its data in value_t datastructures)
 * @param	h	Configuration hashtable
 * @param	key	String key of stored value
 * @param	val	Pointer to write stored value to
 * @retval	0	Success
 * @retval	-ESRCH	Key not found in dictionary
 * @retval	-EINVAL	Key found, but stored data is of incorrect type
 */

int unhash_hashtable(hashtable_t *h, char *key, hashtable_t **val)
{
	value_t *value = follow((value_t*)(hashtable_search(h, key)));

	if (value == NULL) {
		return -ESRCH;
	}
	if (value->type != DICTTYPE) {
		return -EINVAL;
	}

	*val = value->value.h;
	return 0;
}
/**
 * Extract a stored linked list value from a configuration dictionary (i.e. a hashtable
 * that encapsulates all its data in value_t datastructures)
 * @param	h	Configuration hashtable
 * @param	key	String key of stored value
 * @param	val	Pointer to write stored value to
 * @retval	0	Success
 * @retval	-ESRCH	Key not found in dictionary
 * @retval	-EINVAL	Key found, but stored data is of incorrect type
 */

int unhash_list(hashtable_t *h, char *key, list_t **val)
{
	value_t *value = follow((value_t*)(hashtable_search(h, key)));

	if (value == NULL) {
		return -ESRCH;
	}
	if (value->type != LISTTYPE) {
		return -EINVAL;
	}

	*val = value->value.l;
	return 0;
}
/**
 * Extract a stored invocation value from a configuration dictionary (i.e. a hashtable
 * that encapsulates all its data in value_t datastructures)
 * @param	h	Configuration hashtable
 * @param	key	String key of stored value
 * @param	val	Pointer to write stored value to
 * @retval	0	Success
 * @retval	-ESRCH	Key not found in dictionary
 * @retval	-EINVAL	Key found, but stored data is of incorrect type
 */

int unhash_invoc(hashtable_t *h, char *key, invocation_t **val) {
	value_t *value = follow((value_t*)(hashtable_search(h, key)));

	if (value == NULL) {
		return -ESRCH;
	}
	if (value->type != INVOTYPE) {
		return -EINVAL;
	}

	*val = value->value.v;

	return 0;
}

/**
 * Determine the datatype for a value stored with a given key.
 *
 * @param hashtable to examine
 * @return the valuetype of the stored data. if the key does not exist,
 * the result is undefined. Check your keys first!
 */
valuetype_t hashtable_get_type(hashtable_t *h, char *key)
{
	value_t *value = follow((value_t*)(hashtable_search(h, key)));
	if (value == NULL) {
		eprintf("Key %s not in hashtable\n", key);
		return 0;
	}
	return value->type;
}

/**
 * Extract a stored invocation value at the current position in a configuration
 * linked list (i.e. a linked list that wraps its values in value_t structures).
 * This function is most useful inside a list_for_each loop.
 * @param	list	A link in a linked list. Must not be the head.
 * @param	val	Pointer to write stored data to
 * @retval	0	Success
 * @retval	-ESRCH	You called this function on a list head pointer, which
 * doesn't store any data
 * @retval	-EINVAL	Stored data is of incorrect type.
 */
int unlist_invoc(list_t *list, invocation_t **val)
{
	value_t *value = follow((value_t*)list->item);

	if (value == NULL) {
		bprintf("Unlist operation performed on list head pointer.");
		return -ESRCH;
	}
	if (value->type != INVOTYPE) {
		return -EINVAL;
	}
	*val = value->value.v;

	return 0;
}
/**
 * Extract a stored integer value at the current position in a configuration
 * linked list (i.e. a linked list that wraps its values in value_t structures).
 * This function is most useful inside a list_for_each loop.
 * @param	list	A link in a linked list. Must not be the head.
 * @param	val	Pointer to write stored data to
 * @retval	0	Success
 * @retval	-ESRCH	You called this function on a list head pointer, which
 * doesn't store any data
 * @retval	-EINVAL	Stored data is of incorrect type.
 */

int unlist_int(list_t *list, int *val)
{
	value_t *value = follow((value_t*)list->item);

	if (value == NULL) {
		bprintf("Unlist operation performed on list head pointer.");
		return -ESRCH;
	}
	if (value->type != INTTYPE) {
		return -EINVAL;
	}

	*val = value->value.i;
	return 0;
}

int unlist_bool(list_t *list, int *val)
{
	value_t *value = follow((value_t*)list->item);

	if (value == NULL) {
		bprintf("Unlist operation performed on list head pointer.");
		return -ESRCH;
	}
	if (value->type != BOOLTYPE) {
		return -EINVAL;
	}

	*val = value->value.i;
	return 0;
}



/**
 * Extract a stored long value at the current position in a configuration
 * linked list (i.e. a linked list that wraps its values in value_t structures).
 * This function is most useful inside a list_for_each loop.
 * @param	list	A link in a linked list. Must not be the head.
 * @param	val	Pointer to write stored data to
 * @retval	0	Success
 * @retval	-ESRCH	You called this function on a list head pointer, which
 * doesn't store any data
 * @retval	-EINVAL	Stored data is of incorrect type.
 */

int unlist_long(list_t *list, long long *val)
{
	value_t *value = follow((value_t*)list->item);

	if (value == NULL) {
		bprintf("Unlist operation performed on list head pointer.");
		return -ESRCH;
	}
	if (value->type != LONGTYPE) {
		return -EINVAL;
	}

	*val = value->value.g;
	return 0;
}
/**
 * Extract a stored double value at the current position in a configuration
 * linked list (i.e. a linked list that wraps its values in value_t structures).
 * This function is most useful inside a list_for_each loop.
 * @param	list	A link in a linked list. Must not be the head.
 * @param	val	Pointer to write stored data to
 * @retval	0	Success
 * @retval	-ESRCH	You called this function on a list head pointer, which
 * doesn't store any data
 * @retval	-EINVAL	Stored data is of incorrect type.
 */

int unlist_double(list_t *list, double *val)
{
	value_t *value = follow((value_t*)list->item);

	if (value == NULL) {
		bprintf("Unlist operation performed on list head pointer.");
		return -ESRCH;
	}
	if (value->type != DOUBLETYPE) {
		return -EINVAL;
	}

	*val = value->value.d;
	return 0;
}

/**
 * Extract a stored string value at the current position in a configuration
 * linked list (i.e. a linked list that wraps its values in value_t structures).
 * This function is most useful inside a list_for_each loop.
 * @param	list	A link in a linked list. Must not be the head.
 * @param	val	Pointer to write stored data to
 * @retval	0	Success
 * @retval	-ESRCH	You called this function on a list head pointer, which
 * doesn't store any data
 * @retval	-EINVAL	Stored data is of incorrect type.
 */
int unlist_string(list_t *list, char **val)
{
	value_t *value = follow((value_t*)(list->item));

	if (value == NULL) {
		bprintf("Unlist operation performed on list head pointer.");
		return -ESRCH;
	}
	if (value->type != STRINGTYPE) {
		return -EINVAL;
	}

	*val = value->value.s;
	return 0;
}

/**
 * Extract a stored hashtable value at the current position in a configuration
 * linked list (i.e. a linked list that wraps its values in value_t structures).
 * This function is most useful inside a list_for_each loop.
 * @param	list	A link in a linked list. Must not be the head.
 * @param	val	Pointer to write stored data to
 * @retval	0	Success
 * @retval	-ESRCH	You called this function on a list head pointer, which
 * doesn't store any data
 * @retval	-EINVAL	Stored data is of incorrect type.
 */
int unlist_hashtable(list_t *list, hashtable_t **val)
{
	value_t *value = follow((value_t*)list->item);

	if (value == NULL) {
		bprintf("Unlist operation performed on list head pointer.");
		return -ESRCH;
	}
	if (value->type != DICTTYPE) {
		return -EINVAL;
	}

	*val = value->value.h;
	return 0;
}

/**
 * Extract a stored linked list value at the current position in a configuration
 * linked list (i.e. a linked list that wraps its values in value_t structures).
 * This function is most useful inside a list_for_each loop.
 * @param	list	A link in a linked list. Must not be the head.
 * @param	val	Pointer to write stored data to
 * @retval	0	Success
 * @retval	-ESRCH	You called this function on a list head pointer, which
 * doesn't store any data
 * @retval	-EINVAL	Stored data is of incorrect type.
 */

int unlist_list(list_t *list, list_t **val)
{
	value_t *value = follow((value_t*)list->item);

	if (value == NULL) {
		bprintf("Unlist operation performed on list head pointer.");
		return -ESRCH;
	}
	if (value->type != LISTTYPE) {
		return -EINVAL;
	}

	*val = value->value.l;
	return 0;
}



static int __print_value(FILE *fd, value_t *value, int indent) {
	int i;
	struct list_s *templist;
	hashtable_itr_t *hi;
	hashtable_t *temphash;
	char *tempkey;
	value_t *tempval;
	char *tempstr;
	int sz = 0;

	switch (value->type) {
	case INTTYPE:
		sz += fprintf(fd, "%d",  value->value.i);
		break;
	case DOUBLETYPE:
		sz += fprintf(fd, "%f", value->value.d);
		break;
	case LONGTYPE:
		sz += fprintf(fd, "%lldL", value->value.g);
		break;
	case REFTYPE:
		sz += fprintf(fd, "@");
	case STRINGTYPE:
		tempstr = value->value.s;
		sz += fprintf(fd, "\"");
		while (*tempstr) {
			// FIXME: is this exhaustive?
			switch (*tempstr) {
			case '"':
				sz += fprintf(fd, "\\\"");
				break;
			case '\t':
				sz += fprintf(fd, "\\t");
				break;
			case '\n':
				sz += fprintf(fd, "\\n");
				break;
			case '\r':
				sz += fprintf(fd, "\\r");
				break;
			case '\b':
				sz += fprintf(fd, "\\b");
				break;
			case '\f':
				sz += fprintf(fd, "\\f");
				break;
			default:
				sz += fprintf(fd, "%c", *tempstr);
			}
			tempstr++;
		}
		sz += fprintf(fd, "\"");
		break;
	case DICTTYPE:
		temphash = value->value.h;
		if (hashtable_count(temphash) == 0) {
			sz += fprintf(fd, "{}");
			break;
		}
		sz += fprintf(fd, "{\n");

		hi = hashtable_iterator(temphash);
		do {
			tempkey = (char*)(hashtable_iterator_key(hi));
			tempval = (value_t*)(hashtable_iterator_value(hi));
			for (i=0; i <= indent; i++) {
				sz += fprintf(fd, "\t");
			}
			sz += fprintf(fd, "\"%s\" = ", tempkey);
			sz += __print_value(fd, tempval, indent+1);
			sz += fprintf(fd, "\n");
		} while (hashtable_iterator_advance(hi));
		for (i=0; i < indent; i++) {
			sz += fprintf(fd, "\t");
		}
		sz += fprintf(fd, "}");
		free(hi);
		break;
	case LISTTYPE:
		if (list_size(value->value.l) == 0) {
			sz += fprintf(fd, "[]");
			break;
		}
		sz += fprintf(fd, "[\n");
		list_for_each(templist,  value->value.l) {
			tempval = (value_t*)(templist->item);
			for (i=0; i <= indent; i++) {
				sz += fprintf(fd, "\t");
			}
			sz += __print_value(fd, tempval, indent+1);
			sz += fprintf(fd, "\n");
		}
		for (i=0; i < indent; i++) {
			sz += fprintf(fd, "\t");
		}
		sz += fprintf(fd, "]");
		break;
	case INVOTYPE:
		tempkey = value->value.v->name;
		temphash = value->value.v->params;
		if (hashtable_count(temphash) == 0) {
			sz += fprintf(fd, "\"%s\" ()", tempkey);
			break;
		}

		sz += fprintf(fd, "\"%s\" (\n", tempkey);
		hi = hashtable_iterator(temphash);
		do {
			tempkey = (char*)(hashtable_iterator_key(hi));
			tempval = (value_t*)(hashtable_iterator_value(hi));
			for (i=0; i <= indent; i++) {
				sz += fprintf(fd, "\t");
			}
			sz += fprintf(fd, "\"%s\" = ", tempkey);
			sz += __print_value(fd, tempval, indent+1);
			sz += fprintf(fd, "\n");
		} while (hashtable_iterator_advance(hi));
		for (i=0; i < indent; i++) {
			sz += fprintf(fd, "\t");
		}
		sz += fprintf(fd, ")");
		free(hi);
		break;
	case BOOLTYPE:
		if (value->value.i) {
			sz += fprintf(fd, "true");
		} else {
			sz += fprintf(fd, "false");
		}

	}
	return sz;
}

/**
 * Write a string representation of a value_t to an output stream.
 * See the documentation of prettyprint_value for more information.
 * @param	fd	File object to write prettyprinted value
 * @param	value	value_t to prettyprint
 */
void write_value(FILE *fd, value_t *value) {
	__print_value(fd, value, 0);
}

/**
 * Write a nicely formatted, human-readable representation of a value_t
 * to the console. This function is most useful if you are uncertain of the
 * structure of a value. Container types (invocations, lists, hashtables) are
 * recursively processed and indented for clarity. The output conforms to
 * the configfile language and can be read by the parser.
 * @param	value	value_t to prettyprint
 */
void prettyprint_value(value_t *value) {
	__print_value(stdout, value, 0);
}

/**
 * Prettyprint a configuration dictionary to the console. See
 * prettyprint_value for more details.
 * @param	hash	Configuration dictionary to prettyprint
 */
void prettyprint_hash(hashtable_t *hash) {
	value_t v;
	v.value.h = hash;
	v.type = DICTTYPE;
	prettyprint_value(&v);
}

/**
 * Prettyprint a configuration linked list to the console. See
 * prettyprint_value for more details.
 * @param	list	Configuration linked list to prettyprint
 */
void prettyprint_list(list_t *list) {
	value_t v;
	v.value.l = list;
	v.type = LISTTYPE;
	prettyprint_value(&v);
}

/**
 * Compare two value_t's for ordering and equality. Values of different
 * datatypes are arbitraily ordered by type. This comparison function
 * is patterned after strcmp.
 *
 * @retval 0 The values are equal
 * @retval positive v1 is greater than v2
 * @retval negative v1 is less than v2
 */
int valcmp(const value_t *v1, const value_t *v2)
{
	v1 = follow(v1);
	v2 = follow(v2);

	if (v1->type != v2->type) {
		// impose arbitrary but consistent ordering among different types
		return v1->type - v2->type;
	}

	switch(v1->type) {
	case LISTTYPE:
		if (v1->value.l > v2->value.l) {
			return 1;
		}
		if (v1->value.l < v2->value.l) {
			return -1;
		}
		return 0;
	case INVOTYPE:
		if (v1->value.v > v2->value.v) {
			return 1;
		}
		if (v1->value.v < v2->value.v) {
			return -1;
		}
		return 0;
	case DICTTYPE:
		if (v1->value.h > v2->value.h) {
			return 1;
		}
		if (v1->value.h < v2->value.h) {
			return -1;
		}
		return 0;
	case BOOLTYPE:
	case INTTYPE:
		if (v1->value.i > v2->value.i) {
			return 1;
		}
		if (v1->value.i < v2->value.i) {
			return -1;
		}
		return 0;
	case DOUBLETYPE:
		if (v1->value.d > v2->value.d) {
			return 1;
		}
		if (v1->value.d < v2->value.d) {
			return -1;
		}
		return 0;
	case LONGTYPE:
		if (v1->value.g > v2->value.g) {
			return 1;
		}
		if (v1->value.g < v2->value.g) {
			return -1;
		}
		return 0;
	case REFTYPE:
	case STRINGTYPE:
		return strcmp(v1->value.s, v2->value.s);
	}

	/* shouldn't get here */
	return 0;
}



/**
 * Determine membership inside a list. Runs in linear time wrt size of list.
 *
 * @param list list to search
 * @param v value to search for.
 */
int list_membership_test(list_t *head, const value_t *v)
{
	list_t *cur;
	list_for_each(cur, head) {
		value_t *v2 = (value_t *)(cur->item);
		if (valcmp(v, v2) == 0) {
			return 1;
		}
	}
	return 0;
}

int string_inside_list(list_t *head, char *string)
{
	value_t v;
	v.type = STRINGTYPE;
	v.value.s = string;
	return list_membership_test(head, &v);
}

/**
 * Write a configuration file to disk, in a format such that it can be
 * read by the parser. See prettyprint_value for more details.
 * Note that all preprocessor directives in the original file will
 * be lost.
 *
 * @param fd		FILE object to write to
 * @param config	Configuration dictionary to write
 */
int write_config(FILE *fd, hashtable_t *config) {
	int sz = 0;

	if (hashtable_count(config) == 0) {
		return sz;
	}

	hashtable_itr_t hi, bi;

	init_iterator(&hi, config);
	do {
		char *key = (char*)(hashtable_iterator_key(&hi));

		sz += fprintf(fd, "<%s>\n", key);
		hashtable_t *block = NULL;
		unhash_hashtable(config, key, &block);

		if (hashtable_count(block) == 0) {
			continue;
		}

		init_iterator(&bi, block);
		do {
			char *bkey = hashtable_iterator_key(&bi);
			value_t *value = hashtable_iterator_value(&bi);

			sz += fprintf(fd, "%s = ", bkey);
			sz += __print_value(fd, value, 0);
			sz += fprintf(fd, "\n");
		} while (hashtable_iterator_advance(&bi));

		sz += fprintf(fd, "\n");
	} while (hashtable_iterator_advance(&hi));

	return sz;
}


void config_to_string(hashtable_t *config, size_t *size, char **ptr)
{
#ifdef HAVE_OPEN_MEMSTREAM
	FILE *f = open_memstream(ptr, size);

	write_config(f, config);

	fclose(f);
#else
	FILE *f = tmpfile();
	*size = write_config(f, config);
	*ptr = malloc(*size + 1);
	rewind(f);
	fread(*ptr, *size, sizeof(char), f);
	fclose(f);
#endif
}

/**
 * Given a string filename, open it up, parse its contents, and return
 * a pointer to the configuration dictionary generated. If the file
 * cannot be opened or cannot be parsed, NULL will be returned.
 * @param	filename	The file to open
 * @retval	The generated configuration dictionary, or NULL if there was a problem.
 */
hashtable_t *parse_config(char *filename) {
	hashtable_t *retval;
	FILE *cfile = fopen(filename, "r");
	if (cfile == NULL) {
		eprintf("unable to open config file '%s': ", filename);
		perror("fopen");
		return NULL;
	}
	retval = parse_config_file(cfile);
	fclose(cfile);
	return retval;
}

// XXX: fmemopen is not portable
hashtable_t *parse_config_string(char *config) {
	hashtable_t *retval;
#ifdef HAVE_FMEMOPEN
	FILE *cfile = fmemopen(config, strlen(config), "r");
	if (cfile == NULL) {
		kusp_perror("fmemopen");
		return NULL;
	}
#else
	FILE *cfile = tmpfile();
	fwrite(config, strlen(config), sizeof(char), cfile);
	rewind(cfile);
#endif
	retval = parse_config_file(cfile);
	fclose(cfile);
	return retval;
}



/**
 * Given a valuetype_t, return a string representation of it. Used by
 * various prettyprinting and configuration help functions.
 * @param v	A value type enumeration
 * @retval	A string representation.
 */
char *get_type_name(valuetype_t v) {
	switch (v) {
	case INTTYPE:
		return "integer";
	case DICTTYPE:
		return "dictionary";
	case STRINGTYPE:
		return "string";
	case LISTTYPE:
		return "list";
	case DOUBLETYPE:
		return "real";
	case INVOTYPE:
		return "invocation";
	case BOOLTYPE:
		return "boolean";
	case LONGTYPE:
		return "long";
	case REFTYPE:
		return "reference";
	}
	return "NULL (shouldn't see me)";
}


