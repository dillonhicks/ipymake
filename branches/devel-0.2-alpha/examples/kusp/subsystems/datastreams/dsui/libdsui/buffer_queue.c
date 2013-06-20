/**
 * @author Andrew Boie
 * @file
 */

#include <dslist.h>
#include <mutex.h>
#include "buffer_queue.h"

/**
 * Create a new empty buffer list.
 *
 * @param bqueue pointer to uninitialized buffer queue
 */
int buffer_queue_init(struct dstrm_buffer_queue *bqueue)
{
	INIT_LIST_HEAD(&bqueue->list);
	// initialize other variables
	bqueue->num_buffers = 0;

	km_mutex_init(&bqueue->lock, NULL);

	km_cond_init(&bqueue->cond, NULL);

	return 0;
}



void buffer_queue_reset_front(struct dstrm_buffer_queue *queue)
{
	struct dstrm_buffer *buffer;
	km_mutex_lock(&queue->lock);

	buffer = __buffer_queue_front(queue);
	if (buffer) {
		buffer_reset(buffer);
	}

	km_mutex_unlock(&queue->lock);
}


/**
 * Return the buffer at the front of the queue (the first item
 * to be inserted)
 */
struct dstrm_buffer *__buffer_queue_front(struct dstrm_buffer_queue *queue) {
	if (dstrm_list_empty(&queue->list)) {
		return NULL;
	}

	return dstrm_list_entry(queue->list.next, struct dstrm_buffer, list);
}

struct dstrm_buffer *buffer_queue_front(struct dstrm_buffer_queue *queue)
{
	struct dstrm_buffer *buffer;

	km_mutex_lock(&queue->lock);

	buffer = __buffer_queue_front(queue);

	km_mutex_unlock(&queue->lock);
	return buffer;
}

/**
 * Return the buffer at the back of the queue (the last or most
 * recently inserted item)
 */
struct dstrm_buffer *__buffer_queue_back(struct dstrm_buffer_queue *queue) {
	if (dstrm_list_empty(&queue->list)) {
		return NULL;
	}

	return dstrm_list_entry(queue->list.prev, struct dstrm_buffer, list);
}
struct dstrm_buffer *buffer_queue_back(struct dstrm_buffer_queue *queue)
{
	struct dstrm_buffer *buffer;

	km_mutex_lock(&queue->lock);

	buffer = __buffer_queue_back(queue);

	km_mutex_unlock(&queue->lock);
	return buffer;
}

/**
 * Remove a buffer from the front of the queue, and
 * return it. This wakes up anyone sleeping on the queue's
 * condition variable.
 *
 * @param queue queue to dequeue
 * @return The buffer removed from the head of the queue
 */
struct dstrm_buffer *buffer_queue_dequeue(struct dstrm_buffer_queue *queue)
{
	struct dstrm_buffer *buffer;

	km_mutex_lock(&queue->lock);

	buffer = __buffer_queue_dequeue(queue);

	km_mutex_unlock(&queue->lock);

	return buffer;
}

struct dstrm_buffer *__buffer_queue_dequeue(struct dstrm_buffer_queue *queue)
{
	struct dstrm_buffer *buffer;

	buffer = __buffer_queue_front(queue);

	if (buffer == NULL) {
		return NULL;
	}

	dstrm_list_del(&buffer->list);
	queue->num_buffers--;

	km_cond_broadcast(&queue->cond);

	return buffer;
}

/**
 * Add an empty buffer to the tail of a queue. This wakes up
 * anyone sleeping on the queue's condition variable.
 *
 * @param queue queue to add buffer to
 * @param buffer buffer to place at end of queue
 */
void buffer_queue_enqueue(struct dstrm_buffer_queue *queue, struct dstrm_buffer *buffer)
{
	km_mutex_lock(&queue->lock);

	__buffer_queue_enqueue(queue, buffer);

	km_mutex_unlock(&queue->lock);

}

void __buffer_queue_enqueue(struct dstrm_buffer_queue *queue, struct dstrm_buffer *buffer)
{
	dstrm_list_add_tail(&buffer->list, &queue->list);
	queue->num_buffers++;

	km_cond_broadcast(&queue->cond);
}

/**
 * Add an empty buffer to the tail of a queue. This wakes up
 * anyone sleeping on the queue's condition variable.
 *
 * @param queue queue to add buffer to
 * @param buffer buffer to place at end of queue
 */
void buffer_queue_push(struct dstrm_buffer_queue *queue, struct dstrm_buffer *buffer)
{
	km_mutex_lock(&queue->lock);

	__buffer_queue_push(queue, buffer);

	km_mutex_unlock(&queue->lock);

}

void __buffer_queue_push(struct dstrm_buffer_queue *queue, struct dstrm_buffer *buffer)
{
	dstrm_list_add(&buffer->list, &queue->list);
	queue->num_buffers++;

	km_cond_broadcast(&queue->cond);
}

