#ifndef _DATASTREAM_H_
#define _DATASTREAM_H_

#include <dsui.h>
#include <dsentity.h>

#include "logging_thread.h"
#include "buffer_thread.h"
#include "pool.h"
#include "buffer_queue.h"

struct buffer_thread;
struct dstrm_pipeline;

/**
 * This structure represents a datastream. During initialization,
 * the datastream is registered with all entities it is supposed to log.
 */
struct datastream {
	/** a unique id for this datastream */
	int id;

	/* list of all enabled entities for this datastream */
	struct dstrm_list_head enabled;

	/** These filters are used to determine whether
	 * an event should be logged or not */
	struct dstrm_pipeline *pre_filters;

	/** These filters are used when the datastream
	 * is in ringbuffer mode. If the pipeline accepts
	 * the event, flush the ringbuffer to the logging thread */
	struct dstrm_pipeline *trigger_filters;

	/** number of entities logged to this datastream */
	int log_count;

	/** thread in charge of logging events.
	 * we will put full buffers on its queue
	 * so they can be written out
	 *
	 * this logging thread can be shared by many datastreams,
	 * each writing to the same file */
	struct logging_thread *logging_thread;

	/** Pool to retrieve new buffers from	 */
	struct dstrm_pool *pool;

	/** Number of buffers to keep in cache. */
	unsigned int cache_size;

	/** buffer management thread. we will
	 * wake this up when we need more empty buffers */
	struct buffer_thread buffer_thread;

	/** a cache of empty buffers to write events to.
	 * the buffer thread will automatically replenish
	 * this queue. */
	struct dstrm_buffer_queue cache;

	/** number of times we ran out of buffers in the cache,
	 * and had to manually fill the datastream cache ourselves. */
	unsigned long block_counter;

	/** buffer mode */
	enum datastream_mode mode;
};

struct datastream *datastream_create(int id, struct dstrm_pool *pool,
		struct logging_thread *logging_thread,
		unsigned int cache_size, enum datastream_mode mode);

void datastream_set_pre_filters(struct datastream *datastream,
		struct dstrm_pipeline *filterpipe);
void datastream_set_trigger_filters(struct datastream *datastream,
		struct dstrm_pipeline *filterpipe);
int datastream_disable(struct datastream *datastream);

int entity_enable(struct datastream *d, struct datastream_ip_data *ip,
		union ds_entity_info *config_info);
void entity_disable(struct datastream *d, struct datastream_ip_data *ip);

void datastream_log(struct datastream *d, const void *data1,
		unsigned int size1,
		const void *data2, unsigned int size2);
void datastream_flush(struct datastream *d);
void datastream_snapshot(struct datastream *d);


#endif
