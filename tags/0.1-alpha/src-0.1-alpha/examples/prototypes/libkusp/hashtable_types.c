#include "hashtable.h"
#include <stdio.h>
#include <string.h>

unsigned int hash_string(void * key)
{
	char *str = (char *)key;
	unsigned int hash = 0;
	int c;

	while ((c = *str++))
		hash = c + (hash << 6) + (hash << 16) - hash;

        return hash;
}

int string_key_equal(void * key1, void * key2) {
	char *skey1, *skey2;
	skey1 = (char*)key1;
	skey2 = (char*)key2;

	if (strcmp(key1, key2) != 0) {
		return 0;
	} else {
		return -1;
	}
}

unsigned int hash_int(void * key) {
	return (unsigned int)(*((int *)key));
}

int int_key_equal(void * key1, void * key2) {
	return (*((int*)(key1))) == (*((int*)(key2)));
}
