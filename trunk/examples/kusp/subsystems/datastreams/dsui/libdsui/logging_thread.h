/**
 * @file logging_thread.h
 */

#ifndef _LOGGING_THREAD_H_
#define _LOGGING_THREAD_H_

#include <pthread.h>
#include "dstrm_buffer.h"
#include "buffer_queue.h"
#include <mutex.h>
#include <dslist.h>

/**
 * Datastructure for file/socket logging thread. One exists
 * for each open output/file socket
 *
 * Every output file has a single logging thread associated with
 * */
struct logging_thread {

	// member of a global list of active logging threads
	struct dstrm_list_head list_member;

	/// mostly used for debugging
	char *filename;

	/// file descriptor to write entities to
	int fd;

	/// queue of full buffers to write
	struct dstrm_buffer_queue queue;

	/// the logging thread itself
	pthread_t thread;

	/**
	 * total amount of data written to file
	 * */
	unsigned long written;

	/**
	 * set this to 0 and wake up the thread to kill it
	 * this variable is protected by the queue's lock.
	 * */
	int running;

	/**
	 * Entity counter, used to generate a sequential id for
	 * each logged entity. This isn't used by the logging thread,
	 * but since we need to maintain an entity count for each
	 * output file, this is the natural place to put it.
	 */
	//dstrm_atomic_t entity_count;
	int entity_count;
	pthread_mutex_t entity_count_lock;

	/**
	 * protect against concurrent access to instance variables
	 * and output file. entity_count, running, and queue have their own
	 * locks and are not covered by this mutex
	 */
	pthread_mutex_t write_lock;

	/** number of datastreams using this logging thread.*/
	int ref_count;
};


int init_socket_logging_thread(struct logging_thread *t, char *hostname,
		int port);
int init_file_logging_thread(struct logging_thread *t, char *filename);

int close_logging_thread(struct logging_thread *self);


void logging_thread_write(struct logging_thread *self, const void *data,
		size_t size);
void __logging_thread_write(struct logging_thread *self, const void *data,
		size_t size);

void log_time_state(struct logging_thread *log);
void log_admin_event(struct logging_thread *log, int id,
		int tag, size_t size, void *extradata);

#endif // _LOGGING_THREAD_H_
