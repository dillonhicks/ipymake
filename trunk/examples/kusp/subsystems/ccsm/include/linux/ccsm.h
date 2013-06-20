#ifndef CCSM_H
#define CCSM_H

/* Maximum set name length */
#define CCSM_MAX_NAME_LEN 100

#ifdef __KERNEL__

#include <linux/list.h>
#include <linux/module.h>

/* CCSM specific error constants */
#define CCSM_ERROR_SEVERE		1
#define CCSM_ERROR_NO_SUCH_SET		2
#define CCSM_ERROR_NO_SUCH_MEMBER	3
#define CCSM_ERROR_SET_ALREADY_EXISTS	4

/* Used to define the hash table bit size */
/*FIXME.J what exactly is CONFIG_BASE_SMALL */
#define CCSM_HASH_BITS (CONFIG_BASE_SMALL ? 4 : 8)


/* 
 * ===============================================
 *             CCSM Data Structures
 * ===============================================
 */

extern struct mutex ccsm_mutex;

extern struct list_head ccsm_master_list;

/*
 * Required Proc File-system Struct
 *
 * Used to map entry into proc file table upon module insertion
 */
extern struct proc_dir_entry *proc_entry;

/*
 * Series of counters used to ensure generation of unique names between
 * components and between multiple, concurrent runs of the same application.
 */
extern int ccsm_task_name_counter;
extern int ccsm_pipe_name_counter;
extern int ccsm_fifo_name_counter;
extern int ccsm_shm_name_counter;
extern int ccsm_socket_name_counter;
extern int ccsm_file_name_counter;
extern int ccsm_mutex_name_counter;
extern int ccsm_generic_name_counter;

/*
 * Bucket structure for initial hash table implementation
 *
 * lock:	lock protecting access/membership on set_list
 * set_list:	list of sets whose names fall into this hash table bucket
 */
struct ccsm_hash_table_bucket {
	spinlock_t lock;
	struct list_head set_list;
};

/*
 * Creating our global hash table for initial hash table implementation
 */
extern struct ccsm_hash_table_bucket ccsm_name_table[1 << CCSM_HASH_BITS];

/*
 * Creating our global hash table for initial hash table implementation
 */
extern struct ccsm_hash_table_bucket ccsm_id_table[1 << CCSM_HASH_BITS];

/*
 * Union to be used as component handle
 *
 * Currently only one component type:
 * task:	member is of type task_struct
 */
union ccsm_component_ptr {
	struct task_struct *task;
	struct ccsm_set    *set;
};

#if 0
struct ccsm_component_id {
	unsigned int        type;
	struct kref         kref;
	struct list_head    table_entry;
	struct ccsm_set    *set;
};
#endif

/*
 * Data structure representing a set
 *
 * flags:		bit flags for set options and properties
 * name:		unique name of this set
 * compid:		structure holding unique identifier for component set
 *
 * comp_ptr:		if this is a component set, this is the pointer to the
 *                      component
 * members:		list of member structs for this set
 *
 * call_backs:		list of CCSM - GS callbacks for this set
 *
 * hash_table_entry:	entry into the global CCSM hash table
 * id_table_entry:	entry into the global CCSM ID hash table (only for
 *                      component sets)
 *
 * kref:		kernel reference count
 */
struct ccsm_set {
	unsigned int              flags;
	char                      name[CCSM_MAX_NAME_LEN + 1];
#if 0
	struct ccsm_component_id *compid;
#endif
	unsigned int              type;
	unsigned int		  id;
	void                     *handle;
#if 0
	union ccsm_component_ptr  comp_ptr;
#endif
	struct list_head          members;
	struct list_head	  memberships;

	struct list_head          call_backs;

	struct list_head          name_table_entry;
	struct list_head          id_table_entry;
	struct list_head          master_entry;

	struct kref               kref;
};

/* Flag indicating singleton status of set */
#define CCSM_EMPTY_FLAG		  0x0
#define CCSM_COMPONENT_SET	  0x1
#define CCSM_COMPOSIT_SET         0x2
#define CCSM_ADD_CHILD_ON_FORK    0x4
#define CCSM_ON_SIGNAL		  0x8
#define CCSM_ADD_ON_SOCKET_SR	 0x10
#define CCSM_ADD_ON_PIPE_RW	 0x20
#define CCSM_ADD_FB		 0x40
#define CCSM_ADD_RB		 0x80
#define CCSM_ADD_USING_HARDIRQ	0x100
#define CCSM_ADD_USING_SOFTIRQ	0x200

/* List of CCSM component types */
#define CCSM_TYPE_TASK   0x1
#define CCSM_TYPE_PIPE   0x2
#define CCSM_TYPE_FIFO   0x4
#define CCSM_TYPE_SHM    0x8
#define CCSM_TYPE_SOCKET 0x10
#define CCSM_TYPE_FILE   0x20
#define CCSM_TYPE_MUTEX  0x40
#define CCSM_TYPE_FUTEX  0x80

/*
 * Data structure allowing a set or component set to be a member of multiple
 * sets.
 *
 * owner:		set that owns this member
 * owner_entry:		membership on the owner's member list
 *
 * set:			set that this member points to
 * set_entry:		membership on the member set's list so that it contains
 *                      a list of all entries in other sets.
 */
struct ccsm_member {
	struct ccsm_set *owner;
	struct list_head owner_entry;

	struct ccsm_set *set;
	struct list_head set_entry;
};


/* CCSM - Groupsched callback mechanism */
struct ccsm_callback {
	struct ccsm_set *set;
	struct list_head set_list_entry;
	unsigned int conditions;
	void *args;
	size_t size;
	void (*func)(unsigned int condition,
			struct ccsm_callback *cbp,
			struct ccsm_set *set);
};

/* List of CCSM Callback Condition Flags */
#define CCSM_CONDITION_NAME_BINDING		0x1
#define CCSM_CONDITION_MEMBER_ADDITION		0x2
#define CCSM_CONDITION_MEMBER_SUBTRACTION	0x4

#define CCSM_CONDITION_SET_MEMBERSHIP_CHANGE	0x6
#define CCSM_CONDITION_SET_DELETION		0x8

/* 
 * ===============================================
 *    CCSM - Callback Functions
 * ===============================================
 */
int ccsm_register_callback(char *name, struct ccsm_callback *cbp);
int ccsm_register_callback_and_call(char *name, struct ccsm_callback *cbp);
int ccsm_remove_callback(struct ccsm_callback *cbp);


/* 
 * ===============================================
 *          Linux Internal API Functions
 * ===============================================
 */
void ccsm_task_exit(struct task_struct *task);

/* 
 * ===============================================
 *             Public API Functions
 * ===============================================
 */
void ccsm_put_set_handle(struct ccsm_set *handle);
int ccsm_get_set_handle(char *name, struct ccsm_set **handle);
int ccsm_get_component_task_handle(struct task_struct *task_handle,
		struct ccsm_set **handle);
int ccsm_get_component_fs_handle(char *fs_id, unsigned long inode_id,
		struct ccsm_set **handle);

int ccsm_create_set(char *name, unsigned int flags, struct ccsm_set **handle);
int ccsm_destroy_set(char *name);

int ccsm_create_component_task(char *name, struct task_struct *task_handle,
		struct ccsm_set **handle);
int ccsm_create_component_fs(char *name, char *fs_id, unsigned long inode_id,
		unsigned int type, struct ccsm_set **handle);
int ccsm_destroy_component_by_name(char *name);
int ccsm_destroy_component_task(struct task_struct *handle);
int ccsm_destroy_component_fs(char *fs_id, unsigned long inode_id);

int ccsm_add_member(char *set_name, char *member_name);
int ccsm_add_member_quick(struct ccsm_set *set, struct ccsm_set *member);
int ccsm_remove_member(char *set_name, char *member_name);

int ccsm_is_member_by_name(char *set_name, char *member_name);

int ccsm_is_member_task_quick(struct ccsm_set *set, struct task_struct *task_handle);
int ccsm_is_member_task(char *set_name, struct task_struct *task_handle);
int ccsm_is_member_fs_quick(struct ccsm_set *set, char *fs_id, unsigned long inode_id);
int ccsm_is_member_fs(char *set_name, char *fs_id, unsigned long inode_id);

int ccsm_gen_component_name(char **name, unsigned int type);
int ccsm_gen_child_name(char **name, unsigned int type, struct ccsm_set *root_set);
int ccsm_gen_child_base_name(char **name, char *base_name, struct ccsm_set *root_set);

struct ccsm_set *ccsm_find_root_set(struct ccsm_set *set);


/*
 * ===============================================
 *      Component ID Inlines and Structures
 * ===============================================
 */

#if 0
struct ccsm_component_task {
	unsigned int        type;
	struct kref         kref;
	struct list_head    table_entry;
	struct ccsm_set    *set;
	struct task_struct *task;
};

struct ccsm_component_file_system {
	unsigned int        type;
	struct kref         kref;
	struct list_head    table_entry;
	struct ccsm_set    *set;
	char               *fs_id;
	unsigned long       inode_id;
};


/*
 * Note: get implicitely does kmalloc if necessary. When done with a reference
 * to a ccsm component ID structure, it needs to be explicitly freed using
 * ccsm_free_id.
 */
static inline struct ccsm_component_task *ccsm_get_id_task(struct task_struct *task)
{
	struct ccsm_component_task *ret_val;
	struct ccsm_component_task  temp_id;
	struct ccsm_set    *set;

	/* Find out if task already has an ID structure in CCSM */
	temp_id.type = CCSM_TYPE_TASK;
	temp_id.task = task;

	set = ccsm_find_set_by_id(&temp_id);
	if (!set) {
		ret_val = kmalloc(sizeof(struct ccsm_component_task), GFP_KERNEL);
		if (!ret_val) {
			return NULL;
		}

		ret_val->type = CCSM_TYPE_TASK;
		ret_val->task = task;
		ret_val->set = NULL;
		kref_init(&ret_val->kref);
		kref_get(&ret_val->kref);
//		list_add(&ccsm_temp_compid_list, &ret_val->table_entry);
	} else {
		kref_get(&set->compid->kref);
		ret_val = (struct ccsm_component_task *)set->compid;
	}
	return ret_val;
}

static inline struct ccsm_component_file_system *__ccsm_get_id_fs(char *fs_id, unsigned long inode_id, unsigned int type)
{
	struct ccsm_component_file_system *ret_val;
	struct ccsm_component_file_system  temp_id;
	struct ccsm_set  *set;

	/* Find out if fifo already has an ID structure in CCSM */
	temp_id.type     = type;
	temp_id.fs_id    = fs_id;
	temp_id.inode_id = inode_id;

	set = ccsm_find_set_by_id(&temp_id);
	if (!set) {
		ret_val = kmalloc(sizeof(struct ccsm_component_file_system), GFP_KERNEL);
		if (!ret_val) {
			return ERR_PTR(-ENOMEM);
		}

		ret_val->type     = type;
		ret_val->fs_id    = fs_id;
		ret_val->inode_id = inode_id;
		kref_init(&ret_val->kref);
		kref_get(&ret_val->kref);
//		list_add(&ccsm_temp_compid_list, &ret_val->table_entry);
	} else {
		kref_get(&set->compid->kref);
		ret_val = (struct ccsm_component_file_system *)set->compid;
	}
	return ret_val;
}

static inline struct ccsm_component_file_system *ccsm_get_id_pipe(char *fs_id, unsigned long inode_id)
{
	return __ccsm_get_id_fs(fs_id, inode_id, CCSM_TYPE_PIPE);
}

static inline struct ccsm_component_file_system *ccsm_get_id_fifo(char *fs_id, unsigned long inode_id)
{
	return __ccsm_get_id_fs(fs_id, inode_id, CCSM_TYPE_FIFO);
}

static inline struct ccsm_component_file_system *ccsm_get_id_shm(char *fs_id, unsigned long inode_id)
{
	return __ccsm_get_id_fs(fs_id, inode_id, CCSM_TYPE_SHM);
}

static inline struct ccsm_component_file_system *ccsm_get_id_socket(char *fs_id, unsigned long inode_id)
{
	return __ccsm_get_id_fs(fs_id, inode_id, CCSM_TYPE_SOCKET);
}

static inline struct ccsm_component_file_system *ccsm_get_id_file(char *fs_id, unsigned long inode_id)
{
	return __ccsm_get_id_fs(fs_id, inode_id, CCSM_TYPE_FILE);
}

static inline void __generic_compid_free(struct kref *kref)
{
	struct ccsm_component_id *ccsm_id;

	ccsm_id = container_of(kref, struct ccsm_component_id, kref);
	kfree(ccsm_id);
}

static inline int ccsm_free_id(struct ccsm_component_id *ccsm_id)
{
	int ret;

	/*
	 * Switch on the ID->type to specify freeing code if necessary.
	 */
	ret = 0;
	switch(ccsm_id->type) {
	case CCSM_TYPE_TASK:
	case CCSM_TYPE_PIPE:
	case CCSM_TYPE_FIFO:
	case CCSM_TYPE_SHM:
	case CCSM_TYPE_SOCKET:
	case CCSM_TYPE_FILE:
	case CCSM_TYPE_MUTEX:
	case CCSM_TYPE_FUTEX:
		kref_put(&ccsm_id->kref, __generic_compid_free);
		break;
	default:
		/* DSTRM_ERROR generation here, indicating an unrecognized ID
		 * type has occured */
		ret = -EINVAL;
		break;
	}

	return ret;
}
#endif

/* 
 * ===============================================
 *               Iteration Structure/Functions
 * ===============================================
 */
struct ccsm_iter {
	struct ccsm_set *set;
	struct task_group *group;
	struct list_head *set_loc;
	struct list_head *group_loc;
};

int ccsm_iter_start(char *name, struct ccsm_iter *iter);
void *ccsm_iter_next(struct ccsm_iter *iter);
void ccsm_iter_end(struct ccsm_iter *iter);
//struct ccsm_set_iter *ccsm_find_memberships(ccsm_set *set);
//struct ccsm_set *ccsm_handle_iterator_next(struct ccsm_set_iter* iter);
//void ccsm_handle_iterator_reset();
//void ccsm_handle_iterator_free();

#endif /* __KERNEL__ */

typedef struct ccsm_ioctl_create_set_s {
	char set_name[CCSM_MAX_NAME_LEN];
	unsigned int flags;
} ccsm_ioctl_create_set_t;

typedef struct ccsm_ioctl_add_member_s {
	char set_name[CCSM_MAX_NAME_LEN];
	char member_name[CCSM_MAX_NAME_LEN];
} ccsm_ioctl_add_member_t;

typedef struct ccsm_ioctl_remove_member_s {
	char set_name[CCSM_MAX_NAME_LEN];
	char member_name[CCSM_MAX_NAME_LEN];
} ccsm_ioctl_remove_member_t;

typedef struct ccsm_ioctl_destroy_set_s {
	char set_name[CCSM_MAX_NAME_LEN];
} ccsm_ioctl_destroy_set_t;

typedef struct ccsm_ioctl_create_component_self_s {
	char component_name[CCSM_MAX_NAME_LEN];
} ccsm_ioctl_create_component_self_t;

typedef struct ccsm_ioctl_create_component_pid_s {
	char component_name[CCSM_MAX_NAME_LEN];
	pid_t pid;
} ccsm_ioctl_create_component_pid_t;

typedef struct ccsm_ioctl_destroy_component_s {
	char component_name[CCSM_MAX_NAME_LEN];
	pid_t pid;
} ccsm_ioctl_destroy_component_t;

typedef union ccsm_ioctl_param_u {
	ccsm_ioctl_create_set_t			create_set;
	ccsm_ioctl_add_member_t			add_member;
	ccsm_ioctl_remove_member_t		remove_member;
	ccsm_ioctl_destroy_set_t		destroy_set;
	ccsm_ioctl_create_component_self_t	create_component_self;
	ccsm_ioctl_create_component_pid_t	create_component_pid;
	ccsm_ioctl_destroy_component_t		destroy_component;
} ccsm_ioctl_param_union;

#define CCSM_MAGIC 'c'

#define CCSM_IOCTL_CREATE_SET		_IOW(CCSM_MAGIC, 1, ccsm_ioctl_create_set_t)
#define CCSM_IOCTL_ADD_MEMBER		_IOW(CCSM_MAGIC, 2, ccsm_ioctl_add_member_t)
#define CCSM_IOCTL_REMOVE_MEMBER	_IOW(CCSM_MAGIC, 3, ccsm_ioctl_remove_member_t)
#define CCSM_IOCTL_DESTROY_SET		_IOW(CCSM_MAGIC, 4, ccsm_ioctl_destroy_set_t)
#define CCSM_IOCTL_CREATE_COMPONENT_SELF	_IOW(CCSM_MAGIC, 5, ccsm_ioctl_create_component_self_t)
#define CCSM_IOCTL_CREATE_COMPONENT_BY_PID	_IOW(CCSM_MAGIC, 6, ccsm_ioctl_create_component_pid_t)
#define CCSM_IOCTL_DESTROY_COMPONENT_BY_NAME	_IOW(CCSM_MAGIC, 7, ccsm_ioctl_destroy_component_t)
#define CCSM_IOCTL_DESTROY_COMPONENT_BY_PID	_IOW(CCSM_MAGIC, 8, ccsm_ioctl_destroy_component_t)
#endif
