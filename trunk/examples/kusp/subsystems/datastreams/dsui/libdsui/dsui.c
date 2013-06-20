/**
 * DSUI - Datastreams User Interface
 *
 * Author: Andrew Boie
 */


#include <config.h>

#include <stdlib.h>
#include <assert.h>
#include <signal.h>
#include <unistd.h>

#include <dsui.h>
#include <dslist.h>
#include <dsentity.h>
#include <linkedlist.h>
#include <configfile.h>
#include <mutex.h>
#include <misc.h>
#include <rdwr.h>
#include <clksyncapi.h>
#include <sys/types.h>
#include <sys/syscall.h>

#include "dsui_private.h"
#include "pool.h"
#include "logging_thread.h"
#include "datastream.h"


sigset_t signals;

pthread_t sigint_thread;

/* Protects the integrity of the complex web of DSUI datastructures */
pthread_rdwr_t dsui_rwlock = PTHREAD_RDWR_INITIALIZER;

/* Hashtable of all active logging threads, indexed by filename */
static hashtable_t *logging_threads;

/** Array of all active datastreams, indexed by ID. */
static struct datastream *ds_array[MAX_DS];

/** The global pool of empty buffers, used by the buffer management threads
 * to populate stream caches */
static struct dstrm_pool *global_buffer_pool = NULL;

/** Set to 1 once DSUI's globals have been initialized */
static int dsui_initialized = 0;

/** Hashtable mapping GROUP/NAME to struct datastream_ip*  */
static hashtable_t *ip_names;

/** DSUI catches SIGINT, and once it deals with it, this
  * user-defined function can be called too */
static sighandler_t dsui_inthandle = NULL;

/** Entity ids are dynamically created, starting at this value.
  * Values below this are assumed to be reserved for hard-coded
  * administrative events */
static int starting_id = 1024;

/** The current header version. Don't forget to update
  * ../utils/dsui-header if you change this */
#define DSUI_HEADER_VER	5

int dsui_verbose = 0;
#define VERB if(dsui_verbose)

/**
 * sig_pid holds the pid of the signal catcher thread which is forked off when DSUI is turned on
 * logging_thread_pid holds the pid of the logging thread which is forked off when DSUI is turned on
 * buffer_thread_pid holds the pid of the buffer thread which is forked off when DSUI is turned on
 * These variables are created for discovery purposes
 */
int sig_pid =0;
int logging_thread_pid=0;
int buffer_thread_pid=0;

/**
 * Condition Variable that is checked to see if all the other spawned threads as part of DSUI
 * have started working.......
 */
int condition_variable = 0;
pthread_cond_t discovery_cond = PTHREAD_COND_INITIALIZER;
pthread_mutex_t discovery_mutex = PTHREAD_MUTEX_INITIALIZER;

/** Instrumentation point datastructures for DSTRM_PRINTF */
static struct datastream_ip_data __datastream_ip_data_DSTREAM_ADMIN_FAMPRINTF =
{
        "DSTREAM_ADMIN_FAM",
        "PRINTF",
        "print_string",
        "",
        "",
        0,
        DS_EVENT_TYPE,
        {NULL, NULL},
        0,
        NULL,
        {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL}
};

struct datastream_ip __datastream_ip_DSTREAM_ADMIN_FAMPRINTF =
{
        &__datastream_ip_data_DSTREAM_ADMIN_FAMPRINTF,
        &__datastream_ip_data_DSTREAM_ADMIN_FAMPRINTF.next,
        &__datastream_ip_data_DSTREAM_ADMIN_FAMPRINTF.id
};

/** Called from the constructor functions in generated _dsui.c files.
  * It freaks out if the header version it was compiled with doesn't match
  * the library's */
void dsui_header_check(int current_version, char *prefix)
{
	if (current_version != DSUI_HEADER_VER) {
		printf("ERROR: Your generated DSUI files for '%s' are too old.\n",
				prefix);
		printf("Current version %d your version %d. "
				"Regenerate and recompile.\n",
			DSUI_HEADER_VER, current_version);
		exit(1);
	}
}


/* XXX: I still am not completely happy with this mechanism, but
 * it's the best i've been able to come up with so far.
 * Mixing pthreads and signals is annoying! */
static void *sigint_thread_run(void *p)
{
	int signum;
	sighandler_t h;
	// storing the pid of the signal catcher thread in the global variable sig_pid
	// which is defined in this file for discovery purposes
	pthread_mutex_lock(&discovery_mutex);
	sig_pid = syscall(SYS_gettid);
	condition_variable=condition_variable+1;
	dprintf("Signal Catcher thread ....%d %d %d %d\n",sig_pid, condition_variable,getpid(),gettid());
	pthread_cond_signal(&discovery_cond);
	pthread_mutex_unlock(&discovery_mutex);

beginning:
	sigwait(&signals, &signum);

	dprintf("signal catcher thread caught a signal!\n");

	dsui_cleanup();

	km_rdwr_rlock(&dsui_rwlock);
	h = dsui_inthandle;
	km_rdwr_runlock(&dsui_rwlock);

	if (h) {
		dprintf("calling user-defined signal function\n");
		(h)(signum);
	} else {
		_exit(signum);
	}

	goto beginning;

	return NULL;
}


static void __dsui_register_ip(struct datastream_ip *ip);

static void dsui_init_check() __attribute__((constructor));


/* This initializes DSUI itself. A call is made every time an application
 * tries to register its instrumentation points, from dsui_register_ip() */
static void dsui_init_check()
{
	km_rdwr_wlock(&dsui_rwlock);
	if (!dsui_initialized) {
		int retval;

		global_buffer_pool = malloc(sizeof(struct dstrm_pool));
		dstrm_pool_init(global_buffer_pool, 128, 32768);
		logging_threads = create_dictionary();
		ip_names = create_dictionary();
		dsui_initialized = 1;

		sigemptyset(&signals);
		sigaddset(&signals, SIGINT);
		retval = pthread_sigmask(SIG_BLOCK, &signals, NULL);
		if (retval) {
			kusp_errno("pthread_sigmask", retval);
		}
		retval = pthread_create(&sigint_thread, NULL, &sigint_thread_run, NULL);
		if (retval) {
			kusp_errno("pthread_create", retval);
		}

		//printf("Signal Thread ....%d\n",sigint_thread);
		__dsui_register_ip(&__datastream_ip_DSTREAM_ADMIN_FAMPRINTF);
	}
	km_rdwr_wunlock(&dsui_rwlock);
}

#ifdef NOTUSED
/** Write an event with hard-coded id directly to a logging thread,
  * bypassing all buffering */
void dsui_raw_event(dsui_log_t log, int id, int tag, size_t size,
		void *extradata)
{
	struct logging_thread *lt;
	km_rdwr_rlock(&dsui_rwlock);
	lt = hashtable_search(logging_threads, log);
	if (lt) {
		log_admin_event(lt, id, tag, size, extradata);
	} else {
		eprintf("Unknown logging thread '%s'\n", log);
	}
	km_rdwr_runlock(&dsui_rwlock);
}
#endif

/* Write namespace information for a specific instrumentation point
 * directly to the output file */
static void write_namespace_event(struct datastream_ip_data *ipdata,
		struct logging_thread *log)
{
	struct ds_ns_fragment ns;

	strncpy(ns.group, ipdata->group, 48);
	strncpy(ns.name, ipdata->name, 48);
	if (ipdata->edf) {
		strncpy(ns.info, ipdata->edf, 48);
	} else {
		strcpy(ns.info, "");
	}

	if (ipdata->line != -1) {
		snprintf(ns.desc, 48, "%s:%s:%d", ipdata->file, ipdata->func,
			ipdata->line);
	} else {
		ns.desc[0] = '\0';
	}
	ns.id = ipdata->id;
	ns.type = ipdata->type;

	// DSTRM_ADMIN_FAM/NAMESPACE_FRAGMENT
	log_admin_event(log, 16, 1337, sizeof(ns), &ns);
}

/* Write the DSUI header to an output file. This includes a timekeeping
 * event (to establish tsc-to-nanosecond correspondence) and then a
 * namespace event for each instrumentation point we know about */
static void write_header(struct logging_thread *log)
{
	hashtable_itr_t itr;

	log_time_state(log);
	if (!hashtable_count(ip_names))
		return;

	init_iterator(&itr, ip_names);

	do {
		struct datastream_ip *ip = hashtable_iterator_value(&itr);
		write_namespace_event(ip->ip, log);
	} while (hashtable_iterator_advance(&itr));
}

// ******** EXTERNAL INTERFACE ****************************

/* This function allows you to declare instrumentation points
 * on the fly, as opposed to during compile-time. This may
 * be necessary for some languages.
 *
 * The IP is automatically registered with DSUI once it is created,
 * emitting namespace information to all open logging threads.
 * However, it is still up to you to enable it.
 *
 * The string parameters are duplicated, the IP does not take
 * ownership of them.
 *
 * @param info   The type-specific field.
 *
 */
struct datastream_ip *dsui_create_ip(char *group, char *name,
		int type, char *info)
{
	struct datastream_ip *ip;
	struct datastream_ip_data *ipdata;

	ip = malloc(sizeof(*ip));
	if (!ip) {
		eprintf("malloc() failed!\n");
		return NULL;
	}

	ipdata = malloc(sizeof(*ipdata));
	if (!ipdata) {
		eprintf("malloc() failed!\n");
		free(ip);
		return NULL;
	}

	memset(ipdata, 0, sizeof(*ipdata));

	ipdata->group = strdup(group);
	ipdata->name = strdup(name);
	if (info) {
		ipdata->edf = strdup(info);
	} else {
		ipdata->edf = "";
	}
	ipdata->file = "";
	ipdata->func = "";
	ipdata->type = type;
	ipdata->line = -1;

	ip->ip = ipdata;
	ip->next = &ipdata->next;
	ip->id = &ipdata->id;

	dsui_register_ip(ip);

	return ip;
}

/* XXX: clksync uses this, but perhaps it would be better to spawn a thread
 * for each output file to automatically write periodic time information? */
void dsui_write_time_state(char *logname)
{
	struct logging_thread *log;
	km_rdwr_rlock(&dsui_rwlock);

	log = hashtable_search(logging_threads, logname);
	if (!log) {
		eprintf("Unknown logging thread '%s'\n", logname);
	} else {
		log_time_state(log);
	}

	km_rdwr_runlock(&dsui_rwlock);
}


/** A wrapper to the signal() system call, useful if the user
  * wants to install a signal handler for SIGINT */
sighandler_t dsui_signal(int signum, sighandler_t handler)
{
	sighandler_t retval;
	if (signum == SIGINT) {
		km_rdwr_wlock(&dsui_rwlock);
		dsui_inthandle = handler;
		km_rdwr_wunlock(&dsui_rwlock);
		retval = handler;
	} else {
		retval = signal(signum, handler);
	}

	return retval;
}


/** Return the instrumentation point datastructure corresponding
 * to the given group and name, or NULL if it does not exist */
struct datastream_ip *dsui_get_ip_byname(char *group, char *name)
{
	struct datastream_ip *retval;
	char ipname[100];
	km_rdwr_rlock(&dsui_rwlock);

	snprintf(ipname, 99, "%s/%s", group, name);
	retval = hashtable_search(ip_names, ipname);

	km_rdwr_runlock(&dsui_rwlock);

	return retval;
}


list_t *dsui_get_ips_byfamily(char *group)
{
	list_t *elist = create_list();
	hashtable_itr_t itr = HASH_ITR_INIT;
	char *key;
	struct datastream_ip *ip;

	km_rdwr_rlock(&dsui_rwlock);

	while (hashtable_iterate(ip_names, &itr, &key, &ip)) {
		char *famname = strdup(key);
		int x = strlen(group);

		if (x > strlen(key))
			goto endloop;

		if (famname[x] != '/')
			goto endloop;

		famname[x] = '\0';

		if (!strcmp(group, famname)) {
			list_append(elist, ip);
		}
endloop:
		free(famname);
	}

	km_rdwr_runlock(&dsui_rwlock);

	return elist;
}


/** Register an instrumentation point with DSUI. This accomplishes
 * several things:
 * 1) The IP is inserted into the global instrumentation point
 *    hash table so it can be looked up by name
 * 2) The numerical ID of the instrumentation point is assigned.
 *    Entities are logged by ID, with the name and other metadata
 *    stored in the previously logged namespace information.
 *
 * If DSUI dicovers that an instrumentation point is already registered
 * under the same name, then it assumes that this IP is another instance
 * of the same point, and modifies the IP's pointers so that it refers
 * to the same namespace/state information as the previous IP.
 *
 * If there are any open log files, a namespace event for this IP
 * will be written to each of them.
 *
 * You must hold the DSUI write-lock when calling this function */
static void __dsui_register_ip(struct datastream_ip *ip)
{
	struct datastream_ip_data *ipdata = ip->ip;
	char *ipname;
	struct datastream_ip *v;
	hashtable_itr_t itr;

	if (ipdata->id) {
		bprintf("Already Registered %s/%s/%d\n", ipdata->group,
			ipdata->name, ipdata->id);
		return;
	}

	ipname = malloc(strlen(ipdata->group) + strlen(ipdata->name) + 2);
	sprintf(ipname, "%s/%s", ipdata->group, ipdata->name);
	v = hashtable_search(ip_names, ipname);
	if (v) {
		//dprintf("%s encountered more than once mapping %p->%p\n",
		//		ipname, ip, v);
		ip->ip = v->ip;
		ip->next = &v->ip->next;
		ip->id = &v->ip->id;
		v->ip->line = -1;
		free(ipname);
		return;
	}

	ipdata->id = starting_id++;
	hashtable_insert(ip_names, ipname, ip);
	//dprintf("Registered %s/%s/%d \n", ipdata->group,
	//		ipdata->name, ipdata->id);

	/* if this ip was registered when there are already active
	 * logging threads, we need to write namespace information
	 * for this ip */

	if (!hashtable_count(logging_threads)) {
		return;
	}
	init_iterator(&itr, logging_threads);
	do {
		struct logging_thread *log;
		log = hashtable_iterator_value(&itr);
		write_namespace_event(ipdata, log);
	} while (hashtable_iterator_advance(&itr));
}

/** Register an instrumentation point datastructure.
  *
  * DSUI needs to be aware of all the instrumentation points so that
  * it can build a namespace. It stores all the registered IPs in a
  * hash table. */
void dsui_register_ip(struct datastream_ip *ip)
{
	// to avoid race conditions; nobody knows what order
	// constructors get called
	dsui_init_check();

	km_rdwr_wlock(&dsui_rwlock);
	__dsui_register_ip(ip);
	km_rdwr_wunlock(&dsui_rwlock);
}


/** Create a new datastream with no entities enabled
 *
 * Returns the ID of this new datastream so it can be specifically referenced
 *
 * The cache size is the number of empty buffers the datastream will hold in
 * its cache, and the mode determines whether the datastream writes events
 * as it recieves them, or holds them in a circular ringbuffer until
 * it is explicitly flushed
 */
int dsui_open_datastream(char *logfile, int cache_size, enum datastream_mode mode)
{
	int id;
	struct datastream *d;
	struct logging_thread *log;

	km_rdwr_wlock(&dsui_rwlock);


	log = hashtable_search(logging_threads, logfile);
	if (!log) {
		eprintf("Unknown logging thread '%s'. Is it open?\n", logfile);
		id = -1;
		goto out;
	}

	for(id = 0; id == MAX_DS; id++) {
		if (ds_array[id] == NULL) break;
	}
	if (id == MAX_DS) {
		eprintf("no free datastreams\n");
		id =  -1;
		goto out;
	}

	d = datastream_create(id, global_buffer_pool, log,
			cache_size, mode);

	ds_array[id] = d;

out:
	km_rdwr_wunlock(&dsui_rwlock);
	return id;
}

/** Open an output file for logging. The opened log file
 * can be referenced in the logging_threads hash table,
 * keyed by its file name.
 *
 * Returns the hashtable key for the opened filename,
 * or NULL if opening did not succeed */
char *dsui_open_output_file(char *filename)
{
	struct logging_thread *log = malloc(sizeof(*log));

	if (init_file_logging_thread(log, filename)) {
		eprintf("Unable to create logging thread.\n");
		free(log);
		return NULL;
	}

	km_rdwr_wlock(&dsui_rwlock);

	hashtable_insert(logging_threads, strdup(log->filename), log);
	write_header(log);

	km_rdwr_wunlock(&dsui_rwlock);

	dprintf("Opened file '%s' for logging.\n", filename);
	return log->filename;
}

/** Open an output socket for logging. The opened log file
 * can be referenced in the logging_threads hash table.
 *
 * Returns the hashtable key for the opened filename,
 * or NULL if opening did not succeed */
char *dsui_open_output_socket(char *hostname, int port)
{
	struct logging_thread *log = malloc(sizeof(*log));
	dprintf("Connecting to '%s:%d' for logging.\n", hostname, port);

	if (init_socket_logging_thread(log, hostname, port)) {
		eprintf("Unable to create socket logging thread.\n");
		free(log);
		return NULL;
	}

	km_rdwr_wlock(&dsui_rwlock);

	hashtable_insert(logging_threads, strdup(log->filename), log);
	write_header(log);

	km_rdwr_wunlock(&dsui_rwlock);

	dprintf("Opened socket '%s:%d' for logging.\n", hostname, port);
	return log->filename;
}

/** returns a configfile linked list of active logging thread filenames.
 * These are the keys in the logging_threads hashtable. */
list_t *get_dsui_output_filenames()
{
	list_t *f = create_list();
	struct logging_thread *log;
	hashtable_itr_t itr;

	km_rdwr_rlock(&dsui_rwlock);

	if (!hashtable_count(logging_threads)) {
		goto out;
	}

	init_iterator(&itr, logging_threads);
	do {
		log = hashtable_iterator_value(&itr);
		list_append(f, encap_string(log->filename));
	} while (hashtable_iterator_advance(&itr));
out:
	km_rdwr_runlock(&dsui_rwlock);
	return f;
}

static int __dsui_enable_ip(int dstream_id, struct datastream_ip *ip,
		union ds_entity_info *config_info)
{
	int retval;
	struct datastream *d = ds_array[dstream_id];
	if (d == NULL) {
		eprintf("Datastream [%d] is not active.\n", dstream_id);
		return -1;
	}

	retval = entity_enable(d, ip->ip, config_info);

	if (retval) {
		eprintf("Could not enable '%s/%s': %s\n", ip->ip->group,
				ip->ip->name, strerror(-retval));
	} else VERB {
		dprintf("Enabled '%s/%s'\n", ip->ip->group,
				ip->ip->name);
	}

	return retval;
}


/** Enable an instrumentation point for logging to a particular datastream.
 * Some entities, such as histograms, require additional configuration
 * information, provided in the config_info parameter.
 *
 * Returns nonzero if the enable operation failed */
int dsui_enable_ip(int dstream_id, struct datastream_ip *ip,
		union ds_entity_info *config_info)
{
	int retval;
//	printf("dstream id : %d\n",dstream_id);
	km_rdwr_wlock(&dsui_rwlock);
	retval = __dsui_enable_ip(dstream_id, ip, config_info);
	km_rdwr_wunlock(&dsui_rwlock);
	return retval;
}


static void __dsui_disable_ip(int dstream_id, struct datastream_ip *ip)
{
	struct datastream *d = ds_array[dstream_id];
	if (d == NULL) {
		eprintf("Datastream [%d] is not active.\n", dstream_id);
		return;
	}

	entity_disable(d, ip->ip);
}

/** Disable an instrumentation point for a particular datastream. */
void dsui_disable_ip(int dstream_id, struct datastream_ip *ip)
{
	km_rdwr_wlock(&dsui_rwlock);
	__dsui_disable_ip(dstream_id, ip);
	km_rdwr_wunlock(&dsui_rwlock);
}


/** Take a 'snapshot' of all enabled entities in a specified datastream
 * that have state; at the moment this includes histograms and counters. */
void dsui_snapshot_datastream(int id)
{
	struct datastream *d;

	km_rdwr_rlock(&dsui_rwlock);
	d = ds_array[id];
	assert(d != NULL);
	datastream_snapshot(d);
	km_rdwr_runlock(&dsui_rwlock);
}


static void __dsui_close_datastream(int id)
{
	struct datastream *d;

	d = ds_array[id];
	if (d) {
		datastream_snapshot(d);
		datastream_disable(d);
		ds_array[id] = NULL;
	}
}

/** Close a datastream. This will take a snapshot of all entities
 * that have state information (counters/histograms) before disabling
 * the datastream itself */
void dsui_close_datastream(int id)
{
	km_rdwr_wlock(&dsui_rwlock);
	__dsui_close_datastream(id);
	km_rdwr_wunlock(&dsui_rwlock);
}

/** Flush all the unwritten buffers of a specific datastream out to the disk.
 * This is particularly useful for datastreams in ringbuffer mode; make this
 * call whenever the triggering condition occurs. */
void dsui_flush_datastream(int id)
{
	struct datastream *d;

	// use a write-lock to ensure that a datastream isn't holding
	// a buffer
	km_rdwr_wlock(&dsui_rwlock);
	d = ds_array[id];
	if (d) {
		datastream_flush(d);
	}
	km_rdwr_wunlock(&dsui_rwlock);
}


static void __dsui_cleanup() {
	int i;
	hashtable_itr_t itr;

	dprintf("called\n");
	for(i=0; i < MAX_DS; i++) {
		__dsui_close_datastream(i);
	}

	if (!hashtable_count(logging_threads)) {
		return;
	}
	init_iterator(&itr, logging_threads);
	do {
		struct logging_thread *log;
		log = hashtable_iterator_value(&itr);
		close_logging_thread(log);
		free(log);

	} while (hashtable_iterator_remove(&itr));
}

/** General-purpose DSUI teardown routine.
 *
 * It closes all open datastreams (taking snapshots of all
 * stateful entities first) and then closes all open logging
 * threads */
void dsui_cleanup() {
	km_rdwr_wlock(&dsui_rwlock);
	__dsui_cleanup();
	km_rdwr_wunlock(&dsui_rwlock);
}


/** Enable all the instrumentation points DSUI knows about for
  * a particular datastream */
void dsui_enable_all_ips(dsui_stream_t ds)
{
	int ctr = 0;

	hashtable_itr_t itr;
	init_iterator(&itr, ip_names);

	do {
		struct datastream_ip *ip = hashtable_iterator_value(&itr);
		ctr++;
		__dsui_enable_ip(ds, ip, NULL);
	} while (hashtable_iterator_advance(&itr));
	dprintf("Enabled %d entities for datastream [%d]\n",
			ctr, ds);
}

static union ds_entity_info *construct_hist_params(
		struct hashtable *config)
{
	int warning_avoider;
	union ds_entity_info *info = malloc(sizeof(*info));

	if (!info) {
		eprintf("malloc() failed\n");
		return NULL;
	}

	unhash_long(config, "upperbound", &(info->hist_info.upperbound));
	unhash_long(config, "lowerbound", &(info->hist_info.lowerbound));
	/* unhash_int is used for various data types which could be either ints
	 * or unsigned ints. Rather than survey all uses and make them all one
	 * or the other, here we chose to cast in these two uses which were
	 * causing compiler warnings. We use the aptly named local int variable
	 * to avoid these warnings because casting the union variable and taking
	 * an address of it all in one statement was giving the compiler
	 * heartburn.
	 */
	warning_avoider = (int)info->hist_info.buckets;
	unhash_int(config, "buckets",     &warning_avoider);

	warning_avoider = (int)info->hist_info.tune_amount;
	unhash_int(config, "tune_amount", &warning_avoider);

	return info;
}


/** Process a dictionary of enabled DSUI events, given from a
 * DSUI configuration file, and enable the corresponding
 * instrumentation points */
static void dsui_process_enable_dict(dsui_stream_t ds,
		struct hashtable *enabled)
{
	hashtable_itr_t fam_itr = HASH_ITR_INIT;
	char *fam_name;
	value_t *val;
#if 0
	/* FIXME.j - appears to be an unused variable */
	hashtable_t family_dict;
#endif
	list_t *pos;


	while (hashtable_iterate(enabled, &fam_itr, &fam_name, &val)) {
		list_t *entity_list;

		if (value_type(val) == BOOLTYPE) {
			if (as_bool(val)) {
				entity_list = create_list();
				list_t *iplist = dsui_get_ips_byfamily(fam_name);
				list_for_each(pos, iplist) {
					struct datastream_ip *ip = pos->item;
					list_append(entity_list, encap_string(ip->ip->name));
				}
				list_free(iplist);
			} else {
				continue;
			}
		} else {
			entity_list = as_list(val);
		}

		list_for_each(pos, entity_list) {
			invocation_t *hist_invoc = NULL;
			char *ent_name;
			struct datastream_ip *ip;
			union ds_entity_info *info = NULL;

			if (!unlist_invoc(pos, &hist_invoc)) {
				ent_name = hist_invoc->name;
			} else {
				unlist_string(pos, &ent_name);
			}

			ip = dsui_get_ip_byname(
				fam_name, ent_name);

			if (!ip) {
				wprintf("Entity %s/%s specified in DSUI "
					"config does not exist, skipping.\n",
					fam_name, ent_name);
				continue;
			}

			if (hist_invoc) {
				if (ip->ip->type != DS_HISTOGRAM_TYPE) {
					wprintf("Histogram config data "
						"specified for entity %s/%s, "
						"but it is not a histogram.\n",
						fam_name, ent_name);
				} else {
					info = construct_hist_params(
							hist_invoc->params);
				}
			}
			dsui_enable_ip(ds, ip, info);

			if (info) {
				free(info);
			}
		}
	}
}



/* Remove num entries in argv, starting at index i. Move subsequent
 * array entries upward and correct argc. */
static void permute_argv(int *argcp, char ***argvp, int num, int *i)
{
	int j;
	for (j=(*i)+num; j < *argcp; j++) {
		(*argvp)[j-num] = (*argvp)[j];
	}
	*argcp = *argcp - num;
	(*i)--;
}

/* List all known instrumentation points in a human-readable format */
static void dsui_list_ips()
{
	hashtable_itr_t itr = HASH_ITR_INIT;
	char *key;
	struct datastream_ip *ip;
	int ctr = 0;

	while (hashtable_iterate(ip_names, &itr, &key, &ip)) {
		struct datastream_ip_data *ipd = ip->ip;
		switch (ipd->type) {
		case DS_EVENT_TYPE:
			printf("event     ");
			break;
		case DS_COUNTER_TYPE:
			printf("counter   ");
			break;
		case DS_HISTOGRAM_TYPE:
			printf("histogram ");
			break;
		case DS_INTERVAL_TYPE:
			printf("interval  ");
			break;
		default:
			printf("unknown   ");
		}
		printf("\t%u\t", ipd->id);
		printf("%s/%s\t%s:%s:%d\n",
			ipd->group, ipd->name, ipd->file, ipd->func, ipd->line);
		ctr++;
	}
	printf("Total of %d entities declared.\n", ctr);
}

/* Configfile specification for DSUI configuration files */
static char *dsui_spec_str =
"<root>\n"
"doc = \"DSUI enable file\"\n"
"dictdef = {\n"
"       \"dsui_enabled\" = @\"dsui_enabled\"\n"
"       \"dsui\" = @\"dsui\"\n"
"}\n"
"types = \"dictionary\"\n"
"\n"
"<dsui_enabled>\n"
"var = 3\n"
"doc = \"Enabled Families\"\n"
"opendictdef = {\n"
"       \"listdef\" = {\n"
"               \"types\" = [\n"
"                       \"string\"\n"
"                       \"invocation\"\n"
"               ]\n"
"               \"openinvodef\" = {\n"
"                       \"upperbound\" = {\n"
"                               \"default\" = 1\n"
"                               \"types\" = [\n"
"                                       \"long\"\n"
"                               ]\n"
"                       }\n"
"                       \"buckets\" = {\n"
"                               \"default\" = 20\n"
"                               \"types\" = [\n"
"                                       \"integer\"\n"
"                               ]\n"
"                       }\n"
"                       \"lowerbound\" = {\n"
"                               \"default\" = 0\n"
"                               \"types\" = [\n"
"                                       \"long\"\n"
"                               ]\n"
"                       }\n"
"                       \"tune_amount\" = {\n"
"                               \"default\" = 50\n"
"                               \"types\" = [\n"
"                                       \"integer\"\n"
"                               ]\n"
"                       }\n"
"               }\n"
"       }\n"
"       \"types\" = [\n"
"               \"boolean\"\n"
"               \"list\"\n"
"       ]\n"
"}\n"
"types = \"dictionary\"\n"
"\n"
"<dsui>\n"
"doc = \"DSUI Library parameters\"\n"
"dictdef = {\n"
"       \"enabled\" = {\n"
"               \"var\" = 1\n"
"               \"doc\" = \"Turn DSUI on or off\"\n"
"               \"default\" = true\n"
"               \"types\" = \"boolean\"\n"
"       }\n"
"       \"buffers\" = {\n"
"               \"var\" = 2\n"
"               \"doc\" = \"buffers per datastream\"\n"
"               \"default\" = 32\n"
"               \"types\" = \"integer\"\n"
"       }\n"
"       \"network_port\" = {\n"
"               \"var\" = 4\n"
"               \"doc\" = \"remote port to connect to\"\n"
"               \"default\" = -1\n"
"               \"types\" = \"integer\"\n"
"       }\n"
"       \"output_file\" = {\n"
"               \"var\" = 0\n"
"               \"doc\" = \"Binary output filename\"\n"
"               \"required\" = false\n"
"               \"types\" = \"string\"\n"
"       }\n"
"}\n"
"types = \"dictionary\"\n"
"\n";


char *dsui_help =
"  --dsui-output <file or hostname>\n"
"	Destination output file or hostname. Only interprets this\n"
"	as a hostname if --dsui-network-port is used.\n"
"  --dsui-list\n"
"	List all the instrumentation points compiled into an application\n"
"	and exit.\n"
"  --dsui-buffers\n"
"	Number of buffers per datastream. Default is 16, increase if you\n"
"	get a lot of 'buffer management thread failed to keep up' messages\n"
"  --dsui-disable\n"
"	Run the application without DSUI\n"
"  --dsui-config <filename>\n"
"	Parameterize DSUI using a configuration file\n"
"  --dsui-network-port <port num>\n"
"	Set the network port of the remote server to connect to. Using\n"
"	this option streams data to a socket, not a file.\n"
"  --dsui-help\n"
"	Show this message\n";


/** General-purpose initialization routine.
 *
 * DSUI supports a few command line options to override some defaults.
 * Because of this, pointers to argc and argv should be provided.
 * When this function returns all DSUI-specific command line options
 * will be removed from argv, so that any subsequent calls to getopt()
 * will not need to recognize DSUI command line options.
 *
 * By default, an output file is opened (specified by default_filename
 * parameter), a single datastream for that output file is created,
 * and all known instrumentation points are enabled for it.\
 *
 * dsui_start is not currently meant to encompass all possible uses of
 * DSUI, just the most common ones. More esoteric configurations will
 * require the direct use of DSUI API calls.
 *
 * FIXME: get rid of default filename parameter and just generate one
 * based on argv[0]
 * */
void dsui_start(int *argcp, char *** argvp, const char *default_filename) {
	dsui_log_t log = NULL;
	dsui_stream_t ds;
	char **argv;
	int enabled = 1;
	int i, err;
	int buffers = 64;
	int network_port = -1;
	const char *log_filename = NULL;
	hashtable_t *enable_dict = NULL;
	
	dsui_init_check();

	if (!argcp || !argvp) {
		goto noargc;
	}

	argv = *argvp;

	for (i=1; i < *argcp; i++) {
		err = 0;
		//dprintf("argv[%d] is %s\n", i, argv[i]);
		if (!strcmp(argv[i], "--dsui-output")) {
			if ((i+1) >= *argcp) {
				eprintf("--dsui-output requires a "
						"output file or hostname\n");
				exit(1);
			}
			log_filename = argv[i+1];
			permute_argv(argcp, argvp, 2, &i);

			dprintf("Specified output file %s on command line.\n",
					log_filename);
			continue;

		} else if (!strcmp(argv[i], "--dsui-list")) {
			dsui_list_ips();
			exit(0);

		} else if (!strcmp(argv[i], "--dsui-disable")) {
			dprintf("Disabled DSUI from command line.\n");
			permute_argv(argcp, argvp, 1, &i);
			enabled = 0;
			continue;

		} else if (!strcmp(argv[i], "--dsui-buffers")) {
			if ((i+1) >= *argcp) {
				eprintf("--dsui-buffers requires a "
						"parameter\n");
				exit(1);
			}
			buffers = atoi(argv[i+1]);
			permute_argv(argcp, argvp, 2, &i);
			dprintf("user set number of datastream buffers to %d\n",
					buffers);
			continue;

		} else if (!strcmp(argv[i], "--dsui-network-port")) {
			if ((i+1) >= *argcp) {
				eprintf("--dsui-network-port requires a "
						"parameter\n");
				exit(1);
			}
			network_port = atoi(argv[i+1]);
			permute_argv(argcp, argvp, 2, &i);
			dprintf("user set network port to %d\n", buffers);
			continue;

		} else if (!strcmp(argv[i], "--dsui-config")) {
			char *config_filename;
			hashtable_t *c;
			void *vars[] = {
				&log_filename,
				&enabled,
				&buffers,
				&enable_dict,
				&network_port
			};

			if ((i+1) >= *argcp) {
				eprintf("--dsui-config requires a "
						"configuration filename\n");
				exit(1);
			}

			config_filename = argv[i+1];
			permute_argv(argcp, argvp, 2, &i);

			dprintf("Specified configuration file '%s' on command line.\n",
					config_filename);

			c = process_configfile(parse_config(config_filename),
					parse_spec_string(dsui_spec_str),
					vars);
			if (!c) {
				eprintf("Unable to process '%s'\n", config_filename);
				goto errorout;
			}
			continue;

		} else if (!strcmp(argv[i], "--dsui-verbose")) {
			dsui_verbose = 1;
			permute_argv(argcp, argvp, 1, &i);
			continue;
		} else if (!strcmp(argv[i], "--dsui-help")) {
			printf("%s", dsui_help);
			exit(0);
		}
	}
noargc:

	if (!enabled) {
		return;
	}

	if (!log_filename) {
		log_filename = default_filename;
	}

	if (network_port != -1) {
		log = dsui_open_output_socket(strdup(log_filename), network_port);
	} else {
		log = dsui_open_output_file(strdup(log_filename));
	}

	if (!log) {
		goto errorout;
	}

	ds = dsui_open_datastream(log, buffers, STREAM_NORMAL_MODE);
	if (ds == -1) {
		eprintf("Unable to create datastream!\n");
		goto errorout;
	}

	if (!enable_dict) {
		dsui_enable_all_ips(ds);
	} else {
		dsui_process_enable_dict(ds, enable_dict);
	}

	/*
	 * we pass DSUI events onto the DSUI LOG file here. we pass the pids of the three threads
	 * being forked off as part of the DSUI initialization step as tag values to the events
	 * defined here, these events are generated for discovery purposes
	 */
	
	pthread_mutex_lock(&discovery_mutex);
	while(condition_variable != 3){
		dprintf("Condition Variable ....%d\n", condition_variable);
		pthread_cond_wait(&discovery_cond, &discovery_mutex);
	}
	pthread_mutex_unlock(&discovery_mutex);
	
	dprintf("signal_pid :%d\n",sig_pid);
	dprintf("logging thread pid :%d\n", logging_thread_pid);
	dprintf("Buffer Thread pid :%d\n", buffer_thread_pid);

	struct datastream_ip *ip;
	ip = dsui_create_ip("DSCVR", "DSUI_SIGNAL_THREAD", DS_EVENT_TYPE,strdup("print_pickle"));
	dsui_enable_ip(ds, ip, NULL);
	dsui_event_log(ip, sig_pid, 0, NULL);

	ip =dsui_create_ip("DSCVR","DSUI_LOGGING_THREAD",DS_EVENT_TYPE,strdup("print_pickle"));
	dsui_enable_ip(ds,ip,NULL);
	dsui_event_log(ip,logging_thread_pid,0,NULL);

	ip = dsui_create_ip("DSCVR","DSUI_BUFFER_THREAD",DS_EVENT_TYPE,strdup("print_pickle"));
	dsui_enable_ip(ds,ip,NULL);
	dsui_event_log(ip,buffer_thread_pid,0,NULL);

	dprintf("DSUI start completed successfully\n");

	return;

errorout:
	eprintf("DSUI initialization FAILED\n");
	exit(1);
}

/* A function used for storing the pid of the logging thread in the global variable logging_thread_pid
 * which is defined in this file.
 */
void set_logging_thread_pid(int pid){
	pthread_mutex_lock(&discovery_mutex);
	logging_thread_pid = pid;
	condition_variable=condition_variable + 1;
	dprintf("Logger thread ....%d %d\n",logging_thread_pid, condition_variable);
	pthread_cond_signal(&discovery_cond);
	pthread_mutex_unlock(&discovery_mutex);
}

/* A function used for storing the pid of the buffer thread in the global variable buffer_thread_pid
 * which is defined in this file.
 */
void set_buffer_thread_pid(int pid){
	pthread_mutex_lock(&discovery_mutex);
	buffer_thread_pid = pid;
	condition_variable = condition_variable + 1;
	dprintf("Buffer thread ....%d %d\n",buffer_thread_pid, condition_variable);
	pthread_cond_signal(&discovery_cond);
	pthread_mutex_unlock(&discovery_mutex);
}
