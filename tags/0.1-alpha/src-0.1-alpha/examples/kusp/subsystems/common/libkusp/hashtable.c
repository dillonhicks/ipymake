/**
 * @file hashtable.c
 *
 * Hashtable implementation
 *
 * Example of use:
 *
 * @verbatim
       struct hashtable  *h;
       struct some_key   *k;
       struct some_value *v;

       static unsigned int         hash_from_key_fn( void *k );
       static int                  keys_equal_fn ( void *key1, void *key2 );

       h = create_hashtable(16, hash_from_key_fn, keys_equal_fn);
       k = (struct some_key *)     malloc(sizeof(struct some_key));
       v = (struct some_value *)   malloc(sizeof(struct some_value));

       (initialise k and v to suitable values)

       if (! hashtable_insert(h,k,v) )
       {     exit(-1);               }

       if (NULL == (found = hashtable_search(h,k) ))
       {    printf("not found!");                  }

       if (NULL == (found = hashtable_remove(h,k) ))
       {    printf("Not found\n");                 }
 @endverbatim
 *
 * Macros may be used to define type-safe(r) hashtable access functions, with
 * methods specialized to take known key and value types as parameters.
 *
 * Example:
 *
 * Insert this at the start of your file:
 *
 * @verbatim
  DEFINE_HASHTABLE_INSERT(insert_some, struct some_key, struct some_value);
  DEFINE_HASHTABLE_SEARCH(search_some, struct some_key, struct some_value);
  DEFINE_HASHTABLE_REMOVE(remove_some, struct some_key, struct some_value);
  @endverbatim
 *
 * This defines the functions 'insert_some', 'search_some' and 'remove_some'.
 * These operate just like hashtable_insert etc., with the same parameters,
 * but their function signatures have 'struct some_key *' rather than
 * 'void *', and hence can generate compile time errors if your program is
 * supplying incorrect data as a key (and similarly for value).
 *
 * Note that the hash and key equality functions passed to create_hashtable
 * still take 'void *' parameters instead of 'some key *'. This shouldn't be
 * a difficult issue as they're only defined and passed once, and the other
 * functions will ensure that only valid keys are supplied to them.
 *
 * The cost for this checking is increased code size and runtime overhead;
 * if performance is important, it may be worth switching back to the
 * unsafe methods once your program has been debugged with the safe methods.
 * This just requires switching to some simple alternative defines - eg:
 * #define insert_some hashtable_insert
 */

/* Copyright (C) 2004 Christopher Clark <firstname.lastname@cl.cam.ac.uk>
 *
 * Additional modifications by Andrew Boie
 * */

#include "hashtable.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <kusp_common.h>

unsigned int hash(struct hashtable *h, void *k);

static inline unsigned int
indexFor(unsigned int tablelength, unsigned int hashvalue)
{
	return (hashvalue % tablelength);
};

#define freekey(X) free(X)

/*
Credit for primes table: Aaron Krowne
 http://br.endernet.org/~akrowne/
 http://planetmath.org/encyclopedia/GoodHashTablePrimes.html
*/
static const unsigned int primes[] = {
	53, 97, 193, 389,
	769, 1543, 3079, 6151,
	12289, 24593, 49157, 98317,
	196613, 393241, 786433, 1572869,
	3145739, 6291469, 12582917, 25165843,
	50331653, 100663319, 201326611, 402653189,
	805306457, 1610612741
};
const unsigned int prime_table_length = sizeof(primes) / sizeof(primes[0]);
const float max_load_factor = 0.65;

/*****************************************************************************
 * create_hashtable

 * @name                    create_hashtable
 * @param   minsize         minimum initial size of hashtable
 * @param   hashfunction    function for hashing keys
 * @param   key_eq_fn       function for determining key equality
 * @return                  newly created hashtable or NULL on failure
 */

struct hashtable *create_hashtable(unsigned int minsize,
				   unsigned int (*hashf) (void *),
				   int (*eqf) (void *, void *))
{
	struct hashtable *h;
	unsigned int pindex, size = primes[0];
	/* Check requested hashtable isn't too large */
	if (minsize > (1u << 30))
		return NULL;
	/* Enforce size as prime */
	for (pindex = 0; pindex < prime_table_length; pindex++) {
		if (primes[pindex] > minsize) {
			size = primes[pindex];
			break;
		}
	}
	h = (struct hashtable *)malloc(sizeof(struct hashtable));
	if (NULL == h)
		return NULL;	/*oom */
	h->table = (struct entry **)malloc(sizeof(struct entry *) * size);
	if (NULL == h->table) {
		free(h);
		return NULL;
	}			/*oom */
	memset(h->table, 0, size * sizeof(struct entry *));
	h->tablelength = size;
	h->primeindex = pindex;
	h->entrycount = 0;
	h->hashfn = hashf;
	h->eqfn = eqf;
	h->loadlimit = (unsigned int)ceil(size * max_load_factor);
	return h;
}

/*****************************************************************************/
unsigned int hash(struct hashtable *h, void *k)
{
	/* Aim to protect against poor hash functions by adding logic here
	 * - logic taken from java 1.4 hashtable source */
	unsigned int i = h->hashfn(k);
	i += ~(i << 9);
	i ^= ((i >> 14) | (i << 18));	/* >>> */
	i += (i << 4);
	i ^= ((i >> 10) | (i << 22));	/* >>> */
	return i;
}

/*****************************************************************************/
static int hashtable_expand(struct hashtable *h)
{
	/* Double the size of the table to accomodate more entries */
	struct entry **newtable;
	struct entry *e;
	struct entry **pE;
	unsigned int newsize, i, index;
	/* Check we're not hitting max capacity */
	if (h->primeindex == (prime_table_length - 1))
		return 0;
	newsize = primes[++(h->primeindex)];

	newtable = (struct entry **)malloc(sizeof(struct entry *) * newsize);
	if (NULL != newtable) {
		memset(newtable, 0, newsize * sizeof(struct entry *));
		/* This algorithm is not 'stable'. ie. it reverses the list
		 * when it transfers entries between the tables */
		for (i = 0; i < h->tablelength; i++) {
			while (NULL != (e = h->table[i])) {
				h->table[i] = e->next;
				index = indexFor(newsize, e->h);
				e->next = newtable[index];
				newtable[index] = e;
			}
		}
		free(h->table);
		h->table = newtable;
	}
	/* Plan B: realloc instead */
	else {
		newtable = (struct entry **)
		    realloc(h->table, newsize * sizeof(struct entry *));
		if (NULL == newtable) {
			(h->primeindex)--;
			return 0;
		}
		h->table = newtable;
		memset(newtable[h->tablelength], 0, newsize - h->tablelength);
		for (i = 0; i < h->tablelength; i++) {
			for (pE = &(newtable[i]), e = *pE; e != NULL; e = *pE) {
				index = indexFor(newsize, e->h);
				if (index == i) {
					pE = &(e->next);
				} else {
					*pE = e->next;
					e->next = newtable[index];
					newtable[index] = e;
				}
			}
		}
	}
	h->tablelength = newsize;
	h->loadlimit = (unsigned int)ceil(newsize * max_load_factor);
	return -1;
}

/*****************************************************************************
 * Return the number of items stored in the hashtable. Runs in constant time.
 *
 * @name        hashtable_count
 * @param   h   the hashtable
 * @return      the number of items stored in the hashtable
 */
unsigned int hashtable_count(struct hashtable *h)
{
	return h->entrycount;
}

/**
 * This function merges two hashtables. These tables must both use the
 * same hash and equality functions. Each (key,value) pair is removed from
 * the source hashtable, and inserted into the target hashtable. The source
 * hashtable is then freed.
 *
 * A third hashtable 'shadow' is created in this process. If any of the keys
 * in the source hashtable exist in the target hashtable, then the overwritten
 * (key,value) pairs in the target hashtable are inserted into the shadow
 * hashtable. This is done so that the user will be able to know about any
 * collisions, or at least properly free any overwritten values.
 *
 * @param target The hashtable to write data to; once the function completes,
 * the target hashtable will be the merged hashtable.
 * @param source The hashtable to read (key,value) pairs that are merged into
 * the target hashtable. This hashtable will be destroyed by this operation.
 * @return A third hashtable which will contain any values in the target hashtable
 * that were overwritten by the source. If no collisions occurred, this hashtable
 * will be empty.
 * @retval NULL The source and target hashtables had different hash or
 * equality functions.
 */
hashtable_t *hashtable_merge(hashtable_t * target, hashtable_t * source)
{
	if (source->hashfn != target->hashfn || source->eqfn != target->eqfn) {
		bprintf("Attempted to merge incompatible hashtables.");
		return NULL;
	}

	hashtable_t *shadow = create_hashtable(4, source->hashfn, source->eqfn);

	if (hashtable_count(source) == 0) {
		// source is empty, nothing to do.
		return shadow;
	}

	hashtable_itr_t itr;
	init_iterator(&itr, source);
	do {
		void *key = hashtable_iterator_key(&itr);
		void *val = hashtable_iterator_value(&itr);

		void *shadowedval = hashtable_search(target, key);
		if (shadowedval) {
			hashtable_insert(shadow, strdup(key), shadowedval);
			hashtable_remove(target, key);
		}
		hashtable_insert(target, key, val);
	} while (hashtable_iterator_advance(&itr));

	free(source);

	return shadow;
}

/*****************************************************************************
 * hashtable_insert

 * @name        hashtable_insert
 * @param   h   the hashtable to insert into
 * @param   k   the key - hashtable claims ownership and will free on removal
 * @param   v   the value - does not claim ownership
 * @return      non-zero for successful insertion
 *
 * This function will cause the table to expand if the insertion would take
 * the ratio of entries to table size over the maximum load factor.
 *
 * This function does not check for repeated insertions with a duplicate key.
 * The value returned when using a duplicate key is undefined -- when
 * the hashtable changes size, the order of retrieval of duplicate key
 * entries is reversed.
 * If in doubt, remove before insert.
 */
int hashtable_insert(struct hashtable *h, void *k, void *v)
{
	/* This method allows duplicate keys - but they shouldn't be used */
	unsigned int index;
	struct entry *e;
	if (++(h->entrycount) > h->loadlimit) {
		/* Ignore the return value. If expand fails, we should
		 * still try cramming just this value into the existing table
		 * -- we may not have memory for a larger table, but one more
		 * element may be ok. Next time we insert, we'll try expanding again.*/
		hashtable_expand(h);
	}
	e = (struct entry *)malloc(sizeof(struct entry));
	if (NULL == e) {
		--(h->entrycount);
		return 0;
	}			/*oom */
	e->h = hash(h, k);
	index = indexFor(h->tablelength, e->h);
	e->k = k;
	e->v = v;
	e->next = h->table[index];
	h->table[index] = e;
	return -1;
}

/*****************************************************************************
 * hashtable_search

 * @name        hashtable_search
 * @param   h   the hashtable to search
 * @param   k   the key to search for  - does not claim ownership
 * @return      the value associated with the key, or NULL if none found
 */
void *hashtable_search(struct hashtable *h, void *k)
{
	struct entry *e;
	unsigned int hashvalue, index;
	hashvalue = hash(h, k);
	index = indexFor(h->tablelength, hashvalue);
	e = h->table[index];
	while (NULL != e) {
		/* Check hash value to short circuit heavier comparison */
		if ((hashvalue == e->h) && (h->eqfn(k, e->k)))
			return e->v;
		e = e->next;
	}
	return NULL;
}

/*****************************************************************************
 * hashtable_remove

 * @name        hashtable_remove
 * @param   h   the hashtable to remove the item from
 * @param   k   the key to search for  - does not claim ownership
 * @return      the value associated with the key, or NULL if none found
 */
void *				/* returns value associated with key */
hashtable_remove(struct hashtable *h, void *k)
{
	/* TODO: consider compacting the table when the load factor drops enough,
	 *       or provide a 'compact' method. */

	struct entry *e;
	struct entry **pE;
	void *v;
	unsigned int hashvalue, index;

	hashvalue = hash(h, k);
	index = indexFor(h->tablelength, hash(h, k));
	pE = &(h->table[index]);
	e = *pE;
	while (NULL != e) {
		/* Check hash value to short circuit heavier comparison */
		if ((hashvalue == e->h) && (h->eqfn(k, e->k))) {
			*pE = e->next;
			h->entrycount--;
			v = e->v;
			freekey(e->k);
			free(e);
			return v;
		}
		pE = &(e->next);
		e = e->next;
	}
	return NULL;
}

/*****************************************************************************
 * hashtable_destroy

 * @name        hashtable_destroy
 * @param   h   the hashtable
 * @param       free_values     whether to call 'free' on the remaining values
 */
void hashtable_destroy(struct hashtable *h, int free_values)
{
	unsigned int i;
	struct entry *e, *f;
	struct entry **table = h->table;
	if (free_values) {
		for (i = 0; i < h->tablelength; i++) {
			e = table[i];
			while (NULL != e) {
				f = e;
				e = e->next;
				freekey(f->k);
				free(f->v);
				free(f);
			}
		}
	} else {
		for (i = 0; i < h->tablelength; i++) {
			e = table[i];
			while (NULL != e) {
				f = e;
				e = e->next;
				freekey(f->k);
				free(f);
			}
		}
	}
	free(h->table);
	free(h);
}

/**
 * Allocate and initialize a hashtable iterator. This may be used
 * to iterate over all the keys and values stored in the hashtable.
 * Bad things happen if the hashtable is empty; you must check to
 * ensure the hashtable has at least one mapping inside it.
 *
 * @param h Hashtable to generate iterator from
 * @return A pointer to a hashtable iterator; it is your responsibility
 * to free when once you are done.
 *
 **/

struct hashtable_itr *hashtable_iterator(struct hashtable *h)
{
	struct hashtable_itr *itr = (struct hashtable_itr *)
	    malloc(sizeof(struct hashtable_itr));
	if (NULL == itr)
		return NULL;

	init_iterator(itr, h);

	return itr;
}

/**
 * This is very similar to hashtable_iterator, but no memory
 * allocation is done; instead a pointer to an uninitialized
 * hashtable_itr_t is passed in. See hashtable_iterator for
 * more details.
 *
 * @param itr Pointer to uninitialized hashtable_itr_t
 * @param h Hashtable to generate iterator from
 */
void init_iterator(hashtable_itr_t * itr, hashtable_t * h)
{
	unsigned int i, tablelength;

	itr->h = h;
	itr->e = NULL;
	itr->parent = NULL;
	tablelength = h->tablelength;
	itr->index = tablelength;
	if (0 == h->entrycount)
		return;

	for (i = 0; i < tablelength; i++) {
		if (NULL != h->table[i]) {
			itr->e = h->table[i];
			itr->index = i;
			break;
		}
	}

}

/** keyp and valuep MUST be a pointer to a pointer. The signature
 * is only void* to prevent warnings. */
int hashtable_iterate(struct  hashtable *h, hashtable_itr_t *pos,
		void *keyp, void *valuep)
{
	void **key = (void **)keyp;
	void **value = (void **)valuep;


	if (!h->entrycount) {
		return 0;
	}

	if (pos->h == NULL) {
		init_iterator(pos, h);
	} else {
		if (!hashtable_iterator_advance(pos)) {
			return 0;
		}
	}

	*key = hashtable_iterator_key(pos);
	*value = hashtable_iterator_value(pos);
	return -1;
}

/**
 * @param i hashtable iterator
 * @return the key of the (key,value) pair at the current position
 */
void *hashtable_iterator_key(struct hashtable_itr *i)
{
	return i->e->k;
}

/**
 * @param i hashtable iterator
 * @return the key of the (key,value) pair at the current position
 */
void *hashtable_iterator_value(struct hashtable_itr *i)
{
	return i->e->v;
}

/**
 * advance the iterator to the next element. returns zero
 * if advanced to end of table. this function is normally used
 * in the condition of a do-while loop.
 *
 * @param itr hashtable iterator
 * @retval 0 End of hashtable reached
 * @retval -1 Iterator advanced to next element
 */
int hashtable_iterator_advance(struct hashtable_itr *itr)
{
	unsigned int j, tablelength;
	struct entry **table;
	struct entry *next;
	if (NULL == itr->e)
		return 0;	/* stupidity check */

	// check to see if there is another bucket in the current table index
	next = itr->e->next;
	if (NULL != next) {
		itr->parent = itr->e;
		itr->e = next;
		return -1;
	}
	// are we at the end of the table?
	tablelength = itr->h->tablelength;
	itr->parent = NULL;
	j = ++(itr->index);

	if (tablelength <= j) {
		itr->e = NULL;
		return 0;
	}
	// scan the table until we find another entry
	table = itr->h->table;
	while (NULL == (next = table[j])) {
		if (++j >= tablelength) {
			itr->index = tablelength;
			itr->e = NULL;
			return 0;
		}
	}
	itr->index = j;
	itr->e = next;
	return -1;
}

int hash_itr_next(struct hashtable_itr *itr, void **key, void **val)
{
	unsigned int j, tablelength;
	struct entry **table;
	struct entry *next;
	if (NULL == itr->e)
		return 0;	/* stupidity check */

	// check to see if there is another bucket in the current table index
	next = itr->e->next;
	if (NULL != next) {
		itr->parent = itr->e;
		itr->e = next;
		goto found;
	}
	// are we at the end of the table?
	tablelength = itr->h->tablelength;
	itr->parent = NULL;
	j = ++(itr->index);
	if (tablelength <= j) {
		itr->e = NULL;
		return 0;
	}
	// scan the table until we find another entry
	table = itr->h->table;
	while (NULL == (next = table[j])) {
		if (++j >= tablelength) {
			itr->index = tablelength;
			itr->e = NULL;
			return 0;
		}
	}
	itr->index = j;
	itr->e = next;
found:
	*key = itr->e->k;
	*val = itr->e->v;
	return -1;
}

/**
 * remove the entry at the current iterator position
 * and advance the iterator, if there is a successive
 * element. If you want the value, read it before you remove:
 * beware memory leaks if you don't.
 *
 * @param itr hashtable iterator
 * @retval -1 iterator advanced to next entry in table
 * @retval 0 end of iteration.
 */

int hashtable_iterator_remove(struct hashtable_itr *itr)
{
	struct entry *remember_e, *remember_parent;
	int ret;

	/* Do the removal */
	if (NULL == (itr->parent)) {
		/* element is head of a chain */
		itr->h->table[itr->index] = itr->e->next;
	} else {
		/* element is mid-chain */
		itr->parent->next = itr->e->next;
	}
	/* itr->e is now outside the hashtable */
	remember_e = itr->e;
	itr->h->entrycount--;

	freekey(remember_e->k);

	/* Advance the iterator, correcting the parent */
	remember_parent = itr->parent;
	ret = hashtable_iterator_advance(itr);
	if (itr->parent == remember_e) {
		itr->parent = remember_parent;
	}
	free(remember_e);
	return ret;
}

/**
 * overwrite the supplied iterator, to point to the entry
 * matching the supplied key.
 *
 * @param itr hashtable iterator
 * @param h hashtable to be searched
 * @param k key to search for
 * @retval 0 Not found
 * @retval -1 Key was found and iterator updated
 */
int
hashtable_iterator_search(struct hashtable_itr *itr,
			  struct hashtable *h, void *k)
{
	struct entry *e, *parent;
	unsigned int hashvalue, index;

	hashvalue = hash(h, k);
	index = indexFor(h->tablelength, hashvalue);

	e = h->table[index];
	parent = NULL;
	while (NULL != e) {
		/* Check hash value to short circuit heavier comparison */
		if ((hashvalue == e->h) && (h->eqfn(k, e->k))) {
			itr->index = index;
			itr->e = e;
			itr->parent = parent;
			itr->h = h;
			return -1;
		}
		parent = e;
		e = e->next;
	}
	return 0;
}

/**
 * function to change the value associated with a key, where there already
 * exists a value bound to the key in the hashtable.
 * Source due to Holger Schemel
 *
 * If found, the existing value is freed.
 *
 * @param h hashtable to search
 * @param k key to search for.
 * @param v the new value to associate with the key
 * @retval 0 Key not found
 * @retval -1 Key found, old value freed, new value now associated with key
 */
int hashtable_change(struct hashtable *h, void *k, void *v)
{
	struct entry *e;
	unsigned int hashvalue, index;
	hashvalue = hash(h, k);
	index = indexFor(h->tablelength, hashvalue);
	e = h->table[index];
	while (NULL != e) {
		/* Check hash value to short circuit heavier comparison */
		if ((hashvalue == e->h) && (h->eqfn(k, e->k))) {
			free(e->v);
			e->v = v;
			return -1;
		}
		e = e->next;
	}
	return 0;
}

/*
 * Copyright (c) 2002, Christopher Clark
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * * Redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer.
 *
 * * Redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution.
 *
 * * Neither the name of the original author; nor the names of any contributors
 * may be used to endorse or promote products derived from this software
 * without specific prior written permission.
 *
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER
 * OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
