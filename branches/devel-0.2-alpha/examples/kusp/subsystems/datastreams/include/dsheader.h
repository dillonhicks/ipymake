/**
 * @file
 */

#ifndef _DSTREAM_HEADER_H_
#define _DSTREAM_HEADER_H_
#include <stdint.h>

#define DSTREAM_MAGIC_NUMBER (uint32_t)(0x1abcdef1)

struct dstream_header {
	uint32_t magic_number;
	
	uint32_t sz_int;
	uint32_t sz_long;
	uint32_t sz_short;
	uint32_t sz_long_long;
	uint32_t sz_ptr;

	char hostname[80];
} __attribute__ ((packed));

struct dstream_header *get_dstream_header(void);


#endif				/* _DSTREAM_H_ */
