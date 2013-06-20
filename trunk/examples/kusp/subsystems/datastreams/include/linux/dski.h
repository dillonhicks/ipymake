#ifndef DSKI_H
#define DSKI_H

#ifdef CONFIG_DSKI

#ifdef CONFIG_DSKI_DEBUG
#define DSKI_DEBUG(fmt, args...) printk("DSKI(%s@%d): " fmt, __func__, __LINE__, ## args);	
#else
#define DSKI_DEBUG(fmt, args...)
#endif


enum {
	DSKI_EVENT_TYPE = 0,
	DSKI_COUNTER_TYPE,
	DSKI_OBJECT_TYPE,
	DSKI_HISTOGRAM_TYPE,
	DSKI_INTERVAL_TYPE,
	DSKI_TRIGGER_TYPE,
	DSKI_INTERNAL_ERROR_TYPE,
	DSKI_INTERNAL_EVENT_TYPE
};

struct datastream_list;

/*
 * Note that the Datastream instrumentation point structure is divided into two
 * sections. datastream_ip which exists in the special section and is of
 * constant size, so that we may have an iterable table of IPs and
 * __datastream_ip which exists in standard kernel memory is of dynamic size
 * because of the necessity of using char* to store the name strings.
 */

struct __datastream_ip {
	const char *group;
	const char *name;
	const char *edf;
	const char *file;
	const char *func;
	int line;
	unsigned int type;
	struct list_head list_entry;	/* Entry on list of all IPs */
#ifdef CONFIG_DSKI_HASH_TABLE
	struct list_head table_entry;	/* Entry on hash table of all IPs */
#endif
	unsigned int id;		/* Unique ID (address of associated datastream_ip struct) */
	struct datastream_list *next; 	/* Set of DSs enabling this IP */
};

struct datastream_ip {
	struct __datastream_ip *ip;
	struct datastream_list **next;
};

#ifdef CONFIG_DSKI_HASH_TABLE
#define DSKI_TABLE_SIZE 100

/* The global family name IP table */
extern struct list_head dski_ips_table[DSKI_TABLE_SIZE];
//extern struct list_head **dski_ips_table;
#endif

extern struct list_head dski_ips_list;
extern struct mutex dski_ips_lock;

extern void dski_update_list(void);
extern const struct datastream_ip *find_ip_by_id(unsigned int id);
extern const struct datastream_ip *find_ip_by_name(char* fname, char* ename);
extern unsigned int get_deid_by_name(char* fname, char* ename);

struct datastream_hooks {
	void (*ds_event_log)(const struct datastream_ip *ip,
			int tag, int data_len, const void *data);
#ifdef CONFIG_DSKI_DEBUG
	void (*ds_internal_event_log)(const struct datastream_ip *ip,
			int tag, int data_len, const void *data);
#endif
        void (*ds_string_log)(const struct datastream_ip *ip, int tag, const char *fmt, ...);
	void (*ds_counter_add)(const struct datastream_ip *ip, int amount);
	void (*ds_counter_log)(const struct datastream_ip *ip);
	void (*ds_counter_reset)(const struct datastream_ip *ip);
	void (*ds_interval_start)(const struct datastream_ip *ip);
	void (*ds_interval_end)(const struct datastream_ip *ip, int tag);
	void (*ds_histogram_add)(const struct datastream_ip *ip, long long amount);
	void (*ds_histogram_log)(const struct datastream_ip *ip);
	void (*ds_histogram_reset)(const struct datastream_ip *ip);
	void (*ds_user_data_log)(const struct datastream_ip *ip,
			int tag, int data_len, const void *data);
};

extern struct datastream_hooks dskihooks;


#ifdef CONFIG_DSKI_CTXT

#include <linux/preempt.h>
#include <linux/hardirq.h>

#define dski_in_interrupt()	(irq_count())			/* returns level of nested interrupts */
#define dski_in_hardirq()	(hardirq_count() || (current->flags & PF_HARDIRQ))	/* returns level of nested hardware interrupts only */
#define dski_in_softirq()	(softirq_count() || (current->flags & PF_SOFTIRQ))	/* returns level of nested software interrupts only */

#define dski_preempt_disabled()	(preempt_count() != 0)		/* returns true if preemption disabled */
#define dski_irqs_disabled()	(irqs_disabled())		/* returns true if local interrupts disabled */

/*
 * Returns true only when preemption is enabled and the calling context is not
 * inerrupt context. This is useful, as any possibly blocking call, such as
 * those involving memory management or attempting to grab a local semaphore,
 * are not safe to call from interrupt context. Similarly, a blocking call
 * should not be made with preemption disabled. If the thread blocks, then it
 * will remain CPU bound until it unblocks, preventing other threads from
 * running and possibly locking the CPU. 
 */
#define dski_safe_context()	(irq_count() == 0 && !dski_preempt_disabled())

#endif /*CONFIG_DSKI_CTXT*/

#ifdef CONFIG_DSKI_DEBUG
/*
 * Datastream Event intended for use as internal error reporting inside of Active Filters
 *
 * - currently need a datastream pointer to access some set of output channels.
 *   How to get around this?
 *
 *   - fine for use inside of active filters, where we the datastream is part of
 *     the provided context
 *
 *   - how to use outside of active filters? may not be possible in current
 *   environment, will need a method to determine output channels to write to
 */
#ifdef BALA_NOT_USED
#define DSTRM_INTERNAL_ERROR(datastream, tag) { __internal_event_log(datastream, DSKI_INTERNAL_ERROR_TYPE, tag); }
#endif


/*
 * Datastream Event intended for general use inside of Active Filters
 * An entry is created into the Global DSKI Instrumentation Point list.
 *
 * FIXME.J - is it useful to be able to generate a new event under the namespace
 * pair of an existing event?
 *
 *  - if so, will need to access global DSKI hash table to find unique ID of
 *    existing event
 */
#define DSTRM_INTERNAL_EVENT_DATA(gname, ename, tag, data_len, data, edfname) do {			\
	static const char __datastream_ip_group_##gname[] = #gname;		\
	static const char __datastream_ip_name_##ename[] = #ename;		\
	static struct __datastream_ip __datastream_ip_data_##gname##ename =	\
	{									\
		.group	= __datastream_ip_group_##gname,			\
		.name	= __datastream_ip_name_##ename,				\
		.edf	= edfname,						\
		.next	= NULL,							\
		.type   = DSKI_INTERNAL_EVENT_TYPE,					\
		.line	= __LINE__,						\
		.file	= __FILE__,						\
		.func	= __func__,						\
	};									\
	static const struct datastream_ip __datastream_ip_##gname##ename	\
	__attribute__((section("__datastream_ips"))) =				\
	{									\
		.ip = &__datastream_ip_data_##gname##ename,			\
		.next = &__datastream_ip_data_##gname##ename.next		\
	};									\
	if (*__datastream_ip_##gname##ename.next)				\
		dskihooks.ds_internal_event_log(&__datastream_ip_##gname##ename,	\
				tag, data_len, data);				\
} while (0)

#define DSTRM_INTERNAL_EVENT(gname, ename, tag) \
	DSTRM_INTERNAL_EVENT_DATA(gname, ename, tag, 0, NULL, NULL)

#endif /*CONFIG_DSKI_DEBUG*/

#define DSTRM_EVENT_DATA(gname, ename, tag, data_len, data, edfname) do {	\
	static const char __datastream_ip_group_##gname[] = #gname;		\
	static const char __datastream_ip_name_##ename[] = #ename;		\
	static struct __datastream_ip __datastream_ip_data_##gname##ename =	\
	{									\
		.group	= __datastream_ip_group_##gname,			\
		.name	= __datastream_ip_name_##ename,				\
		.edf	= edfname,						\
		.next	= NULL,							\
		.type   = DSKI_EVENT_TYPE,					\
		.line	= __LINE__,						\
		.file	= __FILE__,						\
		.func	= __func__,						\
	};									\
	static const struct datastream_ip __datastream_ip_##gname##ename	\
	__attribute__((section("__datastream_ips"))) =				\
	{									\
		.ip = &__datastream_ip_data_##gname##ename,			\
		.next = &__datastream_ip_data_##gname##ename.next		\
	};									\
	if (*__datastream_ip_##gname##ename.next)				\
		dskihooks.ds_event_log(&__datastream_ip_##gname##ename,		\
				tag, data_len, data);				\
} while (0)

#define DSTRM_EVENT_PRINTF(gname, ename, tag, fmt, args...) do {		\
	static const char __datastream_ip_group_##gname[] = #gname;		\
	static const char __datastream_ip_name_##ename[] = #ename;		\
	static struct __datastream_ip __datastream_ip_data_##gname##ename =	\
	{									\
		.group	= __datastream_ip_group_##gname,			\
		.name	= __datastream_ip_name_##ename,				\
		.edf	= "print_string",					\
		.next	= NULL,							\
		.type   = DSKI_EVENT_TYPE,					\
		.line	= __LINE__,						\
		.file	= __FILE__,						\
		.func	= __func__,						\
	};									\
	static const struct datastream_ip __datastream_ip_##gname##ename	\
	__attribute__((section("__datastream_ips"))) =				\
	{									\
		.ip = &__datastream_ip_data_##gname##ename,			\
		.next = &__datastream_ip_data_##gname##ename.next		\
	};									\
	if (*__datastream_ip_##gname##ename.next)				\
	  dskihooks.ds_string_log(&__datastream_ip_##gname##ename, tag,	        \
				fmt, ##args);				        \
} while (0)

#define DSTRM_EVENT(gname, ename, tag) \
	DSTRM_EVENT_DATA(gname, ename, tag, 0, NULL, NULL)

#define DSTRM_DEBUG_DECL(gname, ename)                                        \
        static const char __datastream_ip_group_##gname##ename[] = #gname;    \
        static const char __datastream_ip_name_##gname##ename[] = #ename;     \
        static struct __datastream_ip __datastream_ip_data_##gname##ename =   \
	  {                                                                   \
	  .group  = __datastream_ip_group_##gname##ename,                     \
	  .name   = __datastream_ip_name_##gname##ename,                      \
	  .edf    = "print_string",                                           \
	  .next   = NULL,                                                     \
	  .type   = DSKI_EVENT_TYPE,                                          \
	  .line   = __LINE__,                                                 \
	  .file   = __FILE__,                                                 \
	  .func   = "",                                                       \
	  };                                                                  \
        const struct datastream_ip __datastream_ip_##gname##ename             \
        __attribute__((section("__datastream_ips"))) =                        \
        {                                                                     \
	  .ip = &__datastream_ip_data_##gname##ename,                         \
          .next = &__datastream_ip_data_##gname##ename.next                   \
        };  

#ifndef CONFIG_DSKI_PRINTK
#define DSTRM_DEBUG(gname, ename, fmt, args...) do {	                  \
    const extern struct datastream_ip __datastream_ip_##gname##ename; \
    if (*__datastream_ip_##gname##ename.next)				  \
      dskihooks.ds_string_log(&__datastream_ip_##gname##ename, 0,	  \
		   "%s@%d: " fmt, __func__, __LINE__, ## args);           \
  } while (0)
#else
#define DSTRM_DEBUG(gname, ename, fmt, args...) do {                      \
  const extern struct datastream_ip __datastream_ip_##gname##ename;	  \
  if (*__datastream_ip_##gname##ename.next)                               \
    dskihooks.ds_string_log(&__datastream_ip_##gname##ename, 0,		  \
		 "%s@%d: " fmt, __func__, __LINE__, ## args);             \
  printk(#gname "(%s@%d): " fmt, __func__, __LINE__, ## args);		  \
  } while (0)
#endif

#define DSTRM_COUNTER_DECL(gname, ename)					\
	static const char __datastream_ip_group_##gname##ename[] = #gname;	\
	static const char __datastream_ip_name_##gname##ename[] = #ename;	\
	static struct __datastream_ip __datastream_ip_data_cnt_##gname##ename = \
	{									\
		.group	= __datastream_ip_group_##gname##ename,			\
		.name	= __datastream_ip_name_##gname##ename,			\
		.edf	= "",							\
		.next	= NULL,							\
		.type	= DSKI_COUNTER_TYPE,					\
		.line	= __LINE__,						\
		.file	= __FILE__,						\
		.func	= "",							\
	};									\
	const struct datastream_ip __datastream_ip_cnt_##gname##ename		\
	__attribute__((section("__datastream_ips"))) =				\
	{									\
		.ip = &__datastream_ip_data_cnt_##gname##ename,			\
		.next = &__datastream_ip_data_cnt_##gname##ename.next		\
	};									\

#define DSTRM_COUNTER_ADD(gname, ename, amount)	do {				\
	const extern struct datastream_ip __datastream_ip_cnt_##gname##ename;	\
	if (*__datastream_ip_cnt_##gname##ename.next)				\
		dskihooks.ds_counter_add(&__datastream_ip_cnt_##gname##ename,	\
				amount);					\
} while (0)

#define DSTRM_COUNTER_LOG(gname, ename)	do {					\
	const extern struct datastream_ip __datastream_ip_cnt_##gname##ename;	\
	if (*__datastream_ip_cnt_##gname##ename.next)				\
		dskihooks.ds_counter_log(&__datastream_ip_cnt_##gname##ename);	\
} while (0)

#define DSTRM_COUNTER_RESET(gname, ename)	do {				\
	const extern struct datastream_ip __datastream_ip_cnt_##gname##ename;	\
	if (*__datastream_ip_cnt_##gname##ename.next)				\
		dskihooks.ds_counter_reset(&__datastream_ip_cnt_##gname##ename);\
} while (0)

#define DSTRM_INTERVAL_DECL(gname, ename)					\
	static const char __datastream_ip_group_##gname##ename[] = #gname;	\
	static const char __datastream_ip_name_##gname##ename[] = #ename;	\
	static struct __datastream_ip __datastream_ip_data_itrvl_##gname##ename = \
	{									\
		.group	= __datastream_ip_group_##gname##ename,			\
		.name	= __datastream_ip_name_##gname##ename,			\
		.edf	= "",							\
		.next	= NULL,							\
		.type	= DSKI_INTERVAL_TYPE,					\
		.line	= __LINE__,						\
		.file	= __FILE__,						\
		.func	= "",							\
	};									\
	const struct datastream_ip __datastream_ip_itrvl_##gname##ename		\
	__attribute__((section("__datastream_ips"))) =				\
	{									\
		.ip = &__datastream_ip_data_itrvl_##gname##ename,		\
		.next = &__datastream_ip_data_itrvl_##gname##ename.next		\
	};									\

#define DSTRM_INTERVAL_END(gname, ename, tag) do {				\
	const extern struct datastream_ip __datastream_ip_itrvl_##gname##ename;	\
	if (*__datastream_ip_itrvl_##gname##ename.next)				\
		dskihooks.ds_interval_end(&__datastream_ip_itrvl_##gname##ename,\
				tag);						\
} while (0)

#define DSTRM_INTERVAL_START(gname, ename) do {					\
	const extern struct datastream_ip __datastream_ip_itrvl_##gname##ename;	\
	if (*__datastream_ip_itrvl_##gname##ename.next)				\
		dskihooks.ds_interval_start(&__datastream_ip_itrvl_##gname##ename);\
} while (0)



#define DSTRM_HISTOGRAM_DECL(gname, ename)					\
	static const char __datastream_ip_group_##gname##ename[] = #gname;	\
	static const char __datastream_ip_name_##gname##ename[] = #ename;	\
	static struct __datastream_ip __datastream_ip_data_hist_##gname##ename = \
	{									\
		.group	= __datastream_ip_group_##gname##ename,			\
		.name	= __datastream_ip_name_##gname##ename,			\
		.edf	= "",							\
		.next	= NULL,							\
		.type	= DSKI_HISTOGRAM_TYPE,					\
		.line	= __LINE__,						\
		.file	= __FILE__,						\
		.func	= "",							\
	};									\
	const struct datastream_ip __datastream_ip_hist_##gname##ename		\
	__attribute__((section("__datastream_ips"))) =				\
	{									\
		.ip = &__datastream_ip_data_hist_##gname##ename,		\
		.next = &__datastream_ip_data_hist_##gname##ename.next		\
	};									\

#define DSTRM_HISTOGRAM_ADD(gname, ename, amount) do {				\
	const extern struct datastream_ip __datastream_ip_hist_##gname##ename;	\
	if (*__datastream_ip_hist_##gname##ename.next)				\
		dskihooks.ds_histogram_add(&__datastream_ip_hist_##gname##ename,\
				amount);					\
} while (0)

#define DSTRM_HISTOGRAM_LOG(gname, ename) do {					\
	const extern struct datastream_ip __datastream_ip_hist_##gname##ename;	\
	if (*__datastream_ip_hist_##gname##ename.next)				\
		dskihooks.ds_histogram_log(&__datastream_ip_hist_##gname##ename);\
} while (0)

#define DSTRM_HISTOGRAM_RESET(gname, ename) do {				\
	const extern struct datastream_ip __datastream_ip_hist_##gname##ename;	\
	if (*__datastream_ip_hist_##gname##ename.next)				\
		dskihooks.ds_histogram_reset(					\
			&__datastream_ip_hist_##gname##ename);			\
} while (0)

#ifdef DSTRM_NOT_USED
/*
 * This is a definition for a "trigger" event which was an idea that was not
 * implemented beyond this point, but may have a future. The idea was a given
 * event in the kernel might not be created for logging purposes but could be
 * used explicitely as the trigger for a certain condition. It would have been
 * lighter weight than a regular event. Note, however, that with imaginitive use
 * of active filters, a special trigger event like this might not be worth the
 * trouble.
 */
#define DSTRM_TRIGGER(ename) do {						\
	static const char __datastream_ip_name_##ename[] = #ename;		\
	static struct __datastream_ip __datastream_ip_data_TRIGGER##ename =	\
	{									\
		.group	= "TRIGGER",						\
		.name	= __datastream_ip_name_##ename,				\
		.edf	= NULL,							\
		.next	= NULL,							\
		.type   = DSKI_TRIGGER_TYPE,					\
		.line	= __LINE__,						\
		.file	= __FILE__,						\
		.func	= __func__,						\
	};									\
	static const struct datastream_ip __datastream_ip_TRIGGER##ename	\
	__attribute__((section("__datastream_ips"))) =				\
	{									\
		.ip = &__datastream_ip_data_TRIGGER##ename,			\
		.next = &__datastream_ip_data_TRIGGER##ename.next		\
	};									\
	if (*__datastream_ip_TRIGGER##ename.next)				\
		dskihooks.ds_trigger(&__datastream_ip_TRIGGER##ename);		\
} while (0)
#endif

#define DSTRM_USER_DATA(gname, ename, tag, data_len, data, edfname) do {	\
	static const char __datastream_ip_group_##gname[] = #gname;		\
	static const char __datastream_ip_name_##ename[] = #ename;		\
	static struct __datastream_ip __datastream_ip_data_##gname##ename =	\
	{									\
		.group	= __datastream_ip_group_##gname,			\
		.name	= __datastream_ip_name_##ename,				\
		.edf	= edfname,						\
		.next	= NULL,							\
		.type   = DSKI_EVENT_TYPE,					\
		.line	= __LINE__,						\
		.file	= __FILE__,						\
		.func	= __func__,						\
	};									\
	static const struct datastream_ip __datastream_ip_##gname##ename	\
	__attribute__((section("__datastream_ips"))) =				\
	{									\
		.ip = &__datastream_ip_data_##gname##ename,			\
		.next = &__datastream_ip_data_##gname##ename.next		\
	};									\
	if (*__datastream_ip_##gname##ename.next)				\
		dskihooks.ds_user_data_log(&__datastream_ip_##gname##ename,	\
				tag, data_len, data);				\
} while (0)

#else
#define DSTRM_TRIGGER(ename) 
#define DSTRM_HISTOGRAM_RESET(a,b)
#define DSTRM_HISTOGRAM_LOG(gname, ename)
#define DSTRM_HISTOGRAM_ADD(gname, ename, amount)
#define DSTRM_HISTOGRAM_DECL(gname, ename)
#define DSTRM_INTERVAL_START(gname, ename)
#define DSTRM_INTERVAL_END(gname, ename, amount)
#define DSTRM_EVENT_DATA(gname, ename, tag, data_len, data, edfname)
#define DSTRM_INTERNAL_EVENT_DATA(gname, ename, tag, data_len, data, edfname)
#define DSTRM_EVENT(gname, ename, tag)
#define DSTRM_EVENT(gname, ename, tag)
#define DSTRM_EVENT_PRINTF(gname, ename, tag, fmt, args...)
#define DSTRM_DEBUG_DECL(gname, ename)
#define DSTRM_EXTERN_DEBUG(gname, ename)
#define DSTRM_DEBUG(gname, ename, fmt, args...)
#define DSTRM_COUNTER_DECL(gname, ename)
#define DSTRM_COUNTER_ADD(gname, ename, amount)
#define DSTRM_COUNTER_LOG(gname, ename)
#define DSTRM_COUNTER_RESET(gname, ename)
#define DSTRM_INTERVAL_DECL(gname, ename)
#define DSTRM_USER_DATA(gname, ename, tag, data_len, data, edfname)
#endif /* CONFIG_DSKI */

/**********************************************************/
/*          BEGIN MERGE OF ENTITY.H into DSKI.H           */
/**********************************************************/

#ifdef __KERNEL__
#include <asm/timex.h>
#else
#include <kusp/misc.h>
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
	DS_TYPE_COUNT,
	DS_INTERNAL_ERROR_TYPE,
	DS_INTERNAL_EVENT_TYPE
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

/**********************************************************/
/*       BEGIN MERGE OF DSTRM_DSKI.H into DSKI.H          */
/**********************************************************/

#include <asm/ioctl.h>
#include <linux/limits.h>

/* Entity configure flags */
#define ENTITY_ENABLE	0x01
#define ENTITY_DISABLE	0x02

#define DS_STR_LEN 256
#define DSKI_DIR "datastreams"
#define CHAN_DIR "channels"

/* channel flags */
#define DS_CHAN_TRIG	0x01
#define DS_CHAN_CONT	0x02
#define DS_CHAN_MMAP    0x04

/* Explicit on/off flag for datastreams */
#define DS_DSTRM_ON	0x01

/* Available filters */
#define FLTR_TAG "Tag Filter"
#define FLTR_PID "PID Filter"
#define FLTR_DSCVR "Discovery Filter"
#define FLTR_SMONITOR "System Monitoring Filter"
#define FLTR_DTRACE "Daemon Trace Filter"
#define FLTR_TASK "CCSM based per-task filter"
#define FLTR_CCSM_TRACEME "CCSM based traceme filter"
#define FLTR_CCSM_STRACE "CCSM based strace filter"
#define FLTR_PRINTK "Printk filter"

#define	FLTR_ACCEPT 1
#define	FLTR_REJECT 2
#define	FLTR_PASS   3
#define	FLTR_NEGATE 4

enum {
// for SystemMonitor Purposes.
	OPEN,
// For SystemMonitor Purposes.
	PINFO,
	SYSTEM_CALL,
// For SystemMonitor Purposes.
	PSYS,
	IPS_MAX
};

struct dski_pid_filter_elem {
	char name[NAME_MAX+1];
	long pid;
	int match_response;
};

struct dski_pid_filter_ctrl {
	size_t pid_array_size;
	struct dski_pid_filter_elem *pids;
	int default_response;
};

struct dski_task_filter_ctrl {
	char *set_name;
	long pid;
	int match_response;
};

struct dski_dscvr_ip {
	char fname[NAME_MAX+1];
	char ename[NAME_MAX+1];
	unsigned int eid;
	struct dski_dscvr_ip *next;
};

struct dski_dscvr_filter_ctrl {
	char *name;
};

// The system Monitor structure that encapsulates the information that the active
// filter requires to process certain information that one requires.
struct dski_smonitor_filter_ctrl {
	char *procfile_name;
	struct dski_monitor_list *lists;
	struct dski_monitor_sysList *sysLs;
	int userid;
};

union dski_ioc_filter_ctrl_params {
	struct dski_dscvr_filter_ctrl dscvr_filter;
	struct dski_pid_filter_ctrl pidfilter;
	struct dski_task_filter_ctrl task_filter;
	struct dski_smonitor_filter_ctrl smon_filter;
};

struct dski_ioc_filter_ctrl {
	char datastream[NAME_MAX+1];
	char filtername[NAME_MAX+1];
	union dski_ioc_filter_ctrl_params params;
};

// Used to hold a list of shared libraries that we want to track from the kernel side.
struct dski_monitor_list {
	char shLibName[NAME_MAX+1];
	struct dski_monitor_list *next;
};

// Used to hold a list of system calls that we want to track from the kernel side.
struct dski_monitor_sysList {
	int num;
	struct dski_monitor_sysList *next;
};

struct dski_ioc_channel_ctrl {
	size_t subbuf_size;
	size_t num_subbufs;
	int timeout;
	unsigned int flags;
	int channel_id;
};
 
struct dski_ioc_datastream_ctrl {
	char name[DS_STR_LEN];
	int channel_id;
};

struct dski_ioc_datastream_ip_info {
	char group[DS_STR_LEN];
	char name[DS_STR_LEN];
	char edf[DS_STR_LEN];
	char desc[DS_STR_LEN];
	unsigned int type;
	unsigned int id;
};

struct dski_ioc_datastream_ip_ctrl {
	struct dski_ioc_datastream_ip_info *info;
	size_t size;
};

struct dski_ioc_entity_ctrl {
	int flags;
	unsigned int id;
	char datastream[DS_STR_LEN];
	union ds_entity_info *config_info;
};

union dski_ioctl_param {
	struct dski_ioc_datastream_ctrl		datastream_ctrl;
	struct dski_ioc_channel_ctrl		channel_ctrl;
	struct dski_ioc_entity_ctrl		entity_ctrl;
	struct dski_ioc_datastream_ip_ctrl	ip_info;
	struct dski_ioc_filter_ctrl		filter_ctrl;
};

#define DSKI_DS_CREATE		_IOW('a',  2, struct dski_ioc_datastream_ctrl)
#define DSKI_CHANNEL_OPEN	_IOW('a',  3, struct dski_ioc_channel_ctrl)
#define DSKI_CHANNEL_FLUSH	_IOW('a',  4, struct dski_ioc_channel_ctrl)
#define DSKI_CHANNEL_CLOSE	_IOW('a',  6, struct dski_ioc_channel_ctrl)
#define DSKI_GET_NAMESPACE	_IOW('a',  5, struct dski_ioc_instance_info)
#define DSKI_DS_DESTROY		_IOW('a',  7, struct dski_ioc_datastream_ctrl)
#define DSKI_IPS_QUERY		_IOWR('a', 9, struct dski_ioc_datastream_ip_ctrl)
#define DSKI_RELAY_DIR		_IO('a',  10)
#define DSKI_ENTITY_CONFIGURE	_IOW('a', 11, struct dski_ioc_entity_ctrl)
#define DSKI_FILTER_APPLY	_IOW('a', 12, struct dski_ioc_filter_ctrl)
#define DSKI_DS_ASSIGN_CHAN	_IOW('a', 13, struct dski_ioc_datastream_ctrl)
#define DSKI_DS_ENABLE		_IOW('a', 14, struct dski_ioc_datastream_ctrl)
#define DSKI_DS_DISABLE		_IOW('a', 15, struct dski_ioc_datastream_ctrl)
#endif /* DSKI_H */
