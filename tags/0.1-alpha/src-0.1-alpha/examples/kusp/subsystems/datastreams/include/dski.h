#ifndef DATASTREAMS_DSKI_H
#define DATASTREAMS_DSKI_H
/* Changed from asm/ioctl.h,
 * Pulled iotcl.h from 2.6.24/include/asm-x86
 * to resolve lack of includes, so you didn't
 * need the kernel source to build the dski
 * python modules.
 */
#include <asm/ioctl.h>
#include <dsentity.h>

/* Entity configure flags */
#define ENTITY_ENABLE	0x01
#define ENTITY_DISABLE	0x02

#define DS_STR_LEN 256
#define DSKI_DIR "datastreams"
#define CHAN_DIR "channels"

/* channel flags */
#define DS_CHAN_TRIG	0x01
#define DS_CHAN_CONT	0x02
#define DS_CHAN_MMAP    0x04

/* Explicit on/off flag for datastreams */
#define DS_DSTRM_ON	0x01

/* Available filters */
#define FLTR_TAG "Tag Filter"
#define FLTR_PID "PID Filter"
#define FLTR_DSCVR "Discovery Filter"
#define FLTR_SMONITOR "System Monitoring Filter"
#define FLTR_TASK "CCSM based per-task filter"
#define FLTR_CCSM_STRACE "CCSM based strace filter"
#define FLTR_CCSM_TRACEME "CCSM based traceme filter"

#define	FLTR_ACCEPT 1
#define	FLTR_REJECT 2
#define	FLTR_PASS   3
#define	FLTR_NEGATE 4

enum {
// for SystemMonitor Purposes.
	OPEN,
// For SystemMonitor Purposes.
	PINFO,
	SYSTEM_CALL,
// For SystemMonitor Purposes.
	PSYS,
	IPS_MAX
};

struct dski_pid_filter_elem {
	char name[NAME_MAX+1];
	long pid;
	int match_response;
};

struct dski_pid_filter_ctrl {
	size_t pid_array_size;
	struct dski_pid_filter_elem *pids;
	int default_response;
};

struct dski_task_filter_ctrl {
	char *set_name;
	long pid;
	int match_response;
};

struct dski_dscvr_ip {
	char fname[NAME_MAX+1];
	char ename[NAME_MAX+1];
	unsigned int eid;
	struct dski_dscvr_ip *next;
};

struct dski_dscvr_filter_ctrl {
	char *name;
};

// The system Monitor structure that encapsulates the information that the active
// filter requires to process certain information that one requires.
struct dski_smonitor_filter_ctrl {
	char *procfile_name;
	struct dski_monitor_list *lists;
	struct dski_monitor_sysList *sysLs;
	int userid;
};

struct dski_daemontrace_filter_ctrl {
	int pid;
	char *process_name;
	struct dski_dscvr_ip *eips;
};

union dski_ioc_filter_ctrl_params {
	struct dski_dscvr_filter_ctrl dscvr_filter;
	struct dski_pid_filter_ctrl pidfilter;
	struct dski_task_filter_ctrl task_filter;
	struct dski_smonitor_filter_ctrl smon_filter;
	struct dski_daemontrace_filter_ctrl dtFilter;
};

struct dski_ioc_filter_ctrl {
	char datastream[NAME_MAX+1];
	char filtername[NAME_MAX+1];
	union dski_ioc_filter_ctrl_params params;
};

// Used to hold a list of shared libraries that we want to track from the kernel side.
struct dski_monitor_list {
	char shLibName[NAME_MAX+1];
	struct dski_monitor_list *next;
};

// Used to hold a list of system calls that we want to track from the kernel side.
struct dski_monitor_sysList {
	int num;
	struct dski_monitor_sysList *next;
};

struct dski_ioc_channel_ctrl {
	size_t subbuf_size;
	size_t num_subbufs;
	int timeout;
	unsigned int flags;
	int channel_id;
};

struct dski_ioc_datastream_ctrl {
	char name[DS_STR_LEN];
	int channel_id;
};

struct dski_ioc_datastream_ip_info {
	char group[DS_STR_LEN];
	char name[DS_STR_LEN];
	char edf[DS_STR_LEN];
	char desc[DS_STR_LEN];
	unsigned int type;
	unsigned int id;
};

struct dski_ioc_datastream_ip_ctrl {
	struct dski_ioc_datastream_ip_info *info;
	size_t size;
};

struct dski_ioc_entity_ctrl {
	int flags;
	unsigned int id;
	char datastream[DS_STR_LEN];
	union ds_entity_info *config_info;
};

union dski_ioctl_param {
	struct dski_ioc_datastream_ctrl		datastream_ctrl;
	struct dski_ioc_channel_ctrl		channel_ctrl;
	struct dski_ioc_entity_ctrl		entity_ctrl;
	struct dski_ioc_datastream_ip_ctrl	ip_info;
	struct dski_ioc_filter_ctrl		filter_ctrl;
};

#define DSKI_DS_CREATE		_IOW('a',  2, struct dski_ioc_datastream_ctrl)
#define DSKI_CHANNEL_OPEN	_IOW('a',  3, struct dski_ioc_channel_ctrl)
#define DSKI_CHANNEL_FLUSH	_IOW('a',  4, struct dski_ioc_channel_ctrl)
#define DSKI_CHANNEL_CLOSE	_IOW('a',  6, struct dski_ioc_channel_ctrl)
#define DSKI_GET_NAMESPACE	_IOW('a',  5, struct dski_ioc_instance_info)
#define DSKI_DS_DESTROY		_IOW('a',  7, struct dski_ioc_datastream_ctrl)
#define DSKI_IPS_QUERY		_IOWR('a', 9, struct dski_ioc_datastream_ip_ctrl)
#define DSKI_RELAY_DIR		_IO('a',  10)
#define DSKI_ENTITY_CONFIGURE	_IOW('a', 11, struct dski_ioc_entity_ctrl)
#define DSKI_FILTER_APPLY	_IOW('a', 12, struct dski_ioc_filter_ctrl)
#define DSKI_DS_ASSIGN_CHAN	_IOW('a', 13, struct dski_ioc_datastream_ctrl)
#define DSKI_DS_ENABLE		_IOW('a', 14, struct dski_ioc_datastream_ctrl)
#define DSKI_DS_DISABLE		_IOW('a', 15, struct dski_ioc_datastream_ctrl)
#endif
