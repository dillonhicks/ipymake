#ifndef TASKMAPPER_H
#define TASKMAPPER_H

#ifdef __KERNEL__
#include <linux/hash_map.h>
#include <linux/sched.h>
#include <linux/ioctl.h>

struct taskmap_callback {
	int (*func)(struct taskmap_callback *cb);
	struct hkey_callback hkey_cb;
	struct task_struct *task;
};

int taskmap_add_task(pid_t pid, char *name);
void taskmap_remove_task(struct task_struct *task);
int taskmap_lookup(char *name, pid_t *pids, int maxret);
int taskmap_add_callback(char *name, struct taskmap_callback *cb, int update);
#endif

#define TASKMAP_NAMELEN 30

struct taskmap_mapping {
	pid_t pid;
	char name[TASKMAP_NAMELEN];
};

/* change ioctl copy_to_user if you change locatin of count in this struct */
struct taskmap_query {
	int count;
	pid_t *pids;
	char name[TASKMAP_NAMELEN];
};

union taskmap_ioctl {
	struct taskmap_mapping map;
	struct taskmap_query query;
};

#define TM_MAGIC_NUM 'k'
#define TASKMAP_ADD_TASK	_IOW(TM_MAGIC_NUM, 1, struct taskmap_mapping)
#define TASKMAP_LOOKUP		_IOWR(TM_MAGIC_NUM, 2, struct taskmap_query)
#define TASKMAP_PRINT_MAPS	_IO(TM_MAGIC_NUM, 3)

#endif
