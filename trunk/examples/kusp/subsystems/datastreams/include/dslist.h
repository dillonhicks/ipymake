#ifndef _DSUI_LIST_H
#define _DSUI_LIST_H

/*
 * Simple doubly linked list implementation.
 *
 * Some of the internal functions ("__xxx") are useful when
 * manipulating whole lists rather than single entries, as
 * sometimes we already know the next/prev entries and we can
 * generate better code by using them directly rather than
 * using the generic single-entry routines.
 */

struct dstrm_list_head {
	struct dstrm_list_head *next, *prev;
};

#define LIST_HEAD_INIT(name) { &(name), &(name) }

#define LIST_HEAD(name) \
	struct dstrm_list_head name = LIST_HEAD_INIT(name)

#define INIT_LIST_HEAD(ptr) do { \
	(ptr)->next = (ptr); (ptr)->prev = (ptr); \
} while (0)

/*
 * Insert a new entry between two known consecutive entries. 
 *
 * This is only for internal list manipulation where we know
 * the prev/next entries already!
 */
static __inline__ void __dstrm_list_add(struct dstrm_list_head * _new,
	struct dstrm_list_head * prev,
	struct dstrm_list_head * next)
{
	next->prev = _new;
	_new->next = next;
	_new->prev = prev;
	prev->next = _new;
}

/**
 * dstrm_list_add - add a new entry
 * @new: new entry to be added
 * @head: list head to add it after
 *
 * Insert a new entry after the specified head.
 * This is good for implementing stacks.
 */
static __inline__ void dstrm_list_add(struct dstrm_list_head *_new, struct dstrm_list_head *head)
{
	__dstrm_list_add(_new, head, head->next);
}

/**
 * dstrm_list_add_tail - add a new entry
 * @new: new entry to be added
 * @head: list head to add it before
 *
 * Insert a new entry before the specified head.
 * This is useful for implementing queues.
 */
static __inline__ void dstrm_list_add_tail(struct dstrm_list_head *_new, struct dstrm_list_head *head)
{
	__dstrm_list_add(_new, head->prev, head);
}

/*
 * Delete a list entry by making the prev/next entries
 * point to each other.
 *
 * This is only for internal list manipulation where we know
 * the prev/next entries already!
 */
static __inline__ void __dstrm_list_del(struct dstrm_list_head * prev,
				  struct dstrm_list_head * next)
{
	next->prev = prev;
	prev->next = next;
}

/**
 * dstrm_list_del - deletes entry from list.
 * @entry: the element to delete from the list.
 * Note: dstrm_list_empty on entry does not return true after this, the entry is in an undefined state.
 */
static __inline__ void dstrm_list_del(struct dstrm_list_head *entry)
{
	__dstrm_list_del(entry->prev, entry->next);
	entry->next = entry->prev = 0;
}

/**
 * dstrm_list_del_init - deletes entry from list and reinitialize it.
 * @entry: the element to delete from the list.
 */
static __inline__ void dstrm_list_del_init(struct dstrm_list_head *entry)
{
	__dstrm_list_del(entry->prev, entry->next);
	INIT_LIST_HEAD(entry); 
}

/**
 * dstrm_list_empty - tests whether a list is empty
 * @head: the list to test.
 */
static __inline__ int dstrm_list_empty(struct dstrm_list_head *head)
{
	return head->next == head;
}

/**
 * dstrm_list_splice - join two lists
 * @list: the new list to add.
 * @head: the place to add it in the first list.
 */
static __inline__ void dstrm_list_splice(struct dstrm_list_head *list, struct dstrm_list_head *head)
{
	struct dstrm_list_head *first = list->next;

	if (first != list) {
		struct dstrm_list_head *last = list->prev;
		struct dstrm_list_head *at = head->next;

		first->prev = head;
		head->next = first;

		last->next = at;
		at->prev = last;
	}
}

/**
 * dstrm_list_entry - get the struct for this entry
 * @ptr:	the &struct dstrm_list_head pointer.
 * @type:	the type of the struct this is embedded in.
 * @member:	the name of the dstrm_list_struct within the struct.
 */
#define dstrm_list_entry(ptr, type, member) \
	((type *)((char *)(ptr)-(unsigned long)(&((type *)0)->member)))

/**
 * dstrm_list_for_each	-	iterate over a list
 * @pos:	the &struct dstrm_list_head to use as a loop counter.
 * @head:	the head for your list.
 */
#define dstrm_list_for_each(pos, head) \
	for (pos = (head)->next; pos != (head); \
        	pos = pos->next)
        	
/**
 * dstrm_list_for_each_safe	-	iterate over a list safe against removal of list entry
 * @pos:	the &struct dstrm_list_head to use as a loop counter.
 * @n:		another &struct dstrm_list_head to use as temporary storage
 * @head:	the head for your list.
 */
#define dstrm_list_for_each_safe(pos, n, head) \
	for (pos = (head)->next, n = pos->next; pos != (head); \
		pos = n, n = pos->next)

/**
 * list_for_each_entry	-	iterate over list of given type
 * @pos:	the type * to use as a loop cursor.
 * @head:	the head for your list.
 * @member:	the name of the list_struct within the struct.
 */
#define dstrm_list_for_each_entry(pos, head, member)				\
	for (pos = dstrm_list_entry((head)->next, typeof(*pos), member);	\
	     prefetch(pos->member.next), &pos->member != (head); 	\
	     pos = dstrm_list_entry(pos->member.next, typeof(*pos), member))

/**
 * list_for_each_entry_safe - iterate over list of given type safe against removal of list entry
 * @pos:	the type * to use as a loop cursor.
 * @n:		another type * to use as temporary storage
 * @head:	the head for your list.
 * @member:	the name of the list_struct within the struct.
 */
#define dstrm_list_for_each_entry_safe(pos, n, head, member)			\
	for (pos = dstrm_list_entry((head)->next, typeof(*pos), member),	\
		n = dstrm_list_entry(pos->member.next, typeof(*pos), member);	\
	     &pos->member != (head); 					\
	     pos = n, n = dstrm_list_entry(n->member.next, typeof(*n), member))

#endif
