/**
 * @file
 */

/* Copyright (C) 2002 Christopher Clark <firstname.lastname@cl.cam.ac.uk> */

#ifndef __HASHTABLE_CWC22_H__
#define __HASHTABLE_CWC22_H__
#include <linkedlist.h>

#ifdef __cplusplus
extern "C" {
#endif 

struct hashtable;
typedef struct hashtable hashtable_t;
struct hashtable_itr;
typedef struct hashtable_itr hashtable_itr_t;


/* new functions I added, inspired by Python C interface */
int hashtable_iterate(struct hashtable *h, hashtable_itr_t *pos,
		void *key, void *value);
#define HASH_ITR_INIT {NULL, NULL, NULL, 0}




hashtable_t *create_hashtable(unsigned int minsize,
                 unsigned int (*hashfunction) (void*),
                 int (*key_eq_fn) (void*,void*));
/* use these functions to create hashtables that use string keys */
unsigned int hash_string(void * key);
int string_key_equal(void * key1, void * key2);

/* use these functions to create hashtables thet use integer keys */
unsigned int hash_int(void * key);
int int_key_equal(void * key1, void * key2);


int hashtable_insert(hashtable_t *h, void *k, void *v);
void *hashtable_search(hashtable_t *h, void *k);
void *hashtable_remove(hashtable_t *h, void *k);
unsigned int hashtable_count(hashtable_t *h);
hashtable_t *hashtable_merge(hashtable_t *target, hashtable_t *source);
void hashtable_destroy(hashtable_t *h, int free_values);
int hashtable_change(hashtable_t *h, void *k, void *v);

// hashtable iterator functions
hashtable_itr_t *hashtable_iterator(hashtable_t *h);
void init_iterator(hashtable_itr_t *itr, hashtable_t *h);
void *hashtable_iterator_key(hashtable_itr_t *i);
void *hashtable_iterator_value(hashtable_itr_t *i);
int hashtable_iterator_advance(hashtable_itr_t *itr);
int hashtable_iterator_remove(hashtable_itr_t *itr);
int hashtable_iterator_search(hashtable_itr_t *itr,
                          hashtable_t *h, void *k);
int hash_itr_next(struct hashtable_itr *itr, void **key, void **val);

/* macros for creating tyoe-restricted hashtable
 * manipulation functions
 */
#define DEFINE_HASHTABLE_ITERATOR_SEARCH(fnname, keytype) \
int fnname (hashtable_itr_t *i, hashtable_t *h, keytype *k) \
{ \
    return (hashtable_iterator_search(i,h,k)); \
}

#define DEFINE_HASHTABLE_INSERT(fnname, keytype, valuetype) \
int fnname (hashtable_t *h, keytype *k, valuetype *v) \
{ \
    return hashtable_insert(h,k,v); \
}

#define DEFINE_HASHTABLE_SEARCH(fnname, keytype, valuetype) \
valuetype * fnname (hashtable_t *h, keytype *k) \
{ \
    return (valuetype *) (hashtable_search(h,k)); \
}

#define DEFINE_HASHTABLE_REMOVE(fnname, keytype, valuetype) \
valuetype * fnname (hashtable_t *h, keytype *k) \
{ \
    return (valuetype *) (hashtable_remove(h,k)); \
}

// you should never manipulate these structures directly
struct entry
{
    void *k, *v;
    unsigned int h;
    struct entry *next;
};

struct hashtable {
    unsigned int tablelength;
    struct entry **table;
    unsigned int entrycount;
    unsigned int loadlimit;
    unsigned int primeindex;
    unsigned int (*hashfn) (void *k);
    int (*eqfn) (void *k1, void *k2);
};

struct hashtable_itr
{
    struct hashtable *h;
    struct entry *e;
    struct entry *parent;
    unsigned int index;
};

#ifdef __cplusplus
}
#endif 

#endif /* __HASHTABLE_CWC22_H__ */

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
