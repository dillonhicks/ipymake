/**
 * @file
 * @author Noah Watkins
 * @author Andrew Boie
 * @addtogroup Taskmapper
 * Taskmapper is the successor to PIDNAME
 */

#include <linkedlist.h>
#include <sys/types.h>
#ifndef _TASK_MAPPER_H_
#define _TASK_MAPPER_H_


// ioctl wrappers
extern int tm_open(void);
extern int tm_printk_maps(int fd);
extern int tm_create_mapping(int fd, pid_t pid, char *name);
extern int tm_query_mappings(int fd, char *name, pid_t **pid, int *count);

// higher-level functions
extern int tm_register(char *name);
extern list_t *tm_lookup(char *name);

#endif
