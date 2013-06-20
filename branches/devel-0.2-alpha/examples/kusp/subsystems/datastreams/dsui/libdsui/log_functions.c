#include "dsui_private.h"
#include <dsui.h>
#include "entity.h"
#include <mutex.h>
#include <stdio.h>
#include <stdarg.h>
#include <config.h>

#if 0
#include "libdsui_dsui.h"
#endif

#ifdef DSUI_CALIBRATION
#error WHAT THE FUCK
DSTRM_HISTOGRAM_DECL(DSUI_CALIB, EVENT_LOG);
#endif


// Public interface to entity logging, which are a bridge to the private
// functions in entity.c
extern struct datastream_ip __datastream_ip_DSTREAM_ADMIN_FAMPRINTF;

/*
 * Accessed via DSTRM_PRINTF
 * Logs the __datastream_ip_DSTREAM_ADMIN_FAMPRINTF ip with
 * the resultant output of passing fmt, ... to a sprintf
 * attached as extra data
 */
void dsui_printf(const char *fmt, ...)
{
	int n;
	char buf[MAX_DS_PRINTF_SIZE];

	va_list ap;
	va_start(ap, fmt);
	n = vsnprintf (buf, MAX_DS_PRINTF_SIZE - 1, fmt, ap);
	va_end(ap);

	if (*__datastream_ip_DSTREAM_ADMIN_FAMPRINTF.next) \
                dsui_event_log(&__datastream_ip_DSTREAM_ADMIN_FAMPRINTF, \
                                0, n, buf);
}

void dsui_event_log(const struct datastream_ip *ip, int tag,
		int data_len, const void *data)
{
	struct ds_event_record evt;
	struct datastream_list *next;

#ifdef DSUI_CALIBRATION
	unsigned long long tsc = get_tsc();
#endif

	evt.data_len = data_len;
	evt.time_stamp = get_tsc();
	evt.event_tag = tag;
	evt.id = *ip->id;

	km_rdwr_rlock(&dsui_rwlock);

	next = *ip->next;
	while (next) {
		__event_log(next->datastream, &evt, data_len, data);
		next = next->next;
	}

	km_rdwr_runlock(&dsui_rwlock);

#ifdef DSUI_CALIBRATION
	tsc = get_tsc() - tsc;
	if (data_len == 0) {
		/* We only record events with no extra data */
		DSTRM_HISTOGRAM_ADD(DSUI_CALIB, EVENT_LOG, tsc);
	}
#endif

}

void dsui_event_log_single(const struct datastream_ip *ip, dsui_stream_t id,
		int tag, int data_len, const void *data)
{
	struct ds_event_record evt;
	struct datastream_list *next;

	evt.data_len = data_len;
	evt.time_stamp = get_tsc();
	evt.event_tag = tag;
	evt.id = *ip->id;

	km_rdwr_rlock(&dsui_rwlock);

	next = ip->ip->ds_array[id];
	if (next) __event_log(next->datastream,  &evt, data_len, data);

	km_rdwr_runlock(&dsui_rwlock);
}



void dsui_histogram_log(const struct datastream_ip *ip)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = *ip->next;
	while (next) {
		histogram_log(next);
		next = next->next;
	}
	km_rdwr_runlock(&dsui_rwlock);
}


void dsui_histogram_log_single(const struct datastream_ip *ip, dsui_stream_t id)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = ip->ip->ds_array[id];
	if (next) histogram_log(next);

	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_histogram_reset(const struct datastream_ip *ip)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = *ip->next;
	while (next) {
		histogram_reset(next);
		next = next->next;
	}
	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_histogram_reset_single(const struct datastream_ip *ip, dsui_stream_t id)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = ip->ip->ds_array[id];
	if (next) histogram_reset(next);

	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_histogram_add(const struct datastream_ip *ip, long long amount)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = *ip->next;
	while (next) {
		histogram_add(next, amount);
		next = next->next;
	}
	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_histogram_add_single(const struct datastream_ip *ip, dsui_stream_t id,
		long long amount)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = ip->ip->ds_array[id];
	if (next) histogram_add(next, amount);

	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_interval_end_single(const struct datastream_ip *ip, int tag,
		int dstrm_id)
{
	struct datastream_list *dl;

	km_rdwr_rlock(&dsui_rwlock);

	dl = ip->ip->ds_array[dstrm_id];
	if (dl) interval_end(dl, tag);

	km_rdwr_rlock(&dsui_rwlock);
}

void dsui_interval_end(const struct datastream_ip *ip, int tag)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = *ip->next;
	while (next) {
		interval_end(next, tag);
		next = next->next;
	}
	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_interval_start(const struct datastream_ip *ip)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = *ip->next;
	while (next) {
		interval_start(next);
		next = next->next;
	}
	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_interval_start_single(const struct datastream_ip *ip, int dstrm_id)
{
	struct datastream_list *dl;

	km_rdwr_rlock(&dsui_rwlock);
	dl = ip->ip->ds_array[dstrm_id];

	if (dl) interval_start(dl);

	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_counter_add(const struct datastream_ip *ip, int amount)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = *ip->next;
	while (next) {
		counter_add(next, amount);
		next = next->next;
	}

	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_counter_add_single(const struct datastream_ip *ip,
		dsui_stream_t id, int amount)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = ip->ip->ds_array[id];
	if (next) counter_add(next, amount);

	km_rdwr_runlock(&dsui_rwlock);
}


void dsui_counter_log(const struct datastream_ip *ip)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = *ip->next;
	while (next) {
		counter_log(next);
		next = next->next;
	}
	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_counter_log_single(const struct datastream_ip *ip,
		dsui_stream_t id)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = ip->ip->ds_array[id];
	if (next) counter_log(next);

	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_counter_reset(const struct datastream_ip *ip)
{

	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = *ip->next;
	while (next) {
		counter_reset(next);
		next = next->next;
	}

	km_rdwr_runlock(&dsui_rwlock);
}

void dsui_counter_reset_single(const struct datastream_ip *ip,
		dsui_stream_t id)
{
	struct datastream_list *next;

	km_rdwr_rlock(&dsui_rwlock);

	next = ip->ip->ds_array[id];
	if (next) counter_reset(next);

	km_rdwr_runlock(&dsui_rwlock);
}

