#ifndef CLKSYNC_API_H
#define CLKSYNC_API_H

#include <time.h>
#include <linux/clksync.h>

/* Path to utime device file */
#define CLKSYNC_DEV_FILE "/dev/clksync"

int clksync_open(void);
int clksync_set_freq(int fd, unsigned long tsckhz);
int clksync_adj_time(int fd, struct timespec *adj);
int clksync_get_info(int fd, clksync_info_t *nfo);
int clksync_set_device(int fd, char *name);
clksync_info_t *get_time_info();
int clksync_set_irq(int fd, int irq);

#endif
