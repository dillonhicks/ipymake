#include <linux/list.h>
#include <linux/fs.h>
#include <linux/relay.h>
#include <asm/semaphore.h>

#include <datastreams/dski.h>
#include <datastreams/entity.h>

#ifdef CONFIG_DSKI_DEFERRED
#include <linux/workqueue.h>
#include <linux/ccsm.h>

/*
 * =======================================
 *       Deferred Work Structures
 * =======================================
 */

#define DSKI_WORK_BUFFER_SIZE 25


#define DSKI_DEFER_CCSM_ADD	0x1		/* Indicates work unit of type CCSM_ADD (CCSM set addition) */
#define DSKI_DEFER_CCSM_REMOVE	0x2		/* Indicates work unit of type CCSM_REMOVE (CCSM set removal) */


/* Deferred work structure holding min. necessary info for a ccsm add
 * instruction */
struct dski_defer_ccsm_add {
	char name[DS_STR_LEN];			/* name of set to be added to */
	char new_name[DS_STR_LEN];		/* name of new singleton set */
	void *handle;				/* handle to structure being added */
	int type;				/* CCSM type of structure being added */
};

/* Deferred work structure holding min. necessary info for a ccsm remove
 * instruction */
struct dski_defer_ccsm_remove {
	char *name;				/* name of set to be removed */
};

/* Union of all deferred work structures */
union dski_work_data {
	struct dski_defer_ccsm_add ccsm_add;
	struct dski_defer_ccsm_remove ccsm_remove;
};


/* Represents a unit of deferred work */
struct dski_work_unit {
	/* DSKI EVENT DATA */
	cycles_t time_stamp;			/* timestamp of original event */
	unsigned int seq;			/* sequence number of original event */
	unsigned int id;			/* id of original event */
	unsigned int tag;			/* tag value of original event */
	unsigned int pid;			/* pid of thread logging original event */

	struct list_head data_entry;		/* entry on the deferred data list of work units */

	/* DEFERRED WORK DATA */
	union dski_work_data work_data;		/* union of possible data necessary for deferred execution */
	unsigned int work_type;			/* type of desired deferred execution */
};


/* Data passed as single argument to the deferred work structure */
struct dski_deferred_data {
	struct list_head work_units;		/* List of deferred work units to be executed */
	struct work_struct dski_deferred;	/* DSKI deferred work structure */
						/* Need others? */
};

void dski_deferred_function(struct work_struct *work);	/* Deferred work function for our work queue */

extern struct dski_work_unit dski_deferred_work_buffer[];
extern struct dski_deferred_data deferred_data;

#endif /* CONFIG_DSKI_DEFERRED */

/* Minimum data fragment size when splitting data to log */
#define MIN_EDC			(1)

/* mutex protects mostly RCU writers */
extern struct semaphore dski_mutex;

/*
 * struct dstrm_user - context for a DSKI user
 *
 * A struct dstrm_user is created when a user opens the DSKI device node. It
 * organizes data for this user, and provides isolation from other users.
 *
 * @name:
 * @dir:
 * @datastreams:	list of user's datastreams
 * @mutex:		controls membership in the datastreams and channels sets
 * @channels:		channels created by user
 * @num_channels:	number of channels (for generating ids)
 */
struct dstrm_user {
	char *name;
	struct dentry *dir;
	struct list_head datastreams;
	struct semaphore mutex;
	struct list_head channels;
	int num_channels;
};

/*
 * struct dstrm_channel - datastream sink
 *
 * @flags		Either DS_CHAN_TRIG or DS_CHAN_CONT
 *                      DS_CHAN_TRIG is the 'ringbuffer' mode
 * @list		member of a user's list of open channels
 * @timer		(NOT USED) expiration timer
 * @user		user context
 * @r_chan		relayfs channel
 * @dir			directory entry in debugfs
 * @channel_id		channel id (for all channels opened by user)
 *
 * @seq:		per-channel seq number
 * @edc_writes:		num edc's written
 * @edc_bytes:		total edc bytes logged
 * @bufswitchfail:	failed buffer switches
 * @max_data_len:	max extra data size
 */
struct dstrm_channel {
	unsigned int flags;
	struct list_head list;
	struct timer_list timer;
	struct dstrm_user *user;
	struct rchan *r_chan;
	struct dentry *dir;
	int channel_id;

	unsigned long long seq[NR_CPUS];
	atomic_t edc_writes;
	size_t edc_bytes;
	atomic_t bufswitchfail;
	int max_data_len;
};

/*
 * struct datastream - configuration
 *
 * A datastream represents a particular configuration of available entities on
 * the system. Datastreams are per-user. Datastreams can be configured
 * independtly of other datastreams and independently of other users
 *
 * @flags:	DS_DSTRM_ON
 * 		Flag used for explicit checking of whether the datastream is
 * 		enabled and collecting events or not.
 * @name:	name of datastream
 * @list:	on per-user list of streams
 * @filters:	active datastream filters
 * @enabled:	enabled entities
 * @d_chan	Datastream channel to log events to
 * @user:	context of owner
 */
struct datastream {
	unsigned long flags;
	char *name;
	struct list_head list;
	struct list_head filters;
	struct list_head enabled;
	struct dstrm_channel *d_chan;
	struct dstrm_user *user;
};


struct active_entity {
#ifdef CONFIG_PREEMPT_RT
	raw_spinlock_t lock;
#else
	spinlock_t lock;
#endif
	union {
		struct ds_active_counter *counter;
		struct ds_active_interval *interval;
		struct ds_active_histogram *histogram;
	} entity;
};

/* FIXME - goes away after markers port ??? 
 * No, probably not. We still need to maintain a list of datastreams for
 * each entity. This will probably be linked from the private data pointer
 * for each marker 
 *
 * This structure is used on two different lists. First, the list rooted in the
 * datastream structure which specifies the set of instrumentation points
 * enabled by a datastream, using the list field. Second, the per-ip list of
 * datastreams enabling an instrumentation point, using the next field.
 */
struct datastream_list {
	const struct datastream_ip *ip;	/* enabled ip of interest to referenced DS */
	struct active_entity entity;	/* persistant data if ip requires it */
	struct list_head list;		/* Entry on per-DS list of enabled ips */
	struct datastream_list *next;	/* Link used for per-ip list of enabling DSs */
	struct datastream *datastream;  /* DS enabling reference ip */
};

int channel_open(struct dstrm_user *user, size_t bufsize,
	size_t nbufs, int timeout, unsigned int flags);
int channel_close(struct dstrm_user *user, int channel_id);
int channel_flush(struct dstrm_user *user, int channel_id);
int __channel_close(struct dstrm_user *user, struct dstrm_channel *d_chan);


struct datastream *find_datastream(struct dstrm_user *user, char *name);

int apply_filters(struct datastream *d, struct ds_event_record *evt, int data_len, const void* data);
int destroy_filters(struct datastream *d);
int create_filter(struct dstrm_user *user, char *dstrm, char *name, union dski_ioc_filter_ctrl_params *params);

void __entity_disable(struct datastream *d, const struct datastream_ip *ip);
int entity_disable(struct dstrm_user *user, char *name, unsigned int id);
int entity_configure(struct dstrm_user *user, char *name, unsigned int id, union ds_entity_info *config_info);
int entity_enable(struct dstrm_user *user, char *name, unsigned int id, union ds_entity_info *config_info);

void counter_add(const struct datastream_ip *ip, int amount);
void counter_log(const struct datastream_ip *ip);
void counter_reset(const struct datastream_ip *ip);
void interval_start(const struct datastream_ip *ip);
void interval_end(const struct datastream_ip *ip, int tag);
void histogram_add(const struct datastream_ip *ip, long long amount);
void histogram_reset(const struct datastream_ip *ip);
void histogram_log(const struct datastream_ip *ip);
void event_log(const struct datastream_ip *ip, int tag,	int data_len, const void *data);
void user_data_log(const struct datastream_ip *ip, int tag, int data_len, const void *data);

void __internal_event_log(struct datastream *d, int event_type, int tag);

// Traceme Active Filter Functions.
int dscvr_filter_c_func(struct datastream *d, void **data,union dski_ioc_filter_ctrl_params *params);
int dscvr_filter_f_func(struct datastream *d, struct ds_event_record *evt,void *data, int data_len, const void *extra_data);
void dscvr_filter_d_func(struct datastream *d, void *data);

// System Monitor Active filter functions.
int smonitor_f_func(struct datastream *d, struct ds_event_record *evt,void *data, int data_len, const void *extra_data);
int smonitor_c_func(struct datastream *d, void **data, union dski_ioc_filter_ctrl_params *params);
void smonitor_d_func(struct datastream *d, void *data);

// Daemon Trace Active filter functions.
int dtrace_f_func(struct datastream *d, struct ds_event_record *evt, void *data, int data_len, const void *extra_data);
int dtrace_c_func(struct datastream*d, void **data, union dski_ioc_filter_ctrl_params *params);
void dtrace_d_func(struct datastream *d, void *data);

// Daemon Trace Active filter functions.
int taskfilter_f_func(struct datastream *d, struct ds_event_record *evt, void *data, int data_len, const void *extra_data);
int taskfilter_c_func(struct datastream*d, void **data, union dski_ioc_filter_ctrl_params *params);
void taskfilter_d_func(struct datastream *d, void *data);

// CCSM Traceme Active Filter Functions.
int traceme_c_func(struct datastream *d, void **data,union dski_ioc_filter_ctrl_params *params);
int traceme_f_func(struct datastream *d, struct ds_event_record *evt,void *data, int data_len, const void *extra_data);
void traceme_d_func(struct datastream *d, void *data);

// proc filesystem utility functions.
int create_proc_file(char *name);
int write_to_procfile(int pid);
int remove_proc_file(char *name);

struct datastream_list *datastream_list_remove(struct datastream_list **list, struct datastream *d);
int __datastream_destroy(struct dstrm_user *user, struct datastream *d);

void histogram_log_closing(struct datastream *d, const struct datastream_ip *ip);
