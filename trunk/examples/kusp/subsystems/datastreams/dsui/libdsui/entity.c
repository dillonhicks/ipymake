#include <stdlib.h>


#include "dsui_private.h"
#include <mutex.h>
#include <misc.h>

#include "filters.h"
#include "datastream.h"
#include "dsentity.h"


// XXX: The DSKI equivalent of this function is *much* more elegant
// but I am too busy to rewrite this right now; it gets the job done
void __event_log(struct datastream *d,
		struct ds_event_record *evt, int data_len, const void *data)
{
	struct logging_thread *log;
	int totalsize;
	int tmp;

	if (!apply_filters(d, d->pre_filters, evt)) {
		return;
	}

	// XXX no way to get PID without making expensive system call =(
	evt->pid = 0;

	log = d->logging_thread;

	// Atomic increments, using GCC builtins. The tmp variable
	// avoids an 'unused value' warning
	evt->seq = __sync_add_and_fetch(&log->entity_count, 1);
	tmp = __sync_add_and_fetch(&d->log_count, 1);
	evt->data_len = data_len;

	totalsize = sizeof(*evt) + data_len;

	if (totalsize > d->pool->max_size) {
		/* If we get here, then event + its extra data
		 * won't fit in a single buffer, and we need
		 * to break it up. */
		struct ds_extra_data_chunk edc;
		int max_size;
		int i;
		int written = 0;
		int total_seq;

		// DSTRM_ADMIN_FAM/DATA_CHUNK
		edc.evt.id = 15;
		edc.owner_seq = evt->seq;
		edc.owner_cid = evt->id;
		edc.evt.event_tag = 0;
		edc.evt.time_stamp = 0;

		/* each edc knows the size of the obj its contributing to */
		edc.total_len = data_len;

		max_size = d->pool->max_size - sizeof(edc);

		total_seq = data_len / max_size;
		if (data_len % max_size) {
			total_seq++;
		}

		/* log the extra data as admin events broken up into
		 * buffer-sized chunks */
		for (i=0; i < total_seq; i++) {
			const void *data_start = data + (i * max_size);
			edc.seq = i;

			if (i != (total_seq - 1)) {
				edc.data_len = max_size;
			} else {
				edc.data_len = (data_len - written);
			}
			written += edc.data_len;
			edc.evt.data_len = edc.data_len + (sizeof(edc) - sizeof(edc.evt));
			datastream_log(d, &edc, sizeof(edc), data_start, edc.data_len);
		}

		/* log the offending event without extra data. postprocess
		 * will cache the data chunks (indexing them by sequence number)
		 *
		 * Postprocess is designed to handle chunks that are out of order, and
		 * may appear later in the datastream than the event itself, which can
		 * happen due to concurrent access to datastream_log */
		evt->data_len = -1;
		datastream_log(d, evt, sizeof(*evt), NULL, 0);
	} else {
		datastream_log(d, evt, sizeof(*evt),
			data, data_len);
	}

	/* Some streams are in a special 'ringbuffer' mode. Events
	 * logged to this stream are placed in a ringbuffer and not
	 * automatically sent to the logging thread. Instead, we wait
	 * for an event to match certain trigger conditions.
	 *
	 * NOTE: At the moment, runtime filtering is unimplemented.
	 * Instead, the user should put datastream_flush calls
	 * directly in their code when the triggering condition is met */
	if (d->mode == STREAM_CIRCULAR_MODE) {
		if (apply_filters(d, d->trigger_filters, evt)) {
			datastream_flush(d);
		}
	}
}


// ************** COUNTER *****************************************

int counter_init(const struct datastream_ip_data *ip,
		struct active_entity *entity, union ds_entity_info *einfo)
{
	struct ds_active_counter *counter;

	counter = malloc(sizeof(*counter));
	if (!counter)
		return -ENOMEM;
	memset(counter, 0, sizeof(*counter));

	counter->id = ip->id;
	entity->entity.counter = counter;
	return 0;
}

void counter_add(struct datastream_list *entity_instance, int amount)
{
	struct ds_active_counter *c;
	km_mutex_lock(&entity_instance->entity.lock);

	c = entity_instance->entity.entity.counter;
	c->last_update = get_tsc();
	if (!c->count)
		c->first_update = c->last_update;
	c->count += amount;

	km_mutex_unlock(&entity_instance->entity.lock);
}

void counter_log(struct datastream_list *entity_instance)
{
	struct ds_active_counter *counter;

	struct ds_event_record evt = {
		.data_len = sizeof(*counter),
		.event_tag = 0,
		.time_stamp = get_tsc(),
		.id = 0
	};

	counter = entity_instance->entity.entity.counter;
	km_mutex_lock(&entity_instance->entity.lock);
	__event_log(entity_instance->datastream, &evt, sizeof(*counter), counter);
	km_mutex_unlock(&entity_instance->entity.lock);
}

void counter_reset(struct datastream_list *entity_instance)
{
	km_mutex_lock(&entity_instance->entity.lock);
	entity_instance->entity.entity.counter->count = 0;
	km_mutex_unlock(&entity_instance->entity.lock);
}


// ********** INTERVAL **********************

int interval_init(const struct datastream_ip_data *ip,
		struct active_entity *entity, union ds_entity_info *einfo)
{
	struct ds_active_interval *interval;

	interval = malloc(sizeof(*interval));
	if (!interval)
		return -ENOMEM;
	memset(interval, 0, sizeof(*interval));

	interval->id = ip->id;
	entity->entity.interval = interval;
	return 0;
}



void interval_start(struct datastream_list *entity_instance)
{
	km_mutex_lock(&entity_instance->entity.lock);
	entity_instance->entity.entity.interval->start_time = get_tsc();
	km_mutex_unlock(&entity_instance->entity.lock);
}


void interval_end(struct datastream_list *entity_instance, int tag)
{
	struct ds_interval_record ir;

	struct ds_event_record evt = {
		.data_len = sizeof(ir),
		.event_tag = tag,
		.time_stamp = get_tsc(),
		.id = 8
	};
	struct ds_active_interval *interval = entity_instance->entity.entity.interval;

	km_mutex_lock(&entity_instance->entity.lock);
	ir.id = interval->id;
	ir.start_time = interval->start_time;
	__event_log(entity_instance->datastream, &evt, sizeof(ir), &ir);
	km_mutex_unlock(&entity_instance->entity.lock);
}

// ******* HISTOGRAM **************************************************


void histogram_free(struct ds_active_histogram *hist)
{
	free(hist->tune_history);
	free(hist);
}

static inline void __incr_bucket(struct ds_active_histogram *hist,
		long long amount)
{
	long long offset = amount - hist->lowerbound;
	int bucket_num;

	offset = offset / hist->range;
	bucket_num = offset;

	if (bucket_num < 0) {
		hist->underflow++;
	} else if (bucket_num >= hist->num_buckets) {
		hist->overflow++;
	} else {
		hist->hist_array[bucket_num]++;
	}
}

static inline void __set_bounds(struct ds_active_histogram *hist,
		long long lowerbound, long long upperbound)
{
	hist->lowerbound = lowerbound;
	hist->range = (upperbound - lowerbound);
	hist->range = hist->range / hist->num_buckets;
	hist->range++;
	hist->upperbound = lowerbound + hist->range * hist->num_buckets;
}


int histogram_configure(const struct datastream_ip_data *ip,
		struct active_entity *entity, union ds_entity_info *einfo)
{
	struct ds_active_histogram *hist, *oldhist;
	unsigned int num_buckets, tune_amount;
	long long lowerbound, upperbound;
	struct ds_histogram_info *config = &einfo->hist_info;

	if (config) {
		num_buckets = config->buckets;
		tune_amount = config->tune_amount;
		lowerbound = config->lowerbound;
		upperbound = config->upperbound;
	} else {
		/* defaults */
		num_buckets = 30;
		tune_amount = 5000;
		lowerbound = 0;
		upperbound = 1;
	}

	if (num_buckets < 0 || tune_amount < 0 || upperbound <= lowerbound ||
			num_buckets > HIST_MAX_BUCKETS ||
			tune_amount > HIST_MAX_TUNE)
		return -EINVAL;

	hist = malloc(sizeof(*hist) + num_buckets * sizeof(unsigned int));
	if (!hist)
		return -ENOMEM;
	memset(hist, 0, sizeof(*hist) + num_buckets * sizeof(unsigned int));

	/*
	 * kzalloc sets results in this being null. fast-paths use this pointer
	 * and expect it to be null or valid, only (emphasis).
	 */
	hist->tune_history = NULL;

	if (tune_amount) {
		hist->tune_history = calloc(tune_amount, sizeof(long long));

		if (!hist->tune_history) {
			free(hist);
			return -ENOMEM;
		}
	}

	hist->num_buckets = num_buckets;
	hist->tune_amount = tune_amount;
	hist->hist_array = (unsigned int*)&hist[1];
	hist->id = ip->id;

	if (hist->tune_amount == 0)
		__set_bounds(hist, lowerbound, upperbound);

	oldhist = entity->entity.histogram;
	entity->entity.histogram = hist;

	if (oldhist) {
		histogram_free(oldhist);
	}

	return 0;
}


int histogram_init(const struct datastream_ip_data *ip,
		struct active_entity *entity, union ds_entity_info *einfo)
{
	return histogram_configure(ip, entity, einfo);
}



void histogram_add(struct datastream_list *entity_instance,
		long long amount)
{
	struct ds_active_histogram *hist = entity_instance->entity.entity.histogram;
	km_mutex_lock(&entity_instance->entity.lock);

	hist->last_update = get_tsc();

	if (hist->num_events == 0) {
		hist->first_update = hist->last_update;
		hist->max = hist->min = amount;
	}

	hist->max = max(amount, hist->max);
	hist->min = min(amount, hist->min);
	hist->num_events++;
	hist->sum_events += amount;

	/* are we still in tuning phase */
	if (hist->tune_history) {
		/* save as temp history */
		hist->tune_history[hist->num_events-1] = amount;
		if (hist->num_events == hist->tune_amount) {
			/* FIXME: Don't do this here! Defer until
			 * histogram_log */
			int i;

			__set_bounds(hist, hist->min, hist->max + 1);
			/* save the history now */
			for (i = 0; i < hist->num_events; i++)
				__incr_bucket(hist, hist->tune_history[i]);

			free(hist->tune_history);
			hist->tune_history = NULL;
		}
	} else
		__incr_bucket(hist, amount);

	km_mutex_unlock(&entity_instance->entity.lock);

}


void histogram_reset(struct datastream_list *entity_instance)
{
	struct ds_active_histogram *hist;
	hist = entity_instance->entity.entity.histogram;

	km_mutex_lock(&entity_instance->entity.lock);

	hist->overflow = hist->underflow = 0;
	hist->sum_events = 0;
	hist->num_events = 0;
	memset(hist->hist_array, 0, sizeof(int) * hist->num_buckets);

	km_mutex_unlock(&entity_instance->entity.lock);

}


void histogram_log(struct datastream_list *entity_instance) {
	struct ds_event_record evt = {
		.time_stamp = get_tsc(),
		.event_tag = 0,
		.id = 1
	};
	struct ds_active_histogram *hist;
	struct datastream *d = entity_instance->datastream;

	hist = entity_instance->entity.entity.histogram;
	km_mutex_lock(&entity_instance->entity.lock);

	evt.data_len = sizeof(*hist) + hist->num_buckets * sizeof(int);

	if (hist->tune_history) {
		int i;

		/* set bounds based on what we currently know */
		__set_bounds(hist, hist->min, hist->max + 1);

		/* use whatever we have */
		for (i = 0; i < hist->num_events; i++)
			__incr_bucket(hist, hist->tune_history[i]);

		/* log and reset */
		__event_log(d, &evt, evt.data_len, hist);
		memset(hist->hist_array, 0, hist->num_buckets * sizeof(int));
	} else
		__event_log(d, &evt, evt.data_len, hist);

	km_mutex_unlock(&entity_instance->entity.lock);
}

