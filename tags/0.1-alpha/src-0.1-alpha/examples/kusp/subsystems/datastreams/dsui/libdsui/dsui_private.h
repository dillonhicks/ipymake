#ifndef _DSUI_PRIVATE_H_
#define _DSUI_PRIVATE_H_

#include <pthread.h>
#include <dsui.h>
#include <dsentity.h>
#include <rdwr.h>



#define DATASTREAM_DEBUG 1
#define LOG_THREAD_DEBUG 0
#define POOL_DEBUG 0
#define BUFFER_THREAD_DEBUG 0


struct datastream;

// fix name of lock to make it more greppable
struct active_entity {
	pthread_mutex_t lock;
	union {
		struct ds_active_counter *counter;
		struct ds_active_interval *interval;
		struct ds_active_histogram *histogram;
	} entity;
};

struct datastream_list {
	struct datastream_ip_data *ip;
	struct active_entity entity;
	struct dstrm_list_head list;
	struct datastream_list *next;
	struct datastream *datastream;
};

extern pthread_rdwr_t dsui_rwlock;

// FIXME: the __sync functions don't work on Fedora boxes
// for some mysterious reason
//#if  (__GNUC__ > 4 || (__GNUC__ == 4 && __GNUC_MINOR__ >= 2))

#if 0

#else
// #warning Use GCC 4.2 for proper atomic increments
#define __sync_add_and_fetch(a, b) (*(a))++
#define __sync_sub_and_fetch(a, b) (*(a))--
#endif

#endif
