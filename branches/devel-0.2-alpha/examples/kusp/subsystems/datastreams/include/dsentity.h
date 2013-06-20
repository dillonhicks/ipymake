#ifndef ENTITY_H
#define ENTITY_H

#ifdef __KERNEL__
#include <asm/timex.h>
#else
#include <misc.h>
#endif

/*
 * Datastream Special Event Types
 */
enum {
	DS_EDC_TYPE = 0,
	DS_RESERVED_OFFSET
};

enum {
	DS_EVENT_TYPE = 0,
	DS_COUNTER_TYPE,
	DS_OBJECT_TYPE,
	DS_HISTOGRAM_TYPE,
	DS_INTERVAL_TYPE,
	DS_TYPE_COUNT
};

struct ds_ns_fragment {
	char group[48];
	char name[48];
	char desc[48];
	char info[48];
	unsigned int type;
	unsigned int id;
};

struct ds_event_record {
	cycles_t time_stamp;
	unsigned int seq;
	unsigned int id;
	unsigned int event_tag;
	/* FIXME.J - does PID take up 32 bits. If not, what can be done with the remainder */
	unsigned int pid;
	int data_len;
};

struct ds_extra_data_chunk {
	struct ds_event_record evt;
	unsigned int owner_seq;
	unsigned int owner_cid;
	unsigned int seq;
	unsigned int total_len;
	unsigned int data_len;
};

struct ds_interval_record {
	unsigned int id;
	cycles_t start_time;
};

struct ds_counter_record {
	unsigned int id;
	int count;
	cycles_t first_update;
	cycles_t last_update;
};

struct ds_active_histogram {
	unsigned int id;

	unsigned int num_buckets;
	int tune_amount;
	long long upperbound;
	long long lowerbound;
	long long range;

	long long min; //6
	long long max;
	int num_events;
	long long sum_events;

	cycles_t first_update; //10
	cycles_t last_update;

	unsigned int underflow; // 12
	unsigned int *hist_array;
	unsigned int overflow;

	long long *tune_history;

//	unsigned int status;
//	cycles_t enter_value;

//	unsigned int num_group_members;
//	int range_flag;
//	int guard_min;
//	int guard_max;
//	int *group_array;
};

struct ds_active_counter {
	unsigned int id;
	int count;
	cycles_t first_update;
	cycles_t last_update;
};

struct ds_active_interval {
	unsigned int id;
	cycles_t start_time;
};

// Configuration datastructures

struct ds_histogram_info {
	long long lowerbound;
	long long upperbound;
	unsigned int buckets;
	unsigned int tune_amount;
};

union ds_entity_info {
	struct ds_histogram_info hist_info;
};

#endif /* ENTITY_H */
