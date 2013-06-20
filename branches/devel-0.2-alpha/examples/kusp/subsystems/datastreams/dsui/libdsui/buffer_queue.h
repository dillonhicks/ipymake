/** @file */
#ifndef _BUFFER_QUEUE_H_
#define _BUFFER_QUEUE_H_

#include <dslist.h>
#include <mutex.h>
#include "dstrm_buffer.h"

/**
 * a datastructure to represent a queue of buffers
 */
struct dstrm_buffer_queue {
	/// we are the head of the list
	struct dstrm_list_head list;

	/// number of buffers in this queue
	int num_buffers;

	/// lock to protect contents of queue
	pthread_mutex_t lock;

	/// condition variable, broadcasted whenever elements are added/removed
	pthread_cond_t cond;

};


int buffer_queue_init(struct dstrm_buffer_queue *queue);

void buffer_queue_reset_front(struct dstrm_buffer_queue *queue);

struct dstrm_buffer *buffer_queue_front(struct dstrm_buffer_queue *queue);
struct dstrm_buffer *__buffer_queue_front(struct dstrm_buffer_queue *queue);

struct dstrm_buffer *buffer_queue_back(struct dstrm_buffer_queue *queue);
struct dstrm_buffer *__buffer_queue_back(struct dstrm_buffer_queue *queue);

struct dstrm_buffer *buffer_queue_dequeue(struct dstrm_buffer_queue *queue);
struct dstrm_buffer *__buffer_queue_dequeue(struct dstrm_buffer_queue *queue);

void buffer_queue_enqueue(struct dstrm_buffer_queue *queue, struct dstrm_buffer *buffer);
void __buffer_queue_enqueue(struct dstrm_buffer_queue *queue, struct dstrm_buffer *buffer);

void buffer_queue_push(struct dstrm_buffer_queue *queue, struct dstrm_buffer *buffer);
void __buffer_queue_push(struct dstrm_buffer_queue *queue, struct dstrm_buffer *buffer);


#endif
