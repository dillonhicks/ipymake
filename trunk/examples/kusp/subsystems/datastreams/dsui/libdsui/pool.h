#ifndef _POOL_H_
#define _POOL_H_

#include "dstrm_buffer.h"
#include <pthread.h>

/// this is an array implementation of a queue of free page nodes
struct dstrm_page_node {
	int num;
	struct dstrm_page_node *next;
	void *data;
};

struct dstrm_page_list {
	struct dstrm_page_node *head, *tail;
};

struct dstrm_buffer;

/**
 * a datastructure to manage a collection of pre-allocated buffers.
 */
struct dstrm_pool {
	
	/// number of pages in pool
	unsigned int page_count;

	/// size, in bytes, of each page
	unsigned int page_size;

	/// maximum amount of data that can be stored in a pool page
	unsigned int max_size;
	
	/// array of page list entries, of size page_count
	struct dstrm_page_node *page_nodes;

	/// pointers to head and tail of free page list
	struct dstrm_page_list page_list;

	pthread_mutex_t lock;
};


// pool functions
int dstrm_pool_init(struct dstrm_pool *pool, unsigned int page_count, 
		unsigned int page_size);
void free_pool(struct dstrm_pool *pool);
struct dstrm_buffer *obtain_buffer(struct dstrm_pool *pool);
void release_buffer(struct dstrm_buffer *buffer);

#endif
