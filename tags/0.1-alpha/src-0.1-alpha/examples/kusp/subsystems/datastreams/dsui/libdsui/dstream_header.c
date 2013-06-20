#include <fcntl.h>
#include <stdio.h>
#include <time.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <dsheader.h>
#include <errno.h>
#include <config.h>
#include <kusp_common.h>
#include <misc.h>

struct dstream_header *get_dstream_header() {
	struct dstream_header *h = malloc(sizeof(*h));

	h->magic_number = DSTREAM_MAGIC_NUMBER;
	h->sz_int = sizeof(int);
	h->sz_long = sizeof(long);
	h->sz_short = sizeof(short int);
	h->sz_long_long = sizeof(long long int);
	h->sz_ptr = sizeof(void *);
	memset(h->hostname, 0, 80);
	gethostname(h->hostname, 80);

	return h;
}
