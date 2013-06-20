/**
 * @file buffer_thread.c
 */


#include "buffer_thread.h"
#include "dstrm_buffer.h"
#include "buffer_queue.h"
#include "pool.h"
#include "dsui_private.h"

#include <sys/syscall.h>
#include <sys/types.h>
#include <misc.h>
#include <mutex.h>
#include <pthread.h>
#include <sys/signal.h>
#include <taskalias.h>

#include <dsui.h>

#if BUFFER_THREAD_DEBUG
#define buffer_debug(...) dprintf(__VA_ARGS__)
#else
#define buffer_debug(...)
#endif
#define CONFIG_DSUI_DEBUG 1

static void *buffer_thread_run(void *param)
{
	struct buffer_thread *self = param;
	int retval;

	//task_alias_add_alias(0, "dskid");

	// this function passes the pid of this buffer thread to a function defined
	// in dsui.c, we do this so that we come to know about the pid of the buffer
	// thread when DSUI is enabled
	// FIXME: 
	// Bad way to get the thread id.
	set_buffer_thread_pid(syscall(SYS_gettid));
	
	// we don't want to handle signals
	sigset_t mask;
	sigfillset(&mask);
	if ((retval = pthread_sigmask(SIG_BLOCK, &mask, NULL))) {
		kusp_errno("pthread_sigmask", retval);
	}
	buffer_debug("Buffer management thread started, PID=%d\n",
			gettid());

	while (1) {
		km_mutex_lock(&self->cache->lock);

		while (self->cache->num_buffers >= self->cache_size) {
			if (!self->running) {
				km_mutex_unlock(&self->cache->lock);
				goto finished;
			}

			buffer_debug("Buffer management thread sleeping.\n");
			km_cond_wait(&self->cache->cond, &self->cache->lock);
			buffer_debug("Buffer management thread woke up.\n");
		}
		km_mutex_unlock(&self->cache->lock);
		fill_datastream_cache(self->pool, self->cache, self->cache_size);
	}
finished:
	buffer_debug("Buffer management thread terminating.\n");
	return NULL;
}

/**
 * Kill a running buffer thread
 */
int close_buffer_thread(struct buffer_thread *self)
{
	int retval;
	buffer_debug("called\n");

	km_mutex_lock(&self->cache->lock);

	if (self->running == 0) {
		eprintf("buffer thread already closed.\n");
		km_mutex_unlock(&self->cache->lock);
		return -1;
	}

	self->running = 0;
	km_cond_signal(&self->cache->cond);
	km_mutex_unlock(&self->cache->lock);

	buffer_debug("waiting for thread to die\n");

	if ((retval = pthread_join(self->thread, NULL))) {
		kusp_errno("pthread_join", retval);
		return -1;
	}

	buffer_debug("thread killed\n");

	return 0;
}


/**
 * Examine a datastream's empty buffer cache, and ensure it has a minimum number of
 * buffers in it. This is normally called in the buffer thread's context, but in an
 * emergency it can be called in application context as well.
 *
 * @param pool pool to obtain new buffers from
 * @param cache queue to add buffers to
 * @param amount minimum number of buffers in queue
 */
void fill_datastream_cache(struct dstrm_pool *pool,
		struct dstrm_buffer_queue *cache, int amount)
{
	// FIXME: does putting the lock inside the while loop
	// increase granularity?
	while (1) {
		struct dstrm_buffer *newbuff;
		km_mutex_lock(&cache->lock);
		if (amount - cache->num_buffers <= 0) {
			km_mutex_unlock(&cache->lock);
			break;
		}
		newbuff = obtain_buffer(pool);
		if (!newbuff) {
			eprintf("fill stream cache failed, out of memory\n");
			km_mutex_unlock(&cache->lock);
			break;
		}
		__buffer_queue_enqueue(cache, newbuff);
		km_mutex_unlock(&cache->lock);
	}
}

/**
 * Create a buffer management thread. It monitors a queue of buffers
 * and ensures it has a minumum number of buffers in it.
 *
 * @param self Pointer to uninitialized struct buffer_thread
 * @param pool pool to get new buffers from
 * @param cache_size Minimum number of buffers to maintain in each
 * datastream's cache of empty buffers. If this cache is exhausted by logging
 * events in a heavily CPU-bound process, populate_datastream_queues will be
 * called in the application's context, which is a bad thing.
 * @param cache queue of new buffers to maintain
 * @retval 0 success
 */
int init_buffer_thread(struct buffer_thread *self, struct dstrm_pool *pool,
		int cache_size, struct dstrm_buffer_queue *cache)
{
	pthread_attr_t attr;
	size_t stacksize;
	int retval;

	buffer_debug("called\n");

	self->pool = pool;
	self->cache_size = cache_size;
	self->cache = cache;
	self->running = 1;

	pthread_attr_init(&attr);
   	pthread_attr_getstacksize (&attr, &stacksize);
	buffer_debug("Buffer management thread stack size = %d\n", stacksize);

	retval = pthread_create(&self->thread, &attr,
			&buffer_thread_run, self);
	if (retval) {
		kusp_errno("pthread_create", retval);
		return -1;
	}


	return 0;
}


