#include "dstrm_buffer.h"
#include "pool.h"

#include <stdlib.h>
#include <string.h>
#include <kusp_common.h>
#include <mutex.h>
#include <errno.h>

#include "dsui_private.h"

#if POOL_DEBUG
#define pool_debug(...) dprintf(__VA_ARGS__)
#else
#define pool_debug(...)
#endif

// @@@@@@@@@ Buffer Pool Functions @@@@@@@@@@

/**
 * Allocate a pool of datastream buffers
 *
 * @param pool Uninitialized pool
 * @param page_count Initial number of buffers in the buffer pool. If this runs
 * out the pool size will be doubled.
 * @param page_size Size, in bytes of each buffer. The amount of space available
 * will be slightly less, since the struct dstrm_buffer_s is located at the end
 * of the page.
 * @retval 0 success, -1 failure
 */
int dstrm_pool_init(struct dstrm_pool *pool, unsigned int page_count, unsigned int page_size)
{
	int i;
	pool_debug("Initializing buffer pool of %d %d byte pages, %d kilobytes total.\n",
			page_count, page_size, page_count * page_size / 1024);

	pool->page_count = page_count;
	pool->page_size = page_size;
	pool->max_size = page_size - sizeof(struct dstrm_buffer);

	// create array-based queue of page nodes
	pool->page_nodes = malloc(page_count * sizeof(struct dstrm_page_node));
	pool->page_list.head = pool->page_nodes;
	pool->page_list.tail = &pool->page_nodes[page_count - 1];

	for (i=0; i < page_count; i++) {
		pool->page_nodes[i].num = i;
		pool->page_nodes[i].data = malloc(page_size);

		if (!pool->page_nodes[i].data) {
			eprintf("Unable to allocate memory for pool page %d.\n", i);
			return -ENOMEM;
		}

		if (i == page_count -1) {
			pool->page_nodes[i].next = NULL;
		} else {
			pool->page_nodes[i].next = &pool->page_nodes[i+1];
		}
	}

	km_mutex_init(&pool->lock, NULL);

	return 0;
}

/**
 * Free all memory used by pool for page node array and buffer pages
 *
 * @param pool pool to free
 */
void free_pool(struct dstrm_pool *pool) {
	int i;

	km_mutex_lock(&pool->lock);

	for (i=0; i < pool->page_count; i++) {
		free(pool->page_nodes[i].data);
	}
	free(pool->page_nodes);
	pool->page_count = 0;

	km_mutex_unlock(&pool->lock);
}

/**
 * Expand the size of a buffer pool. This requires
 * reallocating pool->page_nodes, and allocating memory
 * for all the new pages. Existing pages are not disturbed
 *
 * @param pool dsui pool to expand
 * @param new_pages new size of pool, if not greater than pool->page_count
 * nothing happens.
 */
static void __expand_pool(struct dstrm_pool *pool, unsigned int new_page_count) {
	unsigned int starting_index;
	struct dstrm_page_node *new_page_nodes;
	int i;

	pool_debug("Expanding dsui pool to %d pages.\n", new_page_count);

	starting_index = new_page_count - pool->page_count;
	new_page_nodes = malloc(new_page_count * sizeof(struct dstrm_page_node));

	if (!new_page_nodes) {
		eprintf("Unable to allocate list for expanded pool page numbers: %s\n",
				strerror(errno));
		return;
	}

	// copy the existing elements in the old array to the new one
	memcpy(new_page_nodes, pool->page_nodes, sizeof(struct dstrm_page_node) * pool->page_count);
	free(pool->page_nodes);
	pool->page_nodes = new_page_nodes;
	pool->page_count = new_page_count;

	// initialize the new elements
	for (i = starting_index; i < pool->page_count; i++) {
		pool->page_nodes[i].num = i;
		pool->page_nodes[i].data = malloc(pool->page_size);
		if (!pool->page_nodes[i].data) {
			eprintf("Unable to allocate memory for expanded pool page %d.: %s\n",
					i, strerror(errno));

			// we ran out of memory. use what we were able to allocate.
			pool->page_count = i;
			pool->page_nodes[i-1].next = NULL;
			break;
		}

		if (i == new_page_count - 1) {
			// this is the last page in the expanded pool,
			// and therefore there is no 'next' entry
			pool->page_nodes[i].next = NULL;
		} else {
			pool->page_nodes[i].next = &pool->page_nodes[i+1];
		}
	}

	// in most cases there will be no free page nodes in the original array,
	// but just to be sure, correct any links if they exist.
	if (pool->page_list.head == NULL) {
		// no free nodes in original array
		pool->page_list.head = &pool->page_nodes[starting_index];
	} else {
		pool->page_list.tail->next = &pool->page_nodes[starting_index];
	}
	pool->page_list.tail = &pool->page_nodes[pool->page_count - 1];

}


/**
 * obtain an empty buffer from the buffer pool, expanding
 * the pool if necessary. if the pool is expanded, it will
 * double its size.
 *
 * @param pool	pool to obtain buffer from
 * @retval	A dsui buffer from that pool, or NULL if out of memory
 */
struct dstrm_buffer *obtain_buffer(struct dstrm_pool *pool)
{
	struct dstrm_page_node *bufferpage;
	struct dstrm_buffer *newbuffer;

	km_mutex_lock(&pool->lock);

	if (pool->page_list.head == NULL) {
		__expand_pool(pool, pool->page_count * 2);
	}

	if (pool->page_list.head == NULL) {
		eprintf("obtain buffer failed\n");
		km_mutex_unlock(&pool->lock);
		return NULL;
	}

	bufferpage = pool->page_list.head;

	/* the dstrm_buffer struct will be at the very end of the chunk of data.
	 * someone claimed that this was somehow faster due to the way
	 * caches work. i don't believe it. but it doesn't really matter */
	newbuffer = (bufferpage->data + pool->page_size - sizeof(struct dstrm_buffer));
	newbuffer->pool = pool;
	newbuffer->page_num = bufferpage->num;
	newbuffer->buffer_start = bufferpage->data;
	newbuffer->buffer_end = newbuffer;
	newbuffer->data_start = newbuffer->buffer_start;
	newbuffer->data_end = newbuffer->buffer_start;

	pool->page_list.head = bufferpage->next;
	bufferpage->next = NULL;

	km_mutex_unlock(&pool->lock);

	INIT_LIST_HEAD(&newbuffer->list);

	pool_debug("Obtained buffer from page #%d of the pool.\n", newbuffer->page_num);

	return newbuffer;
}


/**
 * return a buffer to the buffer pool, we don't need it anymore.
 * Memory referenced by buffer_pull calls will be undefined after
 * this call, so be sure to copy/write/whatever that memory before you
 * do this.
 *
 * This function is thread-safe with a shared pool, but make sure you have
 * exclusive access to a buffer before you release it. Simply locking the
 * buffer before releasing it is not a good way to accomplish that, as it
 * can lead to deadlock.
 *
 * @param buffer Buffer to release back to the pool.
 */
void release_buffer(struct dstrm_buffer *buffer) {
	struct dstrm_pool *pool = buffer->pool;
	int page_num = buffer->page_num;

	pool_debug("Releasing buffer at page #%d back to the pool.\n", page_num);
	km_mutex_lock(&pool->lock);

	if (pool->page_list.tail == NULL && pool->page_list.head == NULL) {
		// there were no free pages at all
		pool->page_list.head = &pool->page_nodes[page_num];
		pool->page_list.tail = pool->page_list.head;
	} else {
		// there were some free pages, so add this page to the
		// end of the existing list
		pool->page_list.tail->next = &pool->page_nodes[page_num];
		pool->page_list.tail = pool->page_list.tail->next;
	}
	pool->page_list.tail->next = NULL;

	km_mutex_unlock(&pool->lock);
}


