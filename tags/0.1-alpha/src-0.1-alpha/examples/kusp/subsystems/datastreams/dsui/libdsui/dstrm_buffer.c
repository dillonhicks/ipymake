/**
 * @file dstrm_buffer.c
 * @author Andrew Boie
 */

#include "dstrm_buffer.h"
#include <kusp_common.h>

// @@@@@@@@ Buffer Functions @@@@@@@@@


/**
 * Clear the contents of a buffer so that it may be used again
 */
void buffer_reset(struct dstrm_buffer *buffer)
{
	buffer->data_start = buffer->buffer_start;
	buffer->data_end = buffer->buffer_start;
}

/**
 * Reserve space for data inside a buffer and return a pointer to it.
 *
 * @param buffer	buffer to write data to
 * @param size		size in bytes to reserve
 * @retval A pointer to the reserved region of memory inside the buffer
 */
void *buffer_put(struct dstrm_buffer *buffer, int size)
{
	void *retval;
#ifdef KUSP_DEBUG
        int available_space = buffer_tailroom(buffer);
        if (size > available_space) {
                bprintf("Buffer put (%d) exceeds available room in buffer (%d)\n",
                                size, available_space);
                return NULL;
        }
#endif
	retval = buffer->data_end;
        buffer->data_end += size;

        return retval;
}

/**
 * retrieve memory from a buffer, returning a pointer to it.
 * You will need to copy or otherwise use this data before the buffer
 * is released.
 *
 * @param buffer	buffer to fetch data from
 * @param size		size of data to fetch
 * @retval		A pointer to data retrieved from buffer.
 */
void *buffer_pull(struct dstrm_buffer *buffer, int size)
{
	void *retval;
#ifdef KUSP_DEBUG
	int bsize = buffer_size(buffer);
	if (size > bsize) {
		bprintf("Buffer pull (%d) exceeds available room in buffer (%d)\n",
				size, bsize);
	}
#endif
	retval = buffer->data_start;
	buffer->data_start += size;

	return retval;
}

// @@@@@@ Buffer List Functions @@@@@@@@


