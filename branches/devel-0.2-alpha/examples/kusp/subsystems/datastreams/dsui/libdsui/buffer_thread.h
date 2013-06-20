/**
 * @file buffer_thread.h
 */

#ifndef _BUFFER_THREAD_H_
#define _BUFFER_THREAD_H_

#include <pthread.h>
#include "buffer_queue.h"
#include "pool.h"


/**
 * This datastructure represents a running buffer management thread
 */
struct buffer_thread {
	/// pool to retrieve empty buffers from
	struct dstrm_pool *pool;

	/// the buffer thread itself
	pthread_t thread;

	/// minimum number of buffers to keep in cache
	unsigned int cache_size;

	/// cache of empty buffers to keep populated
	struct dstrm_buffer_queue *cache;
	
	/// set to 0 and wakeup the thread to kill it
	int running;
};

int init_buffer_thread(struct buffer_thread *self, struct dstrm_pool *pool,
		int cache_size, struct dstrm_buffer_queue *cache);
void fill_datastream_cache(struct dstrm_pool *pool, struct dstrm_buffer_queue *cache, 
		int amount);

int close_buffer_thread(struct buffer_thread *self);

#endif
