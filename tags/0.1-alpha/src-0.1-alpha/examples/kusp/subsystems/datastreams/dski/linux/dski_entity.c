#include <linux/spinlock.h>
#include <linux/rcupdate.h>
#include <linux/limits.h>
#include <linux/dski.h>
#include <datastreams/entity.h>
#include <datastreams/dski.h>
#include "dski_common.h"

#define HIST_MAX_BUCKETS 	(200)

/*
 * relay_buffer_write - write mem regions to channel with no checking
 *
 * @buf:	buffer to write to
 * @d1, @s1:	data and size of first chunk
 * @d2, @s2:	data and size of second chunk
 */
static void relay_buffer_write(struct rchan_buf *buf, const void *data1,
		size_t size1, const void *data2, size_t size2)
{
	memcpy(buf->data + buf->offset, data1, size1);
	buf->offset += size1;
	memcpy(buf->data + buf->offset, data2, size2);
	buf->offset += size2;
	BUG_ON(buf->offset > buf->chan->subbuf_size);
}

#ifdef CONFIG_DSKI_DEFERRED

/* Statically allocated pool of deferred work units */
struct dski_work_unit dski_deferred_work_buffer[DSKI_WORK_BUFFER_SIZE];

/* Used to track remaining buffer size */
static int dski_work_buffer_remaining = DSKI_WORK_BUFFER_SIZE;

struct dski_deferred_data deferred_data;

/* Returns a pointer to a statically allocated work_unit */
static struct dski_work_unit *dski_deferred_work_allocate(void)
{
	struct dski_work_unit *unit;

	if (dski_work_buffer_remaining) {
		--dski_work_buffer_remaining;
		unit = &dski_deferred_work_buffer[dski_work_buffer_remaining];
	}

	return unit;
}

/* Frees a statically allocated work_unit for future use */
static void dski_deferred_work_return(struct dski_work_unit *unit)
{
	list_del(&unit->data_entry);
	dski_work_buffer_remaining++;
}

/* The body defining the actions taken by our DSKI deferred work queue */
void dski_deferred_function(struct work_struct *work)
{
	struct dski_deferred_data *data = container_of(work, struct dski_deferred_data, dski_deferred);
	struct dski_work_unit *next;
	struct list_head *cur, *tmp;

	/* For each deferred work unit */
	list_for_each_safe_rcu(cur, tmp, &data->work_units) {

		next = container_of(cur, struct dski_work_unit, data_entry);

		switch(next->work_type) {
		case DSKI_DEFER_CCSM_ADD:
			/* access unique data */
			/* perform action */
			/* if action failure, log error event */
			break;
		case DSKI_DEFER_CCSM_REMOVE:
			/* access unique data */
			/* perform action */
			/* if action failure, log error event */
			break;
		default:
			/* log error event */
			break;
		}

		/* if no error? */
			/* Log a new event, including the timestamp of the causal event as extra
			 * data.
			 */
	}

	return;
}

#endif /* CONFIG_DSKI_DEFERRED */

#ifdef CONFIG_DSKI_DEBUG
/*
 * @d:		pointer to the DS structure from which we can reference channel
 * 		and buffer
 * @event_type:	type of internal event we are logging
 * @tag_val:	tag value, if provided
 */
void __internal_event_log(struct datastream *d, int event_type,	int tag_value)
{
	struct ds_event_record	internal_event;
	struct dstrm_channel	*current_channel;

	struct rchan		*rfs_channel;
	struct rchan_buf	*rfs_buffer;

	size_t			event_size;
	unsigned long		flags;

	/*
	 * For this initial version of internal datastreams, there is no extra
	 * data, so we will only be writing out a chunk of data of event_size.
	 */
	event_size = sizeof(struct ds_event_record);

	/*
	 * Find the relay_fs channel into which we are planning to write it.
	 * Return if the channel doesn't exist.
	 */
	current_channel = d->d_chan;
	rfs_channel = current_channel ? rcu_dereference(current_channel->r_chan) : NULL;
	if (unlikely(!rfs_channel)) {
		return;
	}

	/* 
	 * Disable local interrupts to interact with the Relay Buffer under the
	 * possibility that we are in an RCU read critical section. Disabling
	 * local interrupts will prevent us from conditionally blocking when we
	 * attempt to write to the buffer
	 */
	local_irq_save(flags);

	/*
	 * Fill in a temporary event record which will store our data in the
	 * proper format to be copied into the output Relay File System buffer.
	 *
	 * FIXME.J - To lower overhead, this should be a statically allocated strucutre.
	 * Where should this structure end up?
	 */
	internal_event.id		= event_type;
	internal_event.event_tag	= tag_value;
	internal_event.time_stamp	= get_cycles();
	internal_event.seq		= ++current_channel->seq[smp_processor_id()];
	internal_event.pid		= current->pid;

	/* Buffer for the currently executing CPU */
	rfs_buffer = rfs_channel->buf[smp_processor_id()];

	/* Check to see if the event will fit in the current buffer or not. */
	if (rfs_buffer->offset + event_size > rfs_buffer->chan->subbuf_size) {
		/* 
		 * If it will not fit, just switch to an empty buffer rather
		 * than attempting to divide up a single event between the
		 * remaining space in the current buffer and some space in the
		 * next.
		 */
		if (!relay_switch_subbuf(rfs_buffer, event_size)) {
			atomic_inc(&current_channel->bufswitchfail);
			goto out;
		}
	}

	memcpy(rfs_buffer->data + rfs_buffer->offset, &internal_event, event_size);
	rfs_buffer->offset += event_size;
	BUG_ON(rfs_buffer->offset > rfs_buffer->chan->subbuf_size);

out:
	local_irq_restore(flags);
}
#endif/*CONFIG_DSKI_DEBUG*/

/*
 * __event_log - log event & split extra data into smaller chunks
 * 
 * @d:		pointer to the DS structure from which we can reference channel
 * 		and buffer
 * @evt:	event we are logging
 * @data_len:	size of extra data
 * @data:	extra data
 */
static void __event_log(struct datastream *d, struct ds_event_record *evt,
		int data_len, const void *data)
{
	size_t totalsize;
	struct dstrm_channel *d_chan;
	struct rchan *chan;
	struct rchan_buf *buf;
	unsigned long flags;
	int ret_val;

	/*
	 * Check if this datastream is enabled before attempting to log any
	 * data. If not, return to skip this datastream.
	 */
	if (!test_bit(DS_DSTRM_ON, &d->flags)) {
		return;
	}

	/*
	 * Determine the total size of the event being logged and find the
	 * relay_fs channel into which we are planning to write it. return if
	 * the channel doesn't exist.
	 */
	totalsize = sizeof(*evt) + data_len;
	d_chan = d->d_chan;
	chan = d_chan ? rcu_dereference(d_chan->r_chan) : NULL;

	if (unlikely(!chan)) {
		/* FIXME.J - 
		 *
		 * Need a form of error return, consider use of internal
		 * datastreams, which would work fine from this context as we
		 * have already determined the datastream whose output channel
		 * we can write to.
		 *
		 * ex.
		 * 	DSTRM_INTERNAL_ERROR(d, ERROR_TAG_VALUE);
		 *
		 * Note that this return statement appears to be necessary for
		 * the machine not to lock up, and may be related to the order
		 * in which a Datastream is setup, associated with a channel,
		 * and has a set of events enabled. Implementation of the on/off
		 * for a Datastream permitting configuration of the datastream
		 * while logging is off may eliminate the lock-up scenario.
		 *
		 * Note that the above internal error was intended for use with
		 * a proposed DSKI system datastream that would narrate
		 * datastream subsystem conditions and events in general.
		 *
		 * Consider writing some internal ERROR values unique to
		 * datastreams context that we can push into internal
		 * datastreams to be read in post-processing.
		 */
		return;
	}

	ret_val = apply_filters(d,evt,data_len,data);
	if (ret_val == FLTR_REJECT) {
		/*
		 * The event has been rejected. By returning here it won't be
		 * logged. Note that all of the above information is in the
		 * calling threads context, and thus does not need to be
		 * deallocated
		 */
		return;
	}

	/* disable local interrupts */
	local_irq_save(flags);
	
	/* Sequence for this channel */
	evt->seq = ++d_chan->seq[smp_processor_id()];

	evt->pid = current->pid;

	/* Buffer for this cpu */
	buf = chan->buf[smp_processor_id()];
	d_chan->max_data_len = max(data_len, d_chan->max_data_len);

	/*
	 * Now, decide if a single write of event and extra data will be
	 * satisfactory, or if multiple writes to the relay_fs buffer will be
	 * required.
	 */
	if (unlikely(totalsize > buf->chan->subbuf_size)) {
		/* Must split up because data is bigger than any single buffer */
		goto split;
	}

	if (buf->offset + totalsize <= buf->chan->subbuf_size) {
		/* Can fit everything in the remaining free space in the buffer */
		relay_buffer_write(buf, evt, sizeof(*evt), data, data_len);
		goto out;
	}

	/*
	 * More than one write will be required. This algorithm for splitting up
	 * the data will use the remaining space in the current buffer before
	 * switching to the new buffer. 
	 *
	 * ? - Note that we could have switched buffers
	 * here and checked to see if we could fit in the empty buffer, but the
	 * overhead of the extra data chunk is still small
	 */

split:

	/*
	 * when data_len is zero we'll fall through and try to log the event and
	 * possibly request a new buffer
	 */

	while (data_len) {
	
		/* 
		 * FIXME.J - this structure is on the stack and not static thus
		 * the edc.seq member is likely reinitialized each iteration of the
		 * loop. Check that this exists across each iteration of the
		 * loop so that we are actually incrementing edc.seq.
		 *
		 * Consider declaring struct as local variable of the routine
		 * and initializing .seq outside the loop, along with loop
		 * invariants.
		 */
		struct ds_extra_data_chunk edc = {
			.evt.time_stamp = 0,
			.evt.event_tag = 0,
			.evt.id = 15,
			.owner_seq = evt->seq,
			.owner_cid = evt->id,
			.total_len = data_len,
			.seq = 0,
		};

		/*
		 * Each extra data chunk is a struct typeof(edc) that describes
		 * and identifies the extra data, plus the extra data. Check to
		 * see we have available the user-specified minimum amount of
		 * space for extra data. If not, try and switch buffers
		 */
		if (buf->offset + sizeof(edc) + MIN_EDC > buf->chan->subbuf_size)
			if (!relay_switch_subbuf(buf, sizeof(edc) + MIN_EDC)) {
				/*
				 * Switching buffers failed, we note this and
				 * abandon the effor to log the data 
				 */
				atomic_inc(&d_chan->bufswitchfail);
				goto out;
			}

		/*
		 * We have enough room for a struct edc and the minimum amount
		 * of extra data. Now calculate the maximum space for data
		 * remaining in the buffer. If this is more than we need
		 * then use the required amount.
		 */
		edc.data_len = (buf->chan->subbuf_size - buf->offset) - sizeof(edc);
		if (data_len < edc.data_len)
			edc.data_len = data_len;

		/*
		 * An extra data event is placed at the beginning of a edc.
		 * Caculate its data_len such that PP will read the remainder of
		 * the edc & the extra data and the event's "extra data"
		 */
		edc.evt.data_len = edc.data_len + (sizeof(edc) - sizeof(edc.evt));
		relay_buffer_write(buf, &edc, sizeof(edc), data, edc.data_len);

		atomic_inc(&d_chan->edc_writes);
		d_chan->edc_bytes += edc.data_len;

		/* update: sequence, amount remaining, data pointer */
		data_len -= edc.data_len;
		data += edc.data_len;

		/* 
		 * FIXME.J - this is currently stupid/wasted because the edc
		 * struct is re-allocated on the stack and reinitialized with
		 * each iteration of the loop
		 */
		edc.seq++;
	}

	/*
	 * Checking to see if the event whose extra data we just oupout will fit
	 * in the current buffer or not. If this event is lost, then the extra
	 * data chunks already output are meaningless to post-processing.
	 */
	if (buf->offset + sizeof(*evt) > buf->chan->subbuf_size) {
		/* 
		 * Need to switch to the next buffer. If switch fails, indicate
		 * failure and exit without logging event.
		 */
		if (!relay_switch_subbuf(buf, sizeof(*evt))) {
			atomic_inc(&d_chan->bufswitchfail);
			goto out;
		}
	}

	/*
	 * Log the event w/ the large extra data. modify its data_len to be
	 * zero, as post-processing will find it in the events logged above. evt
	 * is left unmodified because other channels may have different buffer
	 * sizes and not need to split the extra data. 
	 *
	 * FIXME.J - Note that this is not using relay_buffer_write. The only
	 * reason we can think of at the moment is because it is setting the
	 * extra data length of the event written into the buffer to -1, leaving
	 * the local copy unchanged. Why this is important, we are unsure.
	 */
	memcpy(buf->data + buf->offset, evt, sizeof(*evt));
	((struct ds_event_record *)(buf->data + buf->offset))->data_len = -1;
	buf->offset += sizeof(*evt);

out:
	local_irq_restore(flags);
}

void string_log(const struct datastream_ip *ip, const char *fmt, ...)
{
	unsigned long flags;
	va_list args;
	int cpu, len;
	static char buffer[NR_CPUS][1024];
	
	va_start(args, fmt);

	local_irq_save(flags);
	cpu = smp_processor_id();
	
	len = vscnprintf(buffer[cpu], sizeof(buffer)/NR_CPUS, fmt, args);
	event_log(ip, 0, sizeof(char)*len, buffer[cpu]);

	local_irq_restore(flags);
	va_end(args);
}

void event_log(const struct datastream_ip *ip, int tag,
		int data_len, const void *data)
{
	struct ds_event_record evt;
	struct datastream_list *next;

	evt.data_len = data_len;
	evt.time_stamp = get_cycles();
	evt.event_tag = tag;
	evt.id = (unsigned int)ip;
	/* FIXME.J -
	 *    should be:
	 *    evt.id = (unsigned int)ip->id;
	 */

	rcu_read_lock();

	next = rcu_dereference(*ip->next);
	while (next) {
		__event_log(next->datastream, &evt, data_len, data);
		next = rcu_dereference(next->next);
	}

	rcu_read_unlock();
}

/*
 * A method of creating an event which specifies a set of extra data which is
 * currently stored in the address of the current process. Thus, udata is a user
 * address. An example use would be an event in sys_write which could grab a
 * copy of the data being written.
 */
void user_data_log(const struct datastream_ip *ip, int tag,
		int data_len, const void *udata)
{
	struct ds_event_record evt;
	struct datastream_list *next;
	void *kbuf;

	evt.data_len = data_len;
	evt.time_stamp = get_cycles();
	evt.event_tag = tag;
	evt.id = (unsigned int)ip;

	kbuf = kmalloc(data_len, GFP_KERNEL);
	if (!kbuf) {
		printk(KERN_CRIT "Datastreams: Out of memory in user_data_log\n");
		return;
	}
	if (copy_from_user(kbuf, udata, data_len)) {
		kfree(kbuf);
		printk(KERN_CRIT "Datastreams: copy_from_user failed in user_data_log\n");
		return;
	}
	
	rcu_read_lock();

	next = rcu_dereference(*ip->next);
	while (next) {
		__event_log(next->datastream, &evt, data_len, kbuf);
		next = rcu_dereference(next->next);
	}

	rcu_read_unlock();
	kfree(kbuf);
}

void counter_add(const struct datastream_ip *ip, int amount)
{
	struct datastream_list *next;
	unsigned long flags;

	rcu_read_lock();
	
	next = rcu_dereference(*ip->next);
	while (next) {
		struct ds_active_counter *c;
		spin_lock_irqsave(&next->entity.lock, flags);
		
		c = next->entity.entity.counter;
		c->last_update = get_cycles();
		if (!c->count) 
			c->first_update = c->last_update;
		c->count += amount;

		spin_unlock_irqrestore(&next->entity.lock, flags);
		next = rcu_dereference(next->next);
	}
	rcu_read_unlock();
}

void counter_log(const struct datastream_ip *ip)
{
	unsigned long flags;
	struct datastream_list *next;
	struct ds_active_counter *counter;

	struct ds_event_record evt = {
		.data_len = sizeof(*counter),
		.event_tag = 0,
		.time_stamp = get_cycles(),
		.id = 0
	};

	rcu_read_lock();

	next = rcu_dereference(*ip->next);
	while (next) {
		counter = next->entity.entity.counter;
		spin_lock_irqsave(&next->entity.lock, flags);
		__event_log(next->datastream, &evt, sizeof(*counter), counter);
		spin_unlock_irqrestore(&next->entity.lock, flags);
		next = rcu_dereference(next->next);
	}
	rcu_read_unlock();
}

void counter_reset(const struct datastream_ip *ip)
{

	struct datastream_list *next;
	unsigned long flags;

	rcu_read_lock();
	
	next = rcu_dereference(*ip->next);
	while (next) {
		spin_lock_irqsave(&next->entity.lock, flags);
		next->entity.entity.counter->count = 0;
		spin_unlock_irqrestore(&next->entity.lock, flags);
		next = rcu_dereference(next->next);
	}
	rcu_read_unlock();
}

void interval_start(const struct datastream_ip *ip)
{
	struct datastream_list *next;
	unsigned long flags;

	rcu_read_lock();
	
	next = rcu_dereference(*ip->next);
	while (next) {
		spin_lock_irqsave(&next->entity.lock, flags);
		next->entity.entity.interval->start_time = get_cycles();
		spin_unlock_irqrestore(&next->entity.lock, flags);
		next = rcu_dereference(next->next);
	}
	rcu_read_unlock();
}

void interval_end(const struct datastream_ip *ip, int tag)
{
	unsigned long flags;
	struct datastream_list *next;
	struct ds_interval_record ir;
	struct ds_active_interval *interval;

	struct ds_event_record evt = {
		.data_len = sizeof(ir),
		.event_tag = tag,
		.time_stamp = get_cycles(),
		.id = 8
	};

	rcu_read_lock();
	
	next = rcu_dereference(*ip->next);
	while (next) {
		interval = next->entity.entity.interval;
		spin_lock_irqsave(&next->entity.lock, flags);
		ir.id = interval->id;
		ir.start_time = interval->start_time;
		__event_log(next->datastream, &evt, sizeof(ir), &ir);
		spin_unlock_irqrestore(&next->entity.lock, flags);
		next = rcu_dereference(next->next);
	}
	rcu_read_unlock();
}

static inline void __incr_bucket(struct ds_active_histogram *hist,
		long long amount)
{
	long long offset = amount - hist->lowerbound;
	/*
	 * FIXME.64 - it appears that buck_num exists to be a 32 bit value for
	 * comparison to hist->num_buckets. Will work correctly as is for
	 * 64-bit? Our guess is that ints are 64 bits and so while superfluous
	 * would be 64 bit and 32 bit safe.
	 */
	int bucket_num;

	/* 
	 * FIXME.J - obviously range is the size of each bucket and so
	 * bucket_size is probably a more apt name
	 */
	do_div(offset, hist->range);
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
#ifdef DSTRM_HISTRANGE
	long long remainder;
#endif

	hist->lowerbound = lowerbound;
	hist->range = (upperbound - lowerbound);
#ifdef DSTRM_HISTRANGE
	remainder = do_div(hist->range, hist->num_buckets);
#else
	do_div(hist->range, hist->num_buckets);
#endif
	/* 
	 * FIXME.J - need to view result of the above do_div and then determine
	 * why we felt it was neccessary to increment this value. It appears
	 * that range is in fact the size of the bucket and so adding one to it
	 * makes no apparent sense. Perhaps added to account for less-than
	 * num_buckets range of the whole histogram, but note that it is
	 * incremented in all cases, and is incorrect.
	 */
#ifdef DSTRM_HISTRANGE
	if (remainder != 0) {
		hist->range++;
	}
# else
	hist->range++;
#endif
	hist->upperbound = lowerbound + hist->range * hist->num_buckets;
}

static void __histogram_add(struct ds_active_histogram *hist,
		long long amount)
{
	hist->last_update = get_cycles();
	
	if (unlikely(hist->num_events == 0)) {
		hist->first_update = hist->last_update;
		hist->max = hist->min = amount;
	}

	hist->max = max(amount, hist->max);
	hist->min = min(amount, hist->min);
	hist->num_events++;
	hist->sum_events += amount;
	
	/* are we still in tuning phase */
	if (unlikely(hist->tune_history)) {
		/* save as temp history */
		hist->tune_history[hist->num_events-1] = amount;
		if (hist->num_events == hist->tune_amount) {
			int i;

			__set_bounds(hist, hist->min, hist->max + 1);
			/* save the history now */
			for (i = 0; i < hist->num_events; i++)
				__incr_bucket(hist, hist->tune_history[i]);

#if 0
			/* FIXME.J: no sleeping with preempt disabled, which is
			 * done in the calling context of this routine when we
			 * call spinlock_irq_save. (and would be a problem even
			 * without this protection, as we could be calling this
			 * from any context).
			 *
			 * Note that this is a reason why we need the ability to
			 * defer some datastream actions to a safe DS tasklet
			 * context which would be told to free the histogram
			 * tune_history data.
			 */
			kfree(hist->tune_history);
#endif
			hist->tune_history = NULL;
		}
	} else
		__incr_bucket(hist, amount);
}

void histogram_add(const struct datastream_ip *ip, long long amount)
{
	struct datastream_list *next;
	struct ds_active_histogram *hist;
	unsigned long flags;

	rcu_read_lock();

	next = rcu_dereference(*ip->next);
	while (next) {
		hist = next->entity.entity.histogram;
		spin_lock_irqsave(&next->entity.lock, flags);

		__histogram_add(hist, amount);

		spin_unlock_irqrestore(&next->entity.lock, flags);
		next = rcu_dereference(next->next);
	}
	rcu_read_unlock();
}

static inline void __histogram_reset(struct ds_active_histogram *hist)
{
	hist->overflow = 0;
	hist->underflow = 0;
	hist->sum_events = 0;
	hist->num_events = 0;
	memset(hist->hist_array, 0, sizeof(int) * hist->num_buckets);
}

void histogram_reset(const struct datastream_ip *ip)
{
	struct datastream_list *next;
	struct ds_active_histogram *hist;
	unsigned long flags;

	rcu_read_lock();

	next = rcu_dereference(*ip->next);
	while (next) {
		hist = next->entity.entity.histogram;
		spin_lock_irqsave(&next->entity.lock, flags);

		__histogram_reset(hist);

		spin_unlock_irqrestore(&next->entity.lock, flags);
		next = rcu_dereference(next->next);
	}
	rcu_read_unlock();
}


static void __histogram_log(struct datastream *d,
		struct ds_event_record *evt, struct ds_active_histogram *hist)
{
	if (unlikely(hist->tune_history)) {
		/* 
		 * FIXME.J -
		 * If we are trying to taking a snapshot of the histogram while
		 * it is still being tuned, we have to take special action. Note
		 * that this assumes the non-NULL value of tune_history
		 * indicates that tuning is still taking place. This is not a
		 * sufficient test because freeing the tune_history needs to be
		 * a deferred action and is currently a memory leak because this
		 * pointer is simply set to NULL in __histogram_add.
		 */ 
		int i;

		/* set bounds based on what we currently know */
		__set_bounds(hist, hist->min, hist->max + 1);

		/* use whatever we have */
		for (i = 0; i < hist->num_events; i++)
			__incr_bucket(hist, hist->tune_history[i]);

		/*
		 * FIXME.J- resetting the contents of the histogram to zero
		 * seems dumb. Unless after reflection we can think of a reason
		 * for it, we should take it out.
		 */
		__event_log(d, evt, evt->data_len, hist);
		memset(hist->hist_array, 0, hist->num_buckets * sizeof(int));
	} else
		__event_log(d, evt, evt->data_len, hist);
}

void histogram_log(const struct datastream_ip *ip)
{
	struct datastream_list *next;
	struct ds_active_histogram *hist;
	unsigned long flags;

	struct ds_event_record evt = {
		.time_stamp = get_cycles(),
		.event_tag = 0,
		.id = 1
	};

	rcu_read_lock();

	next = rcu_dereference(*ip->next);
	while (next) {
		hist = next->entity.entity.histogram;
		spin_lock_irqsave(&next->entity.lock, flags);

		/* 
		 * FIXME.64 - should histogram buckets be 64 or 32 bits for space
		 * saving sake and if 32 on a 64 bit architecture, what would be
		 * the best method of making it happen.
		 */
		evt.data_len = sizeof(*hist) + hist->num_buckets * sizeof(int);
		__histogram_log(next->datastream, &evt, hist);

		spin_unlock_irqrestore(&next->entity.lock, flags);
		next = rcu_dereference(next->next);
	}
	rcu_read_unlock();
}

void histogram_log_closing(struct datastream *d, const struct datastream_ip *ip)
{
	struct datastream_list *next;
	struct ds_active_histogram *hist;
	unsigned long flags;

	struct ds_event_record evt = {
		.time_stamp = get_cycles(),
		.event_tag = 0,
		.id = 1
	};

	rcu_read_lock();

	next = rcu_dereference(*ip->next);
	while (next) {
		hist = next->entity.entity.histogram;
		spin_lock_irqsave(&next->entity.lock, flags);
		if (next->datastream == d) {
			evt.data_len = sizeof(*hist) + hist->num_buckets * sizeof(int);
			__histogram_log(next->datastream, &evt, hist);
		}
		spin_unlock_irqrestore(&next->entity.lock, flags);
		next = rcu_dereference(next->next);
	}
	rcu_read_unlock();
}

/*
 * counter_init - initialize a counter entity for logging
 *
 * @d:		associated datastream
 * @ent:	associated active entity
 * @fid:	family id
 * @eid:	entity id
 *
 * Allocates and initializes an counter structure
 */
static int counter_init(const struct datastream_ip *ip,
		struct active_entity *entity, union ds_entity_info *einfo)
{
	struct ds_active_counter *counter;

	counter = kzalloc(sizeof(*counter), GFP_KERNEL);
	if (!counter)
		return -ENOMEM;

	counter->id = (unsigned int)ip;
	entity->entity.counter = counter;
	return 0;
}

/*
 * interval_init - initialize an interval entity for logging
 *
 * @d:		associated datastream
 * @ent:	associated active entity
 * @fid:	family id
 * @eid:	entity id
 *
 * Allocates and initializes an interval structure
 */
static int interval_init(const struct datastream_ip *ip,
		struct active_entity *entity, union ds_entity_info *einfo)
{
	struct ds_active_interval *interval;

	interval = kzalloc(sizeof(*interval), GFP_KERNEL);
	if (!interval)
		return -ENOMEM;

	interval->id = (unsigned int)ip;
	entity->entity.interval = interval;
	return 0;
}

static void histogram_free(struct ds_active_histogram *hist)
{
	/*
	 * FIXME.J - memory leak! We are failing to deallocate the hist_array.
	 */
	kfree(hist->tune_history);
	kfree(hist);
}

static void entity_free(const struct datastream_ip *ip, struct datastream *d,
		struct active_entity *entity)
{
	switch (ip->ip->type) {
 	case DS_HISTOGRAM_TYPE:
		BUG_ON(!entity->entity.histogram);
		histogram_free(entity->entity.histogram);
		break;
 
 	case DS_EVENT_TYPE:
		return;
 
 	case DS_COUNTER_TYPE:
		BUG_ON(!entity->entity.counter);
		kfree(entity->entity.counter);
		break;
 	
 	case DS_INTERVAL_TYPE:
		BUG_ON(!entity->entity.interval);
		kfree(entity->entity.interval);
 		break;
 
 	default:
		BUG_ON(1);
 	}
}

static void entity_prepare_free(const struct datastream_ip *ip, struct datastream *d)
{
	switch (ip->ip->type) {
 	case DS_HISTOGRAM_TYPE:
		histogram_log_closing(d, ip);
		break;
 
 	case DS_EVENT_TYPE:
		break;
 
 	case DS_COUNTER_TYPE:
		break;
 	
 	case DS_INTERVAL_TYPE:
 		break;
 
 	default:
		BUG_ON(1);
 	}
}

static int histogram_configure(const struct datastream_ip *ip,
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
		num_buckets = 20;
		tune_amount = 50;
		lowerbound = 0;
		upperbound = 1;
	}

	if (num_buckets < 0 || tune_amount < 0 || upperbound <= lowerbound ||
			num_buckets > HIST_MAX_BUCKETS ||
			tune_amount > HIST_MAX_BUCKETS)
		return -EINVAL;

	hist = kzalloc(sizeof(*hist) + num_buckets * sizeof(unsigned int), 
			GFP_KERNEL);
	if (!hist)
		return -ENOMEM;

	/*
	 * kzalloc sets results in this being null. fast-paths use this pointer
	 * and expect it to be null or valid, only (emphasis).
	 */
	hist->tune_history = NULL;

	if (tune_amount) {
		hist->tune_history = kzalloc(
			tune_amount * sizeof(long long), GFP_KERNEL);

		if (!hist->tune_history) {
			kfree(hist);
			return -ENOMEM;
		}
	}

	hist->num_buckets = num_buckets;
	hist->tune_amount = tune_amount;
	hist->hist_array = (unsigned int*)&hist[1];
	hist->id = (unsigned int)ip;

	if (hist->tune_amount == 0)
		__set_bounds(hist, lowerbound, upperbound);

	oldhist = entity->entity.histogram;
	entity->entity.histogram = hist;

	if (oldhist) {
		synchronize_rcu();
		histogram_free(oldhist);
	}

	return 0;
}

/* __entity_disable - disable an entity
 *
 * @d:		datastream to disable the entity within
 * @dlh:	datastream list head
 *
 * Removes /the/ matching datastream from the given list, thereby disabling an
 * entity for the datastream, as no log point can read this datastream through
 * the particular entity's log point associated with the list given
 */
void __entity_disable(struct datastream *d, const struct datastream_ip *ip)
{
	struct datastream_list *next;

	entity_prepare_free(ip, d);

	/* find matching datastream_list. uniqueness is enforced */
	next = datastream_list_remove(ip->next, d);
	if (!next)
		return;

	synchronize_rcu();
	entity_free(ip, d, &next->entity);
	list_del(&next->list);
	kfree(next);
	printk("dski (%s): disable entity [%s/%s:%u]\n", d->user->name,
			ip->ip->group, ip->ip->name, (unsigned int)ip);
}

/*
 * entity_disable - disable an entity
 *
 * @d:		datastream to disable the entity within
 * @cid:	composite id of the entity
 */
int entity_disable(struct dstrm_user *user, char *name, unsigned int id)
{
	const struct datastream_ip *ip;
	struct datastream *d;

	d = find_datastream(user, name);
	if (!d)
		return -EINVAL;

	ip = find_ip_by_id(id);
	if (!ip)
		return -EINVAL;

	__entity_disable(d, ip);
	return 0;
}

int entity_configure(struct dstrm_user *user, char *name,
		unsigned int id, union ds_entity_info *config_info)
{
	const struct datastream_ip *ip;
	struct datastream_list *link;
	struct datastream *d;
	int ret;

	d = find_datastream(user, name);
	if (!d)
		return -EINVAL;

	ip = find_ip_by_id(id);
	if (!ip)
		return -EINVAL;

	down(&dski_mutex);

	link = *ip->next;
	while (link) {
		if (link->datastream == d)
			break;
		link = link->next;
	}

	ret = -EINVAL;
	if (!link)
		goto out;

	switch (ip->ip->type) {
	case DS_HISTOGRAM_TYPE:
		ret = histogram_configure(ip, &link->entity, config_info);
		break;

	case DS_EVENT_TYPE:
	case DS_COUNTER_TYPE:
	case DS_INTERVAL_TYPE:
		ret = 0;
		break;

	default:
		ret = -ENOENT;
	}

out:
	up(&dski_mutex);
	return ret;
}

/*
 * histogram_init - prepare a datastream for use
 *
 * @d:		datastream logging to this histogram
 * @ent:	active entity structure for this histogram
 * @fid:	family id
 * @eid:	entity id
 */
static int histogram_init(const struct datastream_ip *ip,
		struct active_entity *entity, union ds_entity_info *einfo)
{
	return histogram_configure(ip, entity, einfo);
}

/*
 * entity_init - entity specific initialization
 *
 * @dlist:	datastream list link associated w/ entity
 * @etype:	type of entity
 * @fid:	family id
 * @eid:	entity id
 * @
 */
static int entity_init(const struct datastream_ip *ip, struct datastream *d,
		struct active_entity *entity, union ds_entity_info *config_info)
{
	memset(entity, 0, sizeof(*entity));
	spin_lock_init(&entity->lock);

	switch (ip->ip->type) {
	case DS_EVENT_TYPE:
		return 0;

	case DS_HISTOGRAM_TYPE:
		return histogram_init(ip, entity, config_info);

	case DS_COUNTER_TYPE:
		return counter_init(ip, entity, config_info);

	case DS_INTERVAL_TYPE:
		return interval_init(ip, entity, config_info);

	default:
		return -ENOENT;
	}
}

/*
 * datastream_entity_enable - enable an entity
 *
 * @d:		datastream to enable the entity within
 * @cid:	composite id of the entity to enable
 *
 * Returns 0 on success, else negative error value
 */
int entity_enable(struct dstrm_user *user, char *name,
		unsigned int id, union ds_entity_info *config_info)
{
	const struct datastream_ip *ip;
	struct datastream_list *link;
	struct datastream *d;
	int ret;

	d = find_datastream(user, name);
	if (!d)
		return -EINVAL;

	ip = find_ip_by_id(id);
	if (!ip)
		return -EINVAL;
	
	down(&dski_mutex);

	ret = -EBUSY;
	link = *ip->next;
	while (link) {
		if (link->datastream == d)
			goto out;
		link = link->next;
	}

	ret = -ENOMEM;
	link = kmalloc(sizeof(*link), GFP_KERNEL);
	if (!link)
		goto out;
	/* entity type specific init */
	ret = entity_init(ip, d, &link->entity, config_info);
	if (ret) {
		kfree(link);
		goto out;
	}

	/* link into chain */
	link->datastream = d;
	link->ip = ip;
	link->next = *ip->next;
	*ip->next = link;
	list_add(&link->list, &d->enabled);
	printk("dski (%s): enable entity [%s/%s:%u]\n", user->name,
			ip->ip->group, ip->ip->name, (unsigned int)id);

out:
	up(&dski_mutex);
	return ret;
}
