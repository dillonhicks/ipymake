#ifndef TASK_ALIAS_H
#define TASK_ALIAS_H
#include <stdio.h>
#include <string.h>
#include <stdlib.h>




static inline int task_alias_add_alias(pid_t pid, char *name)
{
	FILE *f = fopen("/proc/taskalias", "w");
	if (!f) {
		return -1;
	}
 	if (fprintf(f, "%d:%d:%s\n", pid, 0, name) < 0) {
		fclose(f);
		return -1;
	}
	fclose(f);

	return 0;
}

static inline int task_alias_add_alias_track(pid_t pid, char *name)
{
	
	FILE *f = fopen("/proc/taskalias", "w");
	if (!f) {
		return -1;
	}
 	if (fprintf(f, "%d:%d:%s\n", pid, 1, name) < 0) {
		fclose(f);
		return -1;
	}
	fclose(f);

	return 0;
}

static inline int task_alias_add_alias_unique(pid_t pid, char *name)
{
	FILE *f = fopen("/proc/taskalias", "w");
	if (!f) {
		return -1;
	}
 	if (fprintf(f, "%d:%d:%s\n", pid, 2, name) < 0) {
		fclose(f);
		return -1;
	}
	fclose(f);

	return 0;
}
#endif
