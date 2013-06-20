#ifndef GSCHED_SDF_SAFE_H
#define GSCHED_SDF_SAFE_H
#include <linux/sched_gsched.h>

#define SAFE_CMD_SAME      1
#define SAFE_CMD_NON_LINUX 2
#define SAFE_CMD_TO        3

#define SAFE_SDF_NAME "sdf_safe"

struct safe_cmd {
	unsigned int cmd;
	union {
		struct timespec to;
		unsigned int count;
	} value;
};

#endif
