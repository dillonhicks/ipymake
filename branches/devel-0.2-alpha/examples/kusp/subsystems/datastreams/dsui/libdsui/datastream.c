#include "datastream.h"
#include "entity.h"
#include <dsui.h>
#include <mutex.h>
#include <stdlib.h>
#include <assert.h>
#include "dsui_private.h"
#include <mutex.h>

#if DATASTREAM_DEBUG
#define datastream_debug(...) dprintf(__VA_ARGS__)
#else
#define datastream_debug(...)
#endif

/** Free an entity's state data structures, if applicable */
static void entity_free(int type, struct active_entity *entity)
{
	switch (type) {
 	case DS_HISTOGRAM_TYPE:
		assert(entity->entity.histogram);
		histogram_free(entity->entity.histogram);
		break;

 	case DS_EVENT_TYPE:
		return;

 	case DS_COUNTER_TYPE:
		assert(entity->entity.counter);
		free(entity->entity.counter);
		break;

 	case DS_INTERVAL_TYPE:
		assert(entity->entity.interval);
		free(entity->entity.interval);
 		break;

 	default:
		assert(0);
 	}
}

/* Take a snapshot of a stateful entity's state, if applicable */
static void entity_snapshot(struct datastream_list *dl)
{
	switch (dl->ip->type) {
	case DS_HISTOGRAM_TYPE:
		histogram_log(dl);
		break;
 	case DS_COUNTER_TYPE:
		counter_log(dl);
		break;
 	default:
 		return;
	}
}


/* Traverse an instrymentation point's list of enabled datastreams,
 * and remove the entry corresponding to the provided datastream */
static struct datastream_list *
__datastream_list_remove(struct datastream_list **list, struct datastream *d)
{
	struct datastream_list **next = list, *check;

	while ((check = *next)) {
		if (check->datastream == d) {
			*next = check->next;
			break;
		}
		next = &check->next;
	}

	return check;
}

/* Disable logging an entity for a particular datastream */
void entity_disable(struct datastream *d, struct datastream_ip_data *ip)
{
	struct datastream_list *next;

	/* find matching datastream_list. uniqueness is enforced */
	next = __datastream_list_remove(&ip->next, d);
	if (!next)
		return;


	ip->ds_array[d->id] = NULL;
	entity_free(ip->type, &next->entity);
	dstrm_list_del(&next->list);
	free(next);
	datastream_debug("(%d): disable entity [%s/%s:%u]\n", d->id,
			ip->group, ip->name, ip->id);
}

/* Initialize an entity, by making appropriate calls to the type-specific
 * initialization function in entity.c. Returns nonzero if there was
 * a problem */
static int entity_init(const struct datastream_ip_data *ip, struct datastream *d,
		struct active_entity *entity, union ds_entity_info *config_info)
{
	km_mutex_init(&entity->lock, NULL);

	switch (ip->type) {
	case DS_EVENT_TYPE:
		return 0;

	case DS_HISTOGRAM_TYPE:
		return histogram_init(ip, entity, config_info);

	case DS_COUNTER_TYPE:
		return counter_init(ip, entity, config_info);

	case DS_INTERVAL_TYPE:
		return interval_init(ip, entity, config_info);

	default:
		eprintf("Unsupported entity type!\n");
		return -1;
	}
}

/** Enable an IP for a particular datastream. Some entities require
 * additional configuration data (such as histograms).
 *
 * The internal representation is a 2-D grid of open datastreams
 * vs. instrumentation points. When an entity is enabled, a
 * struct datastream_list datastructure is allocated, providing
 * a rendezvous between the associated IP and datastream, as well as
 * storing state information (counter tally, histogram buckets, etc).
 *
 * Struct datastream_list structures are members of two different lists:
 * A per-datastream doubly-linked list of all the entities enabled for
 * a datastream (the "list" member) and a singly-linked list of all
 * the datastreams an IP is enabled for (the "next" member).
 *
 * The state information for the entity is stored in the embedded
 * active_entity structure.
 */
int entity_enable(struct datastream *d, struct datastream_ip_data *ip,
		union ds_entity_info *config_info)
{
	struct datastream_list *link;
	int ret = -1;

	link = ip->next;
	while (link) {
		if (link->datastream == d) {
			datastream_debug("Entity %d is already enabled!\n", ip->id);
			goto out;
		}
		link = link->next;
	}

	link = malloc(sizeof(*link));
	memset(link, 0, sizeof(*link));

	if (!link) {
		eprintf("Failed to allocate memory\n");
		goto out;
	}

	ret = entity_init(ip, d, &link->entity, config_info);
	if (ret) {
		free(link);
		goto out;
	}

	/* link into chain */
	link->datastream = d;
	link->ip = ip;
	ip->ds_array[d->id] = link;
	link->next = ip->next;
	ip->next = link;
	dstrm_list_add(&link->list, &d->enabled);
	datastream_debug("(%d): enable entity [%s/%s:%u]\n", d->id,
			ip->group, ip->name, ip->id);
out:
	return ret;
}


/** Create a datastream (and associated buffer management thread)
 *
 * @param log        Logging thread to write data to
 * @param cache-size The number of empty buffers maintained in the
 *                   datastream's cache
 * @param pool       The buffer pool to retrieve additional buffers from
 *                   if needed.
 * @param mode       Either STREAM_NORMAL or STREAM_CIRCULAR for ringbuffer
 *                   mode
 * @param id         A numerical id to assign to this datastream. Normally,
 *                   this would correspond to an empty cell in DSUI's
 *                   datastream array */
struct datastream *datastream_create(int id, struct dstrm_pool *pool,
		struct logging_thread *log,
		unsigned int cache_size, enum datastream_mode mode)
{
	int tmp;

	struct datastream *d = malloc(sizeof(struct datastream));

	if (!d) {
		eprintf("could not allocate memory for datastream\n");
		return NULL;
	}

	d->pre_filters = NULL;
	d->trigger_filters = NULL;
	d->id = id;
	d->log_count = 0;

	INIT_LIST_HEAD(&d->enabled);

	buffer_queue_init(&d->cache);

	if (mode != STREAM_CIRCULAR_MODE) {
		if (init_buffer_thread(&d->buffer_thread, pool,
				cache_size, &d->cache)) {
			eprintf("failed to create buffer thread");
			return NULL;
		}
	}

	d->pool = pool;
	d->logging_thread = log;
	d->cache_size = cache_size;
	d->block_counter = 0;
	d->mode = mode;


	fill_datastream_cache(pool, &d->cache, cache_size);

	tmp = __sync_add_and_fetch(&d->logging_thread->ref_count, 1);

	datastream_debug("Created datastream [%d] logging to '%s'\n",
			d->id, log->filename);

	return d;

}

/* Runtime filtering support in DSUI is currently unimplemented */
void datastream_set_pre_filters(struct datastream *datastream, struct dstrm_pipeline *filterpipe)
{
	datastream->pre_filters = filterpipe;
}

void datastream_set_trigger_filters(struct datastream *datastream, struct dstrm_pipeline *filterpipe)
{
	datastream->trigger_filters = filterpipe;
}

/** Take a snapshot of all stateful entities enabled in
 * the datastream */
void datastream_snapshot(struct datastream *d)
{
	struct datastream_list *link, *tmp;

	dstrm_list_for_each_entry_safe(link, tmp, &d->enabled, list) {
		assert(link->datastream == d);
		entity_snapshot(link);
	}
}

/** Disable a datastream
 *
 * This traverses the list of all entities enabled for the datastream and
 * disables logging for them. The buffer management thread for this
 * datastream is terminated. Then any unwritten buffers are written to the
 * disk. Finally, the datastream structure itself is freed */
int datastream_disable(struct datastream *d)
{
	struct datastream_list *link, *tmp;
	int t;

	dstrm_list_for_each_entry_safe(link, tmp, &d->enabled, list) {
		assert(link->datastream == d);
		entity_disable(link->datastream, link->ip);
	}

	datastream_debug("disable datastream [%d]\n", d->id);


	if (d->mode != STREAM_CIRCULAR_MODE &&
			close_buffer_thread(&d->buffer_thread)) {
		eprintf("Failed to kill buffer management thread\n");
	}

	while (1) {
		struct dstrm_buffer *buffer = buffer_queue_dequeue(&d->cache);
		if (buffer) {
			buffer_queue_enqueue(&d->logging_thread->queue, buffer);
		} else {
			break;
		}
	}

	if (d->block_counter) {
		wprintf("Buffer management thread failed to keep up %ld times.\n",
				d->block_counter);
	}

	t = __sync_sub_and_fetch(&d->logging_thread->ref_count, 1);

	dprintf("%d entities logged to datastream %d.\n",
			d->log_count, d->id);
	free(d);
	return 0;
}


/**
 * Flush any partially written buffers in a datastream to
 * the logging thread to be written out.
 */
void datastream_flush(struct datastream *d)
{
	datastream_debug("called for datastream %d\n", d->id);

	while (1) {
		struct dstrm_buffer *buffer = buffer_queue_dequeue(&d->cache);
		if (buffer) {
			buffer_queue_enqueue(&d->logging_thread->queue, buffer);
		} else {
			break;
		}
	}

	fill_datastream_cache(d->pool, &d->cache,
			d->cache_size);
}

/**
 * Log two chunks of data to a datastream. This function needs to be as fast
 * as possible. We use two chunks; data1 is the entity, data2 is the extra data.
 * They must be kept together in one contiguous block in the output file.
 *
 * @param datastream datastream to log to
 * @param data1 binary data to write (the entity)
 * @param size1 size of data in bytes
 * @param data2 binary data to write (the extra data)
 * @param size2 size of data in bytes
 */
void datastream_log(struct datastream *d, const void *data1, unsigned int size1,
		const void *data2, unsigned int size2)
{
	struct dstrm_buffer *buffer;
	void *write_pointer;
	int totalsize = size1 + size2;
	int tmp;

	if (d->cache_size == 0) {
		/** buffering is disabled for this datastream */
		km_mutex_lock(&d->logging_thread->write_lock);
		__logging_thread_write(d->logging_thread, data1, size1);
		__logging_thread_write(d->logging_thread, data2, size2);
		km_mutex_unlock(&d->logging_thread->write_lock);
		return;
	}

tryagain:
	/* This could block if the buffer management thread is working
	 * on our cache */
	buffer = buffer_queue_dequeue(&d->cache);

	if (!buffer) {
		/* if we get here, that means that the buffer management
		 * thread has failed to keep up, and the datastream's cache of
		 * ready buffers is exhausted. we have to call
		 * fill_datastream_cache in the application's context, which
		 * is potentially very expensive if the pool requires expansion */
		tmp = __sync_add_and_fetch(&d->block_counter, 1);
		fill_datastream_cache(d->pool, &d->cache, 1);
		goto tryagain;
	}

	if (buffer_tailroom(buffer) < totalsize) {
		// This could block if the logging thread is busy.
		if (d->mode == STREAM_CIRCULAR_MODE) {
			/* we are in 'logic analyzer mode', and are acting
			 * as a circular ringbuffer. so take this full
			 * buffer and put it at the end of our cache.
			 * then take the front of the cache and erase it. */

			buffer_queue_enqueue(&d->cache, buffer);
			buffer_queue_reset_front(&d->cache);
		} else {
			/* we are in 'normal' mode, which means that new buffers
			 * get handed off to the logging thread */
			buffer_queue_enqueue(&d->logging_thread->queue, buffer);
		}
		goto tryagain;
	}

	write_pointer = buffer_put(buffer, totalsize);

	memcpy(write_pointer, data1, size1);

	// copy the second chunk of data
	if (size2) {  // do we need this check?
		write_pointer += size1;
		memcpy(write_pointer, data2, size2);
	}

	buffer_queue_push(&d->cache, buffer);
}


