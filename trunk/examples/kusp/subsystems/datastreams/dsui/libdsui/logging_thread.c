/**
 * @file
 */


#include "logging_thread.h"
#include "dstrm_buffer.h"
#include "dsui_private.h"

#include <unistd.h>
#include <pthread.h>
#include <string.h>
#include <sys/syscall.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <misc.h>
#include <sys/signal.h>
#include <dsheader.h>
#include <dsentity.h>
#include <clksyncapi.h>
#include <net.h>
#include <mutex.h>
#include <stdlib.h>
#include <taskalias.h>
#include <dsui.h>

#if LOG_THREAD_DEBUG
#define log_debug(...) dprintf(__VA_ARGS__)
#else
#define log_debug(...)
#endif

void log_time_state(struct logging_thread *log)
{
	clksync_info_t *nfo = get_time_info();
	/*printf("time_state_nfo\ntv_sec: %ld\n tv_nsec: %ld\n"
			"ts: %llu\ntsckhz: %u\n", nfo->time.tv_sec,
			nfo->time.tv_nsec, nfo->ts, nfo->tsckhz);*/
	//FIXME: Why is this necessary?
	nfo->tsckhz = (unsigned int) nfo->tsckhz;
	// DSTRM_ADMIN_FAM/TIME_STATE
	log_admin_event(log, 12, 0, sizeof(*nfo), nfo);
	free(nfo);
}

#ifdef NOT_USED
/* not used */
static void *clksync_worker(void *param)
{
	struct logging_thread *log = param;
	sigset_t mask;
	int retval;

	// we don't want to handle signals
	sigfillset(&mask);
	if ((retval = pthread_sigmask(SIG_BLOCK, &mask, NULL))) {
		kusp_errno("pthread_sigmask", retval);
	}

	dprintf("clksync worker thread started for '%s'\n",
			log->filename);

	while(1) {
		log_time_state(log);
		sleep(1);
	}

	return NULL;
}
#endif


/**
 * Entry point into dsui logging thread. The parameter
 * must be a struct logging_thread
 *
 * @param param void by pthread convention, but must be an
 * initialized struct logging_thread
 * @retval NULL in all cases
 */
static void *logging_thread_run(void *param)
{
	struct logging_thread *self;
	int retval;
	sigset_t mask;

	/* Calling function in dsui.c and we pass the pid of this thread
	 * we do this so that when we do discovery we would be able to
	 * identify the logging thread that is being forked off by DSUI
	 */

	// FIXME: 
	// Bad way to get the thread id.
	set_logging_thread_pid(syscall(SYS_gettid));
	
	self = (struct logging_thread *)param;
//	task_alias_add_alias(0, "dskid");

	/* We don't want to handle signals */
	sigfillset(&mask);
	if ((retval = pthread_sigmask(SIG_BLOCK, &mask, NULL))) {
		kusp_errno("pthread_sigmask", retval);
	}

	log_debug("Logging thread started, PID=%d\n", gettid());
	log_debug("Logging entities to file '%s'.\n", self->filename);

	while (1) {
		struct dstrm_buffer *buffer;
		size_t size;
		void *data;

		km_mutex_lock(&self->queue.lock);

		while (self->queue.num_buffers == 0) {

			if (!self->running) {
				km_mutex_unlock(&self->queue.lock);
				goto finished;
			}
			log_debug("logging thread going to sleep\n");
			km_cond_wait(&self->queue.cond, &self->queue.lock);
			log_debug("logging thread woke up, %d buffers to write\n",
					self->queue.num_buffers);
		}
		buffer = __buffer_queue_dequeue(&self->queue);

		km_mutex_unlock(&self->queue.lock);

		size = buffer_size(buffer);
		data = buffer_pull(buffer, size);

		log_debug("Pulling %d bytes of data off buffer %d\n",
				size, buffer->page_num);

		logging_thread_write(self, data, size);

		release_buffer(buffer);

	}
finished:


	if (close(self->fd)) {
		kusp_errno("close", errno);
	}

	self->fd = -1;

	log_debug("Logging thread exiting.\n");


	return NULL;
}



void __logging_thread_write(struct logging_thread *self, const void *data, size_t size)
{
	int retval;
	while (size > 0) {
		retval = write(self->fd, data, size);
		if (retval < 0) {
			eprintf("Error writing data to file '%s': %s\n",
					self->filename, strerror(errno));
			exit(1);
			// FIXME: what should i do?
		} else {
			//log_debug("Wrote %d bytes to file\n", retval);
			size -= retval;
			data += retval;
			self->written += retval;
		}
	}
}


/**
 * Atomically write data to the logging thread's file descriptor
 */
void logging_thread_write(struct logging_thread *self, const void *data, size_t size)
{
	km_mutex_lock(&self->write_lock);
	__logging_thread_write(self, data, size);
	km_mutex_unlock(&self->write_lock);
}

/** t->fd is already set */
static int init_logging_thread(struct logging_thread *t)
{
	int retval;
	pthread_attr_t attr;
	size_t stacksize;

	struct dstream_header *header;

	t->running = 1;
	buffer_queue_init(&t->queue);
	t->written = 0;
	t->ref_count = 0;

	INIT_LIST_HEAD(&t->list_member);
	t->entity_count = 0;

	km_mutex_init(&t->write_lock, NULL);
	km_mutex_init(&t->entity_count_lock, NULL);

	retval = pthread_attr_init(&attr);

	// XXX: what stack size do we need?
	pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_JOINABLE);
	pthread_attr_getstacksize (&attr, &stacksize);
	log_debug("Logging thread stack size = %d\n", stacksize);

	retval = pthread_create(&t->thread, &attr, &logging_thread_run, t);
	if (retval) {
		kusp_errno("pthread_create", retval);
		return -1;
	}

	header = get_dstream_header();
	logging_thread_write(t, header, sizeof(*header));
	free(header);

	return 0;
}

int init_socket_logging_thread(struct logging_thread *t, char *hostname, int port)
{
	t->fd = setup_client(hostname, port);
	if (t->fd < 0) {
		eprintf("Can't connect to server %s:%d\n", hostname, port);
		return -1;
	}
	t->filename = hostname;
	return init_logging_thread(t);
}

/**
 * Create a logging thread.
 *
 * @param filename name of file to open and write data to
 */
int init_file_logging_thread(struct logging_thread *t, char *filename)
{
	/* O_CREAT: create file if it does not exist
	 * O_RDWR: open for reading and writing
	 * O_TRUNC: truncate size to 0
	 * mode will be 644 */
	t->fd = open(filename, O_CREAT | O_RDWR |  O_TRUNC,
		      S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH);
	t->filename = filename;

	if (t->fd < 0) {
		eprintf("Unable to open file '%s' for writing: %s\n",
				filename, strerror(errno));
		return -1;
	}

	return init_logging_thread(t);
}

/**
 * Terminate a logging thread and close whatever file it was
 * writing to. Does not free datastructure.
 *
 * @param self logging thread to terminate
 * @retval 0  success
 * @retval -1 failure
 */
int close_logging_thread(struct logging_thread *self) {

	int retval;
	km_mutex_lock(&self->write_lock);
	if (self->ref_count) {
		bprintf("Attempted to close in-use logging thread\n");
		km_mutex_unlock(&self->write_lock);
		return -1;
	}
	km_mutex_unlock(&self->write_lock);


	log_debug("called\n");

	// set the running bit to 0, and then wake up the logging
	// thread if it was asleep.
	km_mutex_lock(&self->queue.lock);
	self->running = 0;
	km_cond_broadcast(&self->queue.cond);
	km_mutex_unlock(&self->queue.lock);

	log_debug("waiting for thread to die\n");

	if ((retval = pthread_join(self->thread, NULL))) {
		kusp_errno("pthread_join", retval);
	}

	dprintf("File '%s' closed, %ld bytes written.\n",
			self->filename, self->written);
	return 0;
}

void log_admin_event(struct logging_thread *log, int id,
		int tag, size_t size, void *extradata)
{
	struct ds_event_record evt;
	evt.data_len = size;
	evt.time_stamp = get_tsc();
	evt.id = id;
	evt.event_tag = tag;

	km_mutex_lock(&log->write_lock);
	__logging_thread_write(log, &evt, sizeof(evt));
	__logging_thread_write(log, extradata, size);
	km_mutex_unlock(&log->write_lock);
}

