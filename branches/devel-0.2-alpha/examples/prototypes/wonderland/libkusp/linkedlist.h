/**
 * @file
 * @author Andrew Boie
 */

#ifndef __LINKEDLIST_H__
#define __LINKEDLIST_H__

#ifdef __cplusplus
extern "C" {
#endif 

typedef struct list_s {
	void * item;
	struct list_s *next;
	struct list_s *prev;
} list_t;



list_t *create_list(void);
void list_append(list_t *list, void *item);
void list_prepend(list_t *list, void *item);
// back is freed, front will have merged list
void list_merge(list_t *front, list_t *back);
void list_delete(list_t *entry);

// runs in linear time
int list_size(list_t *list);

list_t *list_index(list_t *list, int idx);
int list_empty(list_t *list);


// frees the entire list. does not touch stored values.
void list_free(list_t *head);

/**
 * list_for_each	-	iterate over a list
 * @param pos	the &struct list_head to use as a loop counter.
 * @param head	the head for your list.
 */
#define list_for_each(pos, head) \
	for (pos = (head)->next; pos != (head); \
        	pos = pos->next)
        	
/**
 * list_for_each_safe	-	iterate over a list safe against removal of list entry
 * @param pos	the &struct list_head to use as a loop counter.
 * @param n	another &struct list_head to use as temporary storage
 * @param head	the head for your list.
 */
#define list_for_each_safe(pos, n, head) \
	for (pos = (head)->next, n = pos->next; pos != (head); \
		pos = n, n = pos->next)

#ifdef __cplusplus
}
#endif 

#endif


