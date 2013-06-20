/**
 * This file provides user programs with the API of the clock synchronization
 * module in KURT.
 *
 * @file libclksync/clksyncapi.c
 * @addtogroup clksync Clock Sync
 *
 * This file provides user programs with the API of the clock synchronization
 * module in KURT.
 */
#include <sys/types.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <kusp_common.h>
#include <clksyncapi.h>
#include <sys/time.h>
#include <time.h>
#include <stdlib.h>
#include <stdint.h>
#include <misc.h>
#include <unistd.h>


#undef dprintf
#define dprintf(...)


clksync_info_t *get_time_info()
{
	clksync_info_t *nfo = malloc(sizeof(*nfo));
	int fd = clksync_open();
	if (fd >= 0) {
		clksync_get_info(fd, nfo);
		dprintf("CLKSYNC reports TSC/sec is %llu\n",
			nfo->tsckhz);
		close(fd);
	} else {
		register cycles_t tsc = 0;
		uint64_t tmp;
		struct timeval tv;


#ifdef __linux__
		FILE *p = fopen("/proc/cpuinfo", "r");
		char buf[160];

		dprintf("Clksync not available, getting cpu speed from /proc/cpuinfo\n");
		while (fgets(buf, 160, p)) {
			if (strncmp(buf, "cpu MHz", 7)) {
				continue;
			}
			char *context;
			char *mhz = strtok_r(buf, ":", &context);
			mhz = strtok_r(NULL, ":", &context);

			tsc = (cycles_t)(atof(mhz) * 1000);
			break;
		}
		nfo->tsckhz = tsc;
		fclose(p);

#else
		iprintf("Calibrating clock...\n");

		// hack to find tsckhz
		tsc = get_tsc();
		sleep(1);
		tsc = get_tsc() - tsc;
		nfo->tsckhz = tsc / 1000;
#endif

		// populate struct fields. see
		// include/linux/clocksource.h
		// for explanation of shift and mult
		nfo->shift = 22;
		tmp = ((uint64_t)1000000) << 22;
		tmp = tmp + (nfo->tsckhz / 2);
		tmp = tmp / nfo->tsckhz;
		nfo->mult = (unsigned int)tmp;
		nfo->ts = get_tsc();
		gettimeofday(&tv, NULL);
		nfo->time.tv_sec = tv.tv_sec;
		nfo->time.tv_nsec = tv.tv_usec * 1000;
		dprintf("TSC/sec is %llu\n",
			nfo->tsckhz * 1000);
	}
	return nfo;
}







/**
 * Open the clock sync device (/dev/clksync)
 *
 * @retval File descriptor of open /dev/clksync file
 * @retval Negative value on error
 */
int clksync_open(void)
{
	int temp_fd = open(CLKSYNC_DEV_FILE, 0);

	if (temp_fd < 0)
		return -errno;

	return temp_fd;
}

/**
 * Set the TSC kHz value. This is conceptually TSCs/Millisecond
 *
 * @param fd File descriptor of open clock sync device
 * @param tsckhz New kHz value of the system
 *
 * @retval 0 for success
 * @retval Negative value otherwise
 */
int clksync_set_freq(int fd, unsigned long tsckhz)
{
	clksync_info_t nfo;
	int ctr = 0;

	nfo.tsckhz = tsckhz;
	nfo.flags = CLKSYNC_ADJ_FREQ;


	if (ioctl(fd, CLKSYNC_IOCTL, &nfo) < 0) {
		deprintf("Unable to set CPU frequency\n");
		return -1;
	}

	do {
		if (clksync_get_info(fd, &nfo)) {
			deprintf("Unable to read current cpu frequency\n");
			return -1;
		}
		if (tsckhz == nfo.tsckhz) {
			break;
		}
		dprintf("propagate new freq: %lld -> %ld\n",
			nfo.tsckhz, tsckhz);
		usleep(12500);
		if (++ctr == 100) {
			deprintf("CPU frequency did not propagate\n");
			return -1;
		}
	} while (1);

	return 0;
}

/**
 * Adjust the current time of the system. The valu of the timespec parameter
 * is added to the current system time.
 *
 * @param fd File descriptor of open clock sync device
 * @param adj Adjust to be added into the current system time
 *
 * @retval 0 for success
 * @retval Negative value otherwise, check errno
 */
int clksync_adj_time(int fd, struct timespec *adj)
{
	clksync_info_t nfo;

	nfo.time = *adj;
	nfo.flags = CLKSYNC_ADJ_TIME;

	if (ioctl(fd, CLKSYNC_IOCTL, &nfo) < 0) {
		return -1;
	}

	return 0;
}

/**
 * Retrieve the values for TSCs/Millisecond, current system time, and a TSC
 * value. The TSC value and the current system time returned are taken as close
 * together as possible and thus try to reflect a correspondence between current
 * time and TSC value.
 *
 * @param fd File descriptor for open clock sync device
 * @param nfo Pointer to clksync_info_t structure to be filled with retreived data.
 *
 * @retval 0 for success
 * @retval Negative value otherwise, check errno
 */
int clksync_get_info(int fd, clksync_info_t * nfo)
{
	nfo->flags = CLKSYNC_GET_INFO;

	if (ioctl(fd, CLKSYNC_IOCTL, nfo) < 0) {
		return -1;
	}
	return 0;
}

int clksync_set_device(int fd, char *name)
{
	clksync_info_t nfo;
	nfo.flags = CLKSYNC_SET_DEV;
	nfo.device_name = name;
	nfo.size = strlen(name) + 1;

	if (ioctl(fd, CLKSYNC_IOCTL, &nfo) < 0) {
		return -1;
	}
	return 0;
}

int clksync_set_irq(int fd, int irq)
{
	clksync_info_t nfo;
	nfo.flags = CLKSYNC_SET_IRQ;
	nfo.irq = irq;
	if (ioctl(fd, CLKSYNC_IOCTL, &nfo) < 0) {
		return -1;
	}
	return 0;
}


