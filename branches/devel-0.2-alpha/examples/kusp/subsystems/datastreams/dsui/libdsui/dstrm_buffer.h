/**
 * @file
 */

#ifndef _DSUI_BUFFER_H_
#define _DSUI_BUFFER_H_

#include <dslist.h>
#include "pool.h"

/**
 * a structure to represent a chunk of memory used as a buffer
 */
struct dstrm_buffer {
	/// protected by the queue's lock
	struct dstrm_list_head list;

	/// the pool this buffer was obtained from
	struct dstrm_pool *pool;
	int page_num;

	/// boundaries of the buffer memory
	void *buffer_start;
	void *buffer_end;

	/// boundaries of the data stored in the buffer
	void *data_start;
	void *data_end;

};

/**
 * get the remaining space inside a buffer
 *
 * @param buffer Buffer to examine
 * @retval Bytes of remaining space in the buffer
 */
static inline unsigned int buffer_tailroom(struct dstrm_buffer *buffer)
{
	return (unsigned int)(buffer->buffer_end - buffer->data_end);
}

/**
 * get the amount of data being stored in a buffer
 *
 * @param buffer Buffer to examine
 * @retval Bytes of data stored in the buffer
 */
static inline unsigned int buffer_size(struct dstrm_buffer *buffer)
{
	return (unsigned int)(buffer->data_end - buffer->data_start);
}

void *buffer_put(struct dstrm_buffer *buffer, int size);
void *buffer_pull(struct dstrm_buffer *buffer, int size);
void buffer_reset(struct dstrm_buffer *buffer);

#endif

