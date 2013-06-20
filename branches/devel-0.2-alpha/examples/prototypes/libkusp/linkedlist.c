/**
 * A linked list implementation. Unlike the kernel linked lists that
 * we sometimes use, these pointer-based lists can store arbitrary data.
 *
 * @file libkusp/linkedlist.c
 * @addtogroup libkusp libkusp
 */

#include "linkedlist.h"
#include <stdlib.h>
#include <assert.h>


/**
 * Allocate an empty list and return a pointer to it.
 * @return	A pointer to a new list
 */
list_t *create_list() {
	list_t *result = malloc(sizeof(list_t));
	result->next = result;
	result->prev = result;
	result->item = NULL;
	return result;
}

/**
 * Create a new list entry, place the provided pointer inside it, and
 * append this entry to the end of the list. Runs in constant time.
 * @param 	list	Head of list to add item to
 * @param	item	Arbitrary pointer to add to list
 */
void list_append(list_t *list, void *item) {
	assert(list->item == NULL);
	list_t *newlink = malloc(sizeof(list_t));
	newlink->item = item;
	newlink->next = list;
	newlink->prev = list->prev;
	list->prev->next = newlink;
	list->prev = newlink;
}

/**
 * Create a new list entry, place the provided pointer inside it, and
 * prepend this entry to the beginning of the list. Runs in constant time.
 * @param 	list	Head of list to add item to
 * @param	item	Arbitrary pointer to add to list
 */

void list_prepend(list_t *list, void *item) {
	assert(list->item == NULL);
	list_t *newlink = malloc(sizeof(list_t));
	newlink->item = item;
	newlink->next = list->next;
	newlink->prev = list;
	list->next->prev = newlink;
	list->next = newlink;
}

/**
 * Merge two lists together by appending the 'back' list to the end
 * of the 'front' list. The pointer to the back list will be freed.
 * Runs in constant time.
 * @param	front Pointer to head of list that will be front of merged list
 * @param	back  Pointer to head of list that will be back of merged list
 */
void list_merge(list_t *front, list_t *back) {
	assert (front->item == NULL && back->item == NULL);
	front->prev->next = back->next;
	back->next->prev = front->prev;
	front->prev = back->prev;
	front->prev->next = front;
	back->next = back->prev = 0;
	free(back);
}

/**
 * Delete an entry within a linked list and free it. The item contained within
 * will not be touched. This function must not be called on a list head, if you
 * need to free an entire list, use list_free. Runs in constant time.
 * @param	entry	List entry to delete
 */
void list_delete(list_t *entry) {
	assert (entry->item != NULL);
	entry->next->prev = entry->prev;
	entry->prev->next = entry->next;
	entry->next = entry->prev = 0;
	free(entry);
}

/**
 * Return the size of a linked list. This function runs in linear time
 * with respect to the size of the list.
 * @param list	The list whose size you want to measure
 * @return The size of the list
 */
int list_size(list_t *list) {
	list_t *pos;
	int counter = 0;
	list_for_each(pos, list) {
		counter++;
	}
	return counter;
}

/**
 * Return a specific entry within a linked list. Bounds checking is not done
 * and will wrap around if too large. Must be called on the head of a list. Runs
 * in linear time. List entries start at 0.
 * @param	list	Head of list
 * @param	index	Index within list to retrieve
 * @retval	List entry that corresponds to given index.
 */
list_t *list_index(list_t *list, int index) {
	assert (list->item == NULL);
	int i;
	for (i=0; i <= index; i++) {
		list = list->next;
	}
	return list;
}

/**
 * Determine whether a list is empty. Runs in constant time.
 * @param list	List to examine
 * @retval	nonzero if it is empty
 * @retval	0 if not.
 */
int list_empty(list_t *list) {
	return list->next == list;
}

/**
 * Free memory allocated to an entire list. Does not disturb stored values.
 * Runs in constant time.
 * @param head	Head of list to free
 */
void list_free(list_t *head) {
	list_t *pos, *n;

	list_for_each_safe(pos, n, head) {
		free(pos);
	}
	free(head);
}
