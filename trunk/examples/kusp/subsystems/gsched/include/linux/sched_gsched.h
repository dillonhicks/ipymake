#ifndef SCHED_GSCHED_H
#define SCHED_GSCHED_H

#define GSCHED_NAME_LEN 25

#define GSCHED_GO_MANAGED 0x01  /* Uninstall and destroy the group when it no longer has members */

#ifdef __KERNEL__
#include <linux/sched.h>
#include <linux/dski.h>

#define GSCHED_COMPTYPE_LINUX 0 /* only used by the linux member placeholder */
#define GSCHED_COMPTYPE_TASK 1
#define GSCHED_COMPTYPE_GROUP 2

#define GSCHED_MF_DEAD	0x01	/* logically removed, awaiting release */
#define GSCHED_MF_PROXY	0x02	/* special member used as a proxy */
#define GSCHED_MF_LINUX	0x04	/* member is in a Linux group */

/* Linux scheduling's psuedo-group name */
#define GSCHED_LINUX_GRP_NAME "GSCHED_LINUX_GRP"

#ifdef CONFIG_GROUPSCHED_DEBUG
#define GSCHED_DEBUG(fmt, args...) DSTRM_DEBUG(GSCHED, DEBUG, fmt, ## args)
#else
#define GSCHED_DEBUG(fmt, args...)
#endif

#ifdef CONFIG_GROUPSCHED_INIT
#define GSCHED_INIT(fmt, args...) printk(fmt, ## args)
#else
#define GSCHED_INIT(fmt, args...) 
#endif

/*
 * Required Proc File-system Struct
 *
 * Used to map entry into proc file table upon module insertion
 */
extern struct proc_dir_entry *gsched_proc_entry;
extern struct list_head gsched_grouplist;
extern struct mutex gsched_lock;

struct gsched_group;
struct gsched_member;

struct gsched_sdf {
	char *name;
	struct module *owner;
	struct list_head schedlist_entry;

	void (*insert_group)(struct gsched_group *);
	void (*remove_group)(struct gsched_group *);

	void (*setup_member)(struct gsched_group *, struct gsched_member *);
	void (*insert_member)(struct gsched_group *, struct gsched_member *);
	void (*remove_member)(struct gsched_group *, struct gsched_member *);
	void (*release_member)(struct gsched_group *, struct gsched_member *);
	void (*release_group)(struct gsched_group *);
	struct gsched_member *(*find_member)(struct gsched_group *group, char *member_name);

	int (*set_member_params)(struct gsched_group *, struct gsched_member *, void *, size_t);
	int (*get_member_params)(struct gsched_group *, struct gsched_member *, void *, size_t);
	int (*set_group_params)(struct gsched_group *, void *, size_t);
	int (*get_group_params)(struct gsched_group *, void *, size_t);
	
	void (*iterator_prepare)(struct gsched_group *, struct rq *rq);
	struct gsched_member *(*iterator_next)(struct gsched_group *, struct gsched_member *, struct rq *rq);
	void (*iterator_finalize)(struct gsched_group *, struct gsched_member *, struct rq *rq);
	int (*is_runnable)(struct gsched_group *, struct gsched_member *);

	int (*fork_member)(struct gsched_group *, struct gsched_member *, struct gsched_member *);
	void (*start_member)(struct gsched_group *, struct gsched_member *, struct rq *, int);
	void (*stop_member)(struct gsched_group *, struct gsched_member *, struct rq *, int);

	size_t per_group_datasize;
	size_t per_member_datasize;
	size_t per_cpu_datasize;
};

struct gsched_group {
	raw_spinlock_t lock;

	int opts; /* options settable by user code */
	struct list_head memberships;
	struct list_head group_members;
	struct list_head grouplist_entry;
	struct gsched_sdf *sdf;
	char name[GSCHED_NAME_LEN];
	void *sched_data;
	void *cpu_sched_data[NR_CPUS];

	int groupint1;
	struct list_head grouplist1;
	struct list_head grouplist2;

	atomic_t usage;
};

union gsched_member_ptr {
	struct task_struct *task;
	struct gsched_group *group;
};

struct gsched_member {
	int flags;
	int type;
	char name[GSCHED_NAME_LEN];
	void *sched_data;

	struct list_head group_entry;
	struct list_head samecomputation_entry;

	union gsched_member_ptr cptr;
	struct gsched_group *group;

	struct gsched_member *proxy;
	struct list_head sprxw_entry;

	int memint1;
	struct list_head memlist1;
	struct list_head memlist2;

	atomic_t usage;
	struct rcu_head rcu;
};

/*
 * Called from Linux scheduling framework (e.g. sched.c)
 */
void gsched_init(void);
int gsched_fork_task(struct task_struct *task);
void gsched_task_exit(struct task_struct *task);
void gsched_enqueue_task(struct rq *rq, struct task_struct *p, int wakeup);
void gsched_dequeue_task(struct rq *rq, struct task_struct *p, int sleep);
struct task_struct *gsched_pick_next_task(struct rq *rq, struct task_struct  *prev);
void gsched_task_dead(struct task_struct *prev);
void gsched_put_prev_task(struct rq *rq, struct task_struct *prev);
void gsched_set_curr_task(struct rq *rq);
void gsched_task_tick(struct rq *rq, struct task_struct *task, int queued);
void gsched_check_preempt_curr(struct rq *rq, struct task_struct *task, int sync);
void gsched_yield_task(struct rq *rq);
void gsched_stale_proxy_fixup(void);

/*
 * Called from the Group Scheduling module. These correspond to IOCTL commands
 */
int gsched_register_scheduler(struct gsched_sdf *sched);
void gsched_unregister_scheduler(struct gsched_sdf *sched);
int gsched_get_member_params(char *gname, char *mname, void *value, size_t size);
int gsched_set_member_params(char *gname, char *mname, void *value, size_t size);
int gsched_get_group_params(char *name, void *value, size_t size);
int gsched_set_group_params(char *name, void *value, size_t size);
int gsched_leave_group(char *group_name, char *member_name);
int gsched_create_group(char *group_name, char *sdf_name);
int gsched_group_join_group(char *group_name, char *addgroup_name, char *member_name);
int gsched_pid_join_group(char *group_name, pid_t pid, char *member_name);
int gsched_name_join_group(char *group_name, char *ccsm_name, int exclusive);
int gsched_destroy_group(char *name);
int gsched_set_exclusive_control(pid_t pid);
int gsched_clear_exclusive_control(pid_t pid);
int gsched_set_group_opts(char* name, int opts);
int gsched_get_group_opts(char* name, int* opts);

/*
 * Default routine used by SDFs
 */
struct gsched_member *gsched_default_find_member(struct gsched_group *group, char *name);

struct sprx_waiter_node {
	raw_spinlock_t		lock;
	struct task_struct	*owner_task;	/* only for assertions */
	struct list_head	owner_ent;	/* also buffer entry */
	struct sprx_waiter	*waiter;
	struct list_head	waiter_ent;
	struct task_struct	*via_task;
	struct rt_mutex		*via_lock;
	struct list_head	via_lock_ent;
};

struct sprx_waiter {
	raw_spinlock_t		lock;
	struct task_struct	*proxy_task;
	struct list_head	proxy_ent;	/* also buffer entry */
	struct list_head	nodes;
	struct sprx_waiter_node	*tnode;
	struct list_head	gsched_members;
};

/* For use by sdf to figure out what the last decision on the current cpu was */
pid_t gsched_last_choice(void);

void gsched_init_sprx_waiter(struct sprx_waiter *sprxw, struct task_struct *task);
void gsched_remove_sprx_waiter(struct sprx_waiter *sprxw, struct task_struct *task);
void gsched_setup_sprx_waiter(struct sprx_waiter *sprxw, struct task_struct *task);
void gsched_clean_sprx_waiter(struct sprx_waiter *sprxw);
void sprx_remove_proxy_member(struct task_struct *task, struct gsched_member *member);
void gsched_remove_sprx_proxy(struct sprx_waiter *sprxw, struct gsched_member *member);
void sprx_add_proxy_member(struct task_struct *task, struct gsched_member *member);
void gsched_add_sprx_proxy(struct sprx_waiter *sprxw, struct gsched_member *member);


/*
 * curr_waiters:	outstanding sprx waiters
 * max_waiter:		max outstanding sprx waiters
 * waiter_instances:	total sprx waiter instances
 * curr_nodes:		outstanding sprx nodes
 * max_nodes:		max outstanding sprx nodes
 * node_instances	total sprx node instances
 * max_chain_len	maximum observed lock chain length
 */
struct proxy_mgmt_stats {
	int curr_waiters;
	int max_waiters;
	int waiter_instances;
	int curr_nodes;
	int max_nodes;
	int node_instances;
	int max_chain_len;
};

/* in kernel/rtmutex.c */
extern struct proxy_mgmt_stats proxy_stats;

#endif /* __KERNEL__ */

#define GSCHED_TOP_GROUP_NAME "gsched_top_seq_group"

/*
 * A special member that is used to indicate that an sdf is
 * choosing linux. This member should not be operated on directly.
 */
extern struct gsched_member GSCHED_LINUX_CHOICE;

typedef struct grp_ioctl_create_group_s {
	char group_name[GSCHED_NAME_LEN];
	char sched_name[GSCHED_NAME_LEN];
} grp_ioctl_create_group_t;

#define GRP_IOCTL_PARAMETERS_READ   0
#define GRP_IOCTL_PARAMETERS_WRITE  1

typedef struct grp_ioctl_group_parameters_s {
	char group_name[GSCHED_NAME_LEN];
	int    rw;
	void * parameter_ptr;
	size_t size;
} grp_ioctl_group_parameters_t;

typedef struct grp_ioctl_member_parameters_s {
	char group_name[GSCHED_NAME_LEN];
	char member_name[GSCHED_NAME_LEN];
	int    rw;
	void * parameter_ptr;
	size_t size;
} grp_ioctl_member_parameters_t;

typedef struct grp_ioctl_pid_join_group_s {
	char group_name[GSCHED_NAME_LEN];
	char member_name[GSCHED_NAME_LEN];
	pid_t pid;
} grp_ioctl_pid_join_group_t;

typedef struct grp_ioctl_name_join_group_s {
	char group_name[GSCHED_NAME_LEN];
	char ccsm_name[GSCHED_NAME_LEN];
	int exclusive;
} grp_ioctl_name_join_group_t;

typedef struct grp_ioctl_exclusive_s {
	pid_t pid;
} grp_ioctl_exclusive_t;

typedef struct grp_ioctl_group_join_group_s {
	char group_name[GSCHED_NAME_LEN];
	char member_name[GSCHED_NAME_LEN];
	char add_group_name[GSCHED_NAME_LEN];
} grp_ioctl_group_join_group_t;

typedef struct grp_ioctl_leave_s {
	char group_name[GSCHED_NAME_LEN];
	char member_name[GSCHED_NAME_LEN];
} grp_ioctl_leave_t;

typedef struct grp_ioctl_destroy_group_s {
	char group_name[GSCHED_NAME_LEN];
} grp_ioctl_destroy_group_t;

typedef struct grp_ioctl_settop_group_s {
	char group_name[GSCHED_NAME_LEN];
} grp_ioctl_settop_group_t;

typedef struct grp_ioctl_set_group_opts_s {
	char group_name[GSCHED_NAME_LEN];
	int opts;
} grp_ioctl_set_group_opts_t;

typedef struct grp_ioctl_get_group_opts_s {
	char group_name[GSCHED_NAME_LEN];
	int* opts;
} grp_ioctl_get_group_opts_t;

typedef union grp_ioctl_param_u {
	grp_ioctl_create_group_t	create_group;
	grp_ioctl_group_parameters_t	group_parameters;
	grp_ioctl_member_parameters_t	member_parameters;
	grp_ioctl_pid_join_group_t	pid_join_group;
	grp_ioctl_name_join_group_t	name_join_group;
	grp_ioctl_group_join_group_t	group_join_group;
	grp_ioctl_leave_t		leave;
	grp_ioctl_destroy_group_t	destroy_group;
	grp_ioctl_exclusive_t		exclusive;
	grp_ioctl_set_group_opts_t      set_group_opts;
	grp_ioctl_get_group_opts_t      get_group_opts;
} grp_ioctl_param_union;

#define GSCHED_MAGIC 'g'

#define GRP_IOCTL_CREATE_GROUP       _IOW(GSCHED_MAGIC,  1, grp_ioctl_create_group_t)
#define GRP_IOCTL_PID_JOIN_GROUP     _IOW(GSCHED_MAGIC,  2, grp_ioctl_pid_join_group_t)
#define GRP_IOCTL_NAME_JOIN_GROUP    _IOW(GSCHED_MAGIC,  3, grp_ioctl_name_join_group_t)
#define GRP_IOCTL_GROUP_JOIN_GROUP   _IOW(GSCHED_MAGIC,  4, grp_ioctl_group_join_group_t)
#define GRP_IOCTL_DESTROY_GROUP      _IOW(GSCHED_MAGIC,  5, grp_ioctl_destroy_group_t)
#define GRP_IOCTL_LEAVE              _IOW(GSCHED_MAGIC,  6, grp_ioctl_leave_t)
#define GRP_IOCTL_GROUP_PARAMETERS   _IOWR(GSCHED_MAGIC, 7, grp_ioctl_group_parameters_t)
#define GRP_IOCTL_MEMBER_PARAMETERS  _IOWR(GSCHED_MAGIC, 8, grp_ioctl_member_parameters_t)
#define GRP_IOCTL_SET_EXCLUSIVE	     _IOW(GSCHED_MAGIC,  9, grp_ioctl_exclusive_t)
#define GRP_IOCTL_CLEAR_EXCLUSIVE    _IOW(GSCHED_MAGIC, 10, grp_ioctl_exclusive_t)
#define GRP_IOCTL_SET_GROUP_OPTS     _IOW(GSCHED_MAGIC, 11, grp_ioctl_set_group_opts_t)
#define GRP_IOCTL_GET_GROUP_OPTS     _IOW(GSCHED_MAGIC, 12, grp_ioctl_get_group_opts_t)
#endif
