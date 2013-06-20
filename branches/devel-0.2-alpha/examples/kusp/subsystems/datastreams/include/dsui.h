#ifndef DSUI_H
#define DSUI_H

#include <signal.h>

#include <dsentity.h>
#include <dslist.h>
#include <configfile.h>

/* Maximum number of active datastreams. If you change this, you will need to
 * update dsui-header as well. */
#define MAX_DS 9
#define MAX_DS_PRINTF_SIZE 1024
/* Max number of buckets per-histogram */
#define HIST_MAX_BUCKETS 	(65536)
#define HIST_MAX_TUNE		(65536)


typedef char * dsui_log_t;
typedef int dsui_stream_t;
typedef void (*sighandler_t)(int);

enum datastream_mode {
	/// datastream is running
	STREAM_NORMAL_MODE,
	/// datastream is running in ringbuffer mode
	STREAM_CIRCULAR_MODE
};

struct datastream_list;

struct datastream_ip_data {
	const char *group;
	const char *name;
	const char *edf;
	const char *file;
	const char *func;
	int line;
	unsigned int type;
	struct dstrm_list_head list;
	unsigned int id;
	struct datastream_list *next;
	struct datastream_list *ds_array[MAX_DS];
};

struct datastream_ip {
	struct datastream_ip_data *ip;
	struct datastream_list **next;
	unsigned int *id;
} __attribute__((aligned(8)));


/* These two routines set global variables indicating the PID of the DSUI helper
 * threads involved as an aid to properly interpreting the DSUI output and DSKI
 * output related to what threads execute as part of the application.
 */
void set_logging_thread_pid(int pid);
void set_buffer_thread_pid(int pid);

void dsui_start(int *argc, char *** argv, const char *default_filename);
void dsui_cleanup(void);
sighandler_t dsui_signal(int signum, sighandler_t handler);

struct datastream_ip *dsui_get_ip_byname(char *group, char *name);
struct datastream_ip *dsui_create_ip(char *group, char *name,
		int type, char *info);

// datastream operations
dsui_stream_t dsui_open_datastream(dsui_log_t logfile, int cache_size,
		enum datastream_mode mode);
void dsui_close_datastream(dsui_stream_t id);
void dsui_flush_datastream(dsui_stream_t id);
void dsui_snapshot_datastream(dsui_stream_t id);
void dsui_enable_all_ips(dsui_stream_t ds);
int dsui_enable_ip(dsui_stream_t id, struct datastream_ip *ip,
	union ds_entity_info *config_info);
void dsui_disable_ip(dsui_stream_t id, struct datastream_ip *ip);

// output file operations
list_t *get_dsui_output_filenames(void);

dsui_log_t dsui_open_output_socket(char *hostname, int port);
dsui_log_t dsui_open_output_file(char *filename);

// ***** ENTITY LOGGING *****
void dsui_raw_event(dsui_log_t log, int id, int tag, size_t size,
		void *extradata);
void dsui_printf(const char *fmt, ...) __attribute__((format(printf,1,2)));
void dsui_write_time_state(dsui_log_t log);

// EVENTS
void dsui_event_log(const struct datastream_ip *ip, int tag,
		int data_len, const void *data);
void dsui_event_log_single(const struct datastream_ip *ip,
		dsui_stream_t id,
		int tag, int data_len, const void *data);

#define DSTRM_EVENT(gname, ename, tag) \
	DSTRM_EVENT_DATA(gname, ename, tag, 0, NULL, NULL)

#define DSTRM_EVENT_ID(id, gname, ename, tag) \
	DSTRM_EVENT_DATA_ID(id, gname, ename, tag, 0, NULL, NULL)

// COUNTER
void dsui_counter_add(const struct datastream_ip *ip, int amount);
void dsui_counter_add_single(const struct datastream_ip *ip,
		dsui_stream_t id, int amount);
void dsui_counter_log(const struct datastream_ip *ip);
void dsui_counter_log_single(const struct datastream_ip *ip,
		dsui_stream_t id);
void dsui_counter_reset(const struct datastream_ip *ip);
void dsui_counter_reset_single(const struct datastream_ip *ip,
		dsui_stream_t id);

#define DSTRM_EXTERN_COUNTER(gname, ename) \
	const extern struct datastream_ip __datastream_ip_##gname##ename;

#define DSTRM_COUNTER_ADD(gname, ename, amount)	do {				\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_counter_add(&__datastream_ip_##gname##ename,	\
				amount);					\
} while (0)

#define DSTRM_COUNTER_LOG(gname, ename)	do {					\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_counter_log(&__datastream_ip_##gname##ename);	\
} while (0)

#define DSTRM_COUNTER_RESET(gname, ename)	do {				\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_counter_reset(&__datastream_ip_##gname##ename);\
} while (0)

#define DSTRM_COUNTER_ADD_ID(id, gname, ename, amount)	do {				\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_counter_add_single(&__datastream_ip_##gname##ename, (id)\
				amount);					\
} while (0)

#define DSTRM_COUNTER_LOG_ID(id, gname, ename)	do {					\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_counter_log_single(&__datastream_ip_##gname##ename, (id));	\
} while (0)

#define DSTRM_COUNTER_RESET_ID(id, gname, ename)	do {			\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_counter_reset_single(&__datastream_ip_##gname##ename, (id));\
} while (0)

// INTERVAL
void dsui_interval_start(const struct datastream_ip *ip);
void dsui_interval_start_single(const struct datastream_ip *ip,
		dsui_stream_t dstrm_id);
void dsui_interval_end(const struct datastream_ip *ip, int tag);
void dsui_interval_end_single(const struct datastream_ip *ip, int tag,
		dsui_stream_t dstrm_id);

#define DSTRM_EXTERN_INTERVAL(gname, ename) \
	const extern struct datastream_ip __datastream_ip_##gname##ename;


#define DSTRM_INTERVAL_END(gname, ename, tag) do {				\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_interval_end(&__datastream_ip_##gname##ename,\
				tag);						\
} while (0)

#define DSTRM_INTERVAL_START(gname, ename) do {					\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_interval_start(&__datastream_ip_##gname##ename);\
} while (0)

#define DSTRM_INTERVAL_END_ID(id, gname, ename, tag) do {				\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_interval_end_single(&__datastream_ip_##gname##ename, (id)\
				tag);						\
} while (0)

#define DSTRM_INTERVAL_START_ID(id, gname, ename) do {					\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_interval_start_single(&__datastream_ip_##gname##ename, (id));\
} while (0)

// HISTOGRAM
void dsui_histogram_add(const struct datastream_ip *ip, long long amount);
void dsui_histogram_add_single(const struct datastream_ip *ip, dsui_stream_t id,
		long long amount);

void dsui_histogram_reset(const struct datastream_ip *ip);
void dsui_histogram_reset_single(const struct datastream_ip *ip,
		dsui_stream_t id);

void dsui_histogram_log(const struct datastream_ip *ip);
void dsui_histogram_log_single(const struct datastream_ip *ip,
		dsui_stream_t id);

#define DSTRM_EXTERN_HISTOGRAM(gname, ename) \
	const extern struct datastream_ip __datastream_ip_##gname##ename;


#define DSTRM_HISTOGRAM_ADD(gname, ename, amount) do {				\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_histogram_add(&__datastream_ip_##gname##ename,\
				amount);					\
} while (0)

#define DSTRM_HISTOGRAM_LOG(gname, ename) do {					\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_histogram_log(&__datastream_ip_##gname##ename);\
} while (0)

#define DSTRM_HISTOGRAM_RESET(gname, ename) do {				\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_histogram_reset(					\
			&__datastream_ip_##gname##ename);			\
} while (0)

#define DSTRM_HISTOGRAM_ADD_ID(id, gname, ename, amount) do {				\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_histogram_add_single(&__datastream_ip_##gname##ename, (id)\
				amount);					\
} while (0)

#define DSTRM_HISTOGRAM_LOG_ID(id, gname, ename) do {					\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_histogram_log_single(&__datastream_ip_##gname##ename, (id));\
} while (0)

#define DSTRM_HISTOGRAM_RESET_ID(id, gname, ename) do {				\
	if (*__datastream_ip_##gname##ename.next)				\
		dsui_histogram_reset_single(					\
			&__datastream_ip_##gname##ename, (id));			\
} while (0)

// used by constructor function in generated .c files
void dsui_header_check(int current_version, char *prefix);
void dsui_register_ip(struct datastream_ip *ip);


#endif // DSUI_H
