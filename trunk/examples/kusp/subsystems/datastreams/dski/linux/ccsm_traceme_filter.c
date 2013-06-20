#include <asm/uaccess.h>
#include <linux/limits.h>
#include <linux/sched.h>
#include <linux/file.h>
#include <linux/fdtable.h>
#include <linux/kernel.h>
#include <linux/list.h>
#include "dski_common.h"
#include <linux/string.h>
#include <linux/ccsm.h>
#include <linux/dski.h>
#include <linux/jhash.h>
#include <linux/pid.h>
#ifdef CONFIG_DISCOVERY
#include <linux/dscvr.h>
#include <linux/dski_netdata.h>
#include <linux/mount.h>
#include <linux/dcache.h>
#include <linux/dski.h>
#endif

#define CCSM_NAME_SIZE 10


/*
 * Enum containing Labels that we make use of within the traceme Active filter.
 */
enum {
	TRACE_DO_FORK,
	TRACE_SEND_SIGNAL,
	TRACE_SHM_AT,
	TRACE_LOCK,
	TRACE_FIFO,
	TRACE_PIPE,
	TRACE_EXIT,
	TRACE_CLOSE,
	TRACE_FILE_OPEN,
	TRACE_ACCEPT,
	TRACE_LOCAL_CONNECT,
	TRACE_TCP_CONNECT,
	TRACE_CONNECT_END,
	TRACE_BIND,
	TRACE_FCNTL_DUP,
	TRACE_DUP,
	TRACE_DUPFD,
	TRACE_SYS_CALL,
	TRACE_SYS_TR_FILTER,
	TRACE_EVENT_UNMAPPED
};

/*
 * Private lists the discovery filter uses to keep track of
 * data across events
 */

/*
 * Structure that holds the events that we are going to look out for in 
 * the traceme active filter. It associates a constant label with each 
 * event that we care about.
 */
struct deid_to_ceid{
	char family_name[NAME_MAX+1];
	char event_name[NAME_MAX+1];
	unsigned int deid;
	int ceid;
	struct list_head list;
	struct list_head hash_list;
};

struct dup_lst {
	pid_t pid;
	unsigned int fd;
	struct list_head list;
};

struct inet_id_lst {
	__u16 port_num;
	struct list_head list;
};

// used for storing information about the various information with respect to each system call.
struct dski_syscall {
	unsigned long nr;
	unsigned long p1;
	unsigned long p2;
	unsigned long p3;
	unsigned long p4;
	unsigned long p5;
	unsigned long p6;
};

/****** DSCVR FILTER **********/

struct dscvr_filter_priv {
	char ccsm_set_name[NAME_MAX+1];
	struct ccsm_set *ccsm_set_handle;
	struct inet_id_lst inets;
	struct dup_lst dups;
	struct deid_to_ceid ptrs;
	pid_t traceme_pid;
};

/**
 * Some utility function are defined here .... which are used by the different actions.
 */

// Get the Exec name that the thread is executing.
int get_exec_name (struct task_struct *task, char *buffer, int len)
{
		struct vm_area_struct * vma;
		struct mm_struct * mm = get_task_mm(task);

		if (!mm) {
			printk(KERN_CRIT "Called get_exec_name on task with bad mm_struct\n");
			return -EINVAL;
		}
		down_read(&mm->mmap_sem);

		vma = mm->mmap;
		while (vma) {
			if ((vma->vm_flags & VM_EXECUTABLE) && vma->vm_file)
				break;
			vma = vma->vm_next;
		}

		if (vma) {
			strncpy(buffer, d_path(&vma->vm_file->f_path, buffer, len), len);
		}

		up_read(&mm->mmap_sem);
		mmput(mm);

		return 0;
}

// used for emitting file descriptor table information used in postprocessing.
void emit_file_table_events(int pid)
{
		int open_file_count, i, size;
		struct fdtable *child_fdt;
		struct file **child_fds;
		struct task_struct *task;
		open_close_info_t f_info;

		rcu_read_lock();
		task = get_pid_task(pid, PIDTYPE_PID);
		rcu_read_unlock();
		spin_lock(&(task->files->file_lock));
		child_fdt = files_fdtable(task->files);
		child_fds = child_fdt->fd;
		size = child_fdt->max_fds;	

		/* Count up the open files */
		for (i = size/(8*sizeof(long)); i > 0; ) {
			if (child_fdt->open_fds->fds_bits[--i])
				break;
		}
		open_file_count = (i+1) * 8 * sizeof(long);

		for (i = open_file_count; i != 0; i--) {
			struct file *f = *child_fds++;
			if (f) {
				f_info = get_dscvr_open_close_info(f, open_file_count - i);
				DSTRM_EVENT_DATA(ROOT_THREAD, INHERIT_FD, task->pid, sizeof(f_info), &f_info, "get_open_close_info");
			}
		}
		spin_unlock(&(task->files->file_lock));
#ifdef BALA_NOT_USED
#endif
}

/**
 * Generic Function that is going to generate names and add components to the CCSM
 * set that we care about in the tracme filter.
 */
int add_component_to_traceme_set(struct dscvr_filter_priv *priv, void *id, unsigned int type){
	char *temp_component_name;
	struct ccsm_set *comp_set;
	int ret;
	
	ret = ccsm_gen_component_name(&temp_component_name, type);
	if (ret) {
		printk("Generating Component Name is not done correctly...\n");
		return 1;
	}	

	comp_set = ccsm_create_component(temp_component_name, id);
	if (IS_ERR(comp_set)) {
		printk("Creating Component is not done correctly....\n");
		return 1;
	}
	
	ret = ccsm_add_member_quick(priv->ccsm_set_handle, comp_set);
	if (ret) {
		printk("Not able to add the identified member to the traceme set ....\n");
		return 1;
	}
#ifdef BALA_NOT_USED
#endif
	return 0;
}

/**
 * All the actions for the different instrumentation points are written below.
 */

/*
 *Action Handler for Fork Instrumentation point. 
 */
int forkAction(struct dscvr_filter_priv *priv, unsigned int tag){

	/*
	 * Some process in the kernel has logged a fork event
	 */
	pid_t child_pid;
	struct task_struct *ts;
	struct ccsm_component_task *task_id;
	struct ccsm_component_task *child_task_id;
	int ret;

	/*
	 * Test whether the current thread is part of the ccsm traceme set 
	 */
	task_id = ccsm_get_id_task(current);
	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)==0) {
		/*
		 * Since the current process is a member of the CCSM set then the child should be 
		 * added to the set. The child pid is the tag value of the event.
		 */
		child_pid = (pid_t) tag;
		
		/*
		 * We need to create a component set to represent the child thread and add it 
		 * to the traceme set that represents the computation. First we create a name
		 * for the component set. The child thread's task structure pointer is used as 
		 * the CCSM unique identifier of the component set. The component set is then 
		 * added as a member of the traceme ccsm set by name.
		 */
		ts = get_pid_task(&child_pid, PIDTYPE_PID);
		child_task_id = ccsm_get_id_task(ts);
		if(!child_task_id){
			printk("Task_ID returned by ccsm for the child thread is NULL %d \n",ts->pid);
		} else {
			ret = add_component_to_traceme_set(priv,child_task_id,CCSM_TYPE_TASK);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered task to the CCSM Set \n");
				return FLTR_PASS;
			}
		}

		/*
		 * If the current process is the traceme thread, then we inject 
		 * its file table contents into the datastream, so that we 
		 * are able to identify any file reads or writes happening to
		 * any of the tracing framework related files. In postprocessing 
		 * we can distinguish framework related operations from the real 
		 * computation operations.
		 */
/*		if (current->pid == priv->traceme_pid) {
			emit_file_table_events(child_pid);
		}*/
		return FLTR_ACCEPT;
	}
	return FLTR_PASS;
}

/*
 *This is action handler for the send signal instrumentation point. 
 */
int sendSignalAction(struct dscvr_filter_priv *priv, unsigned int tag){
	struct task_struct *ts;
	char exec_name[DSCVR_PATHNAME_LEN];
	struct ccsm_component_task *task_id;
	int ret;

	task_id = ccsm_get_id_task(current);
	if(ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)){

		/*
		 * If a task alias does not exist to the task represented by the pid of the
		 * process we are sending the signal to
		 */

		ts = get_pid_task(tag, PIDTYPE_PID);
		task_id = ccsm_get_id_task(ts);
		if(!(ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id))) {

			if (get_exec_name(current, exec_name, DSCVR_PATHNAME_LEN)) {
				printk(KERN_CRIT "Failed getting a discovered tasks \
						exec_name. PID: %d\tGroup%s\n", \
						current->pid, priv->ccsm_set_name);
				return FLTR_PASS;
			}

			ret = add_component_to_traceme_set(priv,task_id,CCSM_TYPE_TASK);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered Signal task to the CCSM Set \n");
				return FLTR_PASS;
			}

			DSTRM_EVENT_DATA(SIGNAL, SIGSEND_ADD, 0, \
					strnlen(exec_name, DSCVR_PATHNAME_LEN), \
					exec_name, "print_string");
		}
		return FLTR_ACCEPT;
	}
	return FLTR_REJECT;
}

/*
 * In regular dup, we do not have access to the old and new
 * fd in the same spot in the kernel. Here we record the old
 * fd, and when we have access to the new fd, we emit a DUP_X
 * event in the next block of code
 */
int duplicateFDAction(struct dscvr_filter_priv *priv, unsigned int tag){

	struct dup_lst *tmpdup;
	struct ccsm_component_task *task_id;

	task_id = ccsm_get_id_task(current);
	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {

		list_for_each_entry(tmpdup, &(priv->dups.list), list) {
			if (tmpdup->pid == current->pid)
				printk(KERN_CRIT "ERROR: Got dup evt before \
						seeing dupfd on (pid, fd): \
						(%u, %d)\n", current->pid, tag);
			return FLTR_PASS;
		}

		tmpdup = kmalloc(sizeof(struct dup_lst), GFP_KERNEL);
		tmpdup->pid = (pid_t)current->pid;
		tmpdup->fd = tag;
		list_add(&(tmpdup->list), &(priv->dups.list));
		return FLTR_REJECT;
	}
	return FLTR_PASS;
}

/*
 * This is called when we encounter the second type of dup system call. which has both the old fd and
 * the new fd it wants as parameters.
 */
int duplicateFDSecondTypeAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){

	struct dup_lst *tmpdup;
	dup_info_t *dup_data;
	open_close_info_t *info;
	struct ccsm_component_task *task_id;

	task_id = ccsm_get_id_task(current);
	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {

		list_for_each_entry(tmpdup, &(priv->dups.list), list) {
			if (tmpdup->pid == current->pid) {
				info = (open_close_info_t *) extra_data;
				dup_data = kmalloc(sizeof(dup_info_t), GFP_KERNEL);
				if(!dup_data)
					return FLTR_PASS;

				dup_data->inode_id = info->inode_id;
				strncpy(dup_data->sys_id, info->sys_id, DSCVR_SYSID_LEN);
				strncpy(dup_data->pathname, info->pathname, DSCVR_PATHNAME_LEN);
				dup_data->mode = info->mode;
				dup_data->old_fd = tmpdup->fd;
				dup_data->new_fd = info->fd;

				DSTRM_EVENT_DATA(FILE, DUP_X, 0, sizeof(dup_info_t), dup_data, "get_dup_info");
				kfree(dup_data);
				list_del(&(tmpdup->list));
				return FLTR_REJECT;
			}
		}

		printk(KERN_CRIT "ERROR: Got a dupfd event without seeing corresponding dup event.\n");
		return FLTR_PASS;
	}
	return FLTR_PASS;
}

/*
 * If this is not a member of the group, look at the list of port numbers
 * threads in our group have called connect on. If the destination port is 
 * in that list, add this thread to the group
 */
int socketAcceptAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){
	struct ccsm_component_task *task_id;
	struct ccsm_component_file_system *serverCon;
	char exec_name[DSCVR_PATHNAME_LEN];
	socket_info_t *sk_info;
	int ret;
	
	sk_info = (socket_info_t *) extra_data;
	task_id = ccsm_get_id_task(current);
	serverCon = ccsm_get_id_socket(sk_info->known_sys_id, sk_info->known_inode);

	if (!ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {		
		int new_conn = 0;
		if (sk_info->family == AF_UNIX) {
			if(ccsm_is_member_by_id_quick(priv->ccsm_set_handle,serverCon)){
				new_conn = 1;
			}
		} else if (sk_info->family == AF_INET) {
			struct inet_id_lst *tmpinet;
			list_for_each_entry(tmpinet, &(priv->inets.list), list){
				if(tmpinet->port_num == sk_info->sport) {
					new_conn = 1;
					break;
				}
			}
		}

		if (new_conn) {

			if (get_exec_name(current, exec_name, DSCVR_PATHNAME_LEN)) {
				printk(KERN_CRIT "Failed getting a discovered tasks \
						exec_name. PID: %d\tGroup%s\n", current->pid, \
						priv->ccsm_set_name);
				return FLTR_PASS;
			}
			
			ret = add_component_to_traceme_set(priv,task_id,CCSM_TYPE_TASK);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered Socket Accept task (Server) to the CCSM Set \n");
				return FLTR_PASS;
			}
			
			DSTRM_EVENT_DATA(SOCKET, SERVER_ADD, 0, \
					strnlen(exec_name, DSCVR_PATHNAME_LEN), exec_name, "print_string");
		}
	}
	return FLTR_PASS;
}

/*
 * For threads we are tracking, add the socket path name to a list
 * of path names we are tracking
 */
int localConnectAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){
	struct ccsm_component_task *task_id;
	struct ccsm_component_file_system *localCon;
	socket_info_t *sk_info;
	int ret;
	
	sk_info = (socket_info_t *) extra_data;
	task_id = ccsm_get_id_task(current);
	localCon = ccsm_get_id_socket(sk_info->known_sys_id,sk_info->known_inode);

	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {
		if(!ccsm_is_member_by_id_quick(priv->ccsm_set_handle,localCon)){
			ret = add_component_to_traceme_set(priv,localCon,CCSM_TYPE_SOCKET);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered Local Connect Socket to the CCSM Set \n");
				return FLTR_PASS;
			}
		}
		return FLTR_PASS;
	} else {
		/*
		 * Discovery needs to know the listening inode of sockets we are
		 * discovering in order to correctly pair socket connections in
		 * postprocessing
		 */
		if(ccsm_is_member_by_id_quick(priv->ccsm_set_handle,localCon)){
			return FLTR_ACCEPT;	
		}
	}
	return FLTR_PASS;
}

/*
 * For threads we are tracking, add this port number to a list of
 * known port numbers
 */
int tcpConnectAction(struct dscvr_filter_priv *priv, unsigned int tag,const void *extra_data){
	struct ccsm_component_task *task_id;

	task_id = ccsm_get_id_task(current);
	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {
		socket_info_t *sk_info = (socket_info_t *) extra_data;
		struct inet_id_lst *tmpinet; 
		tmpinet = kmalloc(sizeof(struct inet_id_lst), GFP_KERNEL);
		tmpinet->port_num = sk_info->dport;
		list_add(&(tmpinet->list), &(priv->inets.list));
	}
	return FLTR_PASS;
}

/*
 * If the task is not a member of the group, check to see if a 
 * member of the group has called bind on this port number. If so,
 * add this task to our group
 */
int connectEndAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){
	struct ccsm_component_task *task_id;
	socket_info_t *sk_info;
	struct ccsm_component_file_system *clientCon;
	char exec_name[DSCVR_PATHNAME_LEN];
	int ret;

	sk_info = (socket_info_t *) extra_data;
	task_id = ccsm_get_id_task(current);
	clientCon = ccsm_get_id_socket(sk_info->known_sys_id,sk_info->known_inode);

	if (!ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {		
		int new_conn = 0;
		if (sk_info->family == AF_UNIX) {
			if(ccsm_is_member_by_id_quick(priv->ccsm_set_handle,clientCon)){
				new_conn = 1;
			}
		} else if (sk_info->family == AF_INET) {
			struct inet_id_lst *tmpinet;
			list_for_each_entry(tmpinet, &(priv->inets.list), list){
				/*
				 * This does not work when the sockets are on the
				 * same computer. Maybe should retest this
				 */
				//if(tmpinet->port_num == sk_info->dport) {
				if(tmpinet->port_num == sk_info->sport) {
					new_conn = 1;
					break;
				}
			}
		}

		if (new_conn) {

			if (get_exec_name(current, exec_name, DSCVR_PATHNAME_LEN)) {
				printk(KERN_CRIT "Failed getting a discovered tasks \
						exec_name. PID: %d\tGroup%s\n", current->pid, \
						priv->ccsm_set_name);
				return FLTR_PASS;
			}

			ret = add_component_to_traceme_set(priv,task_id,CCSM_TYPE_TASK);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered Connect End Socket task to the CCSM Set \n");
				return FLTR_PASS;
			}
			
			DSTRM_EVENT_DATA(SOCKET, CLIENT_ADD, 0, strnlen(exec_name, DSCVR_PATHNAME_LEN), exec_name, "print_string");
		}
	}	
	return FLTR_PASS;
}


/*
 * For threads we are tracking, add a unique identifier for the socket
 * to a list we keep track of
 */
int bindAction(struct dscvr_filter_priv *priv , unsigned int tag, const void *extra_data){
	struct ccsm_component_task *task_id;
	struct ccsm_component_file_system *bindCon;
	socket_info_t *sk_info;
	int ret;

	sk_info = (socket_info_t *) extra_data;
	task_id = ccsm_get_id_task(current);
	bindCon = ccsm_get_id_socket(sk_info->known_sys_id,sk_info->known_inode);

	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {
		/*
		 * Add to list of sockets we are tracking
		 * XXX: Not sure how to handle known_inodes == 0
		 */
		if (sk_info->family == AF_UNIX && sk_info->known_inode != 0) {
			ret = add_component_to_traceme_set(priv,bindCon,CCSM_TYPE_SOCKET);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered Bind Socket to the CCSM Set \n");
				return FLTR_PASS;
			}
		} else if (sk_info->family == AF_INET) {
			struct inet_id_lst *tmpinet; 
			tmpinet = kmalloc(sizeof(struct inet_id_lst), GFP_KERNEL);
			tmpinet->port_num = sk_info->sport;
			list_add(&(tmpinet->list), &(priv->inets.list));
		}
	}
	return FLTR_PASS;
}

/*
 * Shared memory Action, whenever a thread tries to attach to a shared memory segment that we care
 * about or a known thread tries to attach to an external shared memory segment we make note of that.
 */
int sharedMemoryAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){
	struct task_struct *ts;
	struct shmat_dski_info shm_info;
	struct ccsm_component_task *task_id;
	struct ccsm_component_file_system *shared_id;
	char exec_name[DSCVR_PATHNAME_LEN];
	int ret;

	shm_info = *(struct shmat_dski_info *)extra_data;
	task_id = ccsm_get_id_task(current);
	shared_id = ccsm_get_id_shm(shm_info.sys_id,shm_info.inode_id);

	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {
		/*
		 * If the shmid represented by the tagged data is already
		 * in the list of shmids we are tracking, we don't need
		 * to do anything so jump out of here
		 */
		
		/* 
		 * A process in the group we are tracking attached
		 * to a shared memory segment that is not on the list
		 * of segments we are currently tracking
		 */
		if(!ccsm_is_member_by_id_quick(priv->ccsm_set_handle,shared_id)){
			ret = add_component_to_traceme_set(priv,shared_id,CCSM_TYPE_SHM);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered Shared memory to the CCSM Set \n");
				return FLTR_PASS;
			}
		}

	} else {
		/*
		 * The process is not in the group we are tracking
		 */
		if(ccsm_is_member_by_id_quick(priv->ccsm_set_handle,shared_id)){
			if (get_exec_name(current, exec_name, DSCVR_PATHNAME_LEN)) {
				printk(KERN_CRIT "Failed getting a discovered tasks \
						exec_name. PID: %d\tGroup%s\n", current->pid, \
						priv->ccsm_set_name);
				return FLTR_PASS;
			}

			/*
			 * A process not yet in the group is attaching to a shared
			 * memory segment that a process in our group has attached to
			 */

			ts = get_pid_task(tag, PIDTYPE_PID);
			task_id = ccsm_get_id_task(ts);
			ret = add_component_to_traceme_set(priv,task_id,CCSM_TYPE_TASK);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered shared memory task to the CCSM Set \n");
				return FLTR_PASS;
			}
			DSTRM_EVENT_DATA(SHMEM, SHMAT_ADD, 0, strnlen(exec_name, DSCVR_PATHNAME_LEN), exec_name, "print_string");
			return FLTR_PASS;
		}
	}
		
	return FLTR_PASS;
}

/*
 * Syscall Action. whenever the Syscall instrumentation point is crossed
 * we create a new datastream instrumentation point that has the system call
 * number.
 */
int syscallAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){
	struct dski_syscall *syscallInfo;
	int sysNum = 0;
	struct ccsm_component_task *task_id;

	syscallInfo = (struct dski_syscall *)extra_data;
	sysNum = syscallInfo->nr;

	task_id = ccsm_get_id_task(current);
	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {
		DSTRM_EVENT_DATA(SYSCALL, SYS_TR_FILTER, current->pid,sizeof(sysNum),&sysNum,"print_int");
	}
	return FLTR_PASS;
}

/**
 * This function takes care of adding an unnamed pipe component 
 * to the traceme CCSM set. Unnamed pipes exist within computation
 * boundaries.
 */
int unnamedPipeAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){
	struct ccsm_component_task *task_id;
	struct ccsm_component_file_system *pipe_id;
	pipe_info_t *pipe_info;
	int ret;

	pipe_info = (pipe_info_t *) extra_data;
	task_id = ccsm_get_id_task(current);
	pipe_id = ccsm_get_id_pipe(pipe_info->sys_id, pipe_info->inode_id);

	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {
		ret = add_component_to_traceme_set(priv,pipe_id,CCSM_TYPE_PIPE);
		if(ret){
			printk(KERN_CRIT "Cannot add Discovered UnNamed pipe to the CCSM Set \n");
			return FLTR_PASS;
		}
	}
	return FLTR_ACCEPT;
}

/**
 * This function takes care of adding Files being read or written to, by the computation
 * under the scanner to the traceme CCSM set.
 */
int fileOpenAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){
	struct ccsm_component_task *task_id;
	struct ccsm_component_file_system *file_id;
	open_close_info_t *fileOpen;
	int ret;

	fileOpen = (open_close_info_t *)extra_data;
	task_id = ccsm_get_id_task(current);
	file_id = ccsm_get_id_file(fileOpen->sys_id, fileOpen->inode_id);

	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {
		if (!ccsm_is_member_by_id_quick(priv->ccsm_set_handle,file_id)) {
			ret = add_component_to_traceme_set(priv,file_id,CCSM_TYPE_FILE);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered file to the CCSM Set \n");
				return FLTR_PASS;
			}
		}
		return FLTR_PASS;
	}
	return FLTR_REJECT;
}

/*
 * This instrumentation point is used for attaching threads to a taskalias group
 * Here we try to add threads that we care about if it is using the same named pipe 
 * that one of our threads created or if it trying to use a named pipe already in the
 * system. we add the new named pipe inode id,to our linked list as well. so whenever
 * a thread that we care about tries to do a open system call on our named pipe we try
 * to add them to our group
 */ 
int namedPipeAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){
	fifo_info_t fifo_info;
	struct task_struct *ts;
	struct ccsm_component_file_system *fif;
	struct ccsm_component_task *task_id;
	int ret;

	fifo_info = *(fifo_info_t *)extra_data;
	fif = ccsm_get_id_fifo(fifo_info.sys_id,fifo_info.inode_id);

	// we check if the thread is already present in the group, if it is not then we try to
	// check whether it is using a named pipe that we care about, if so add the thread to our 
	// task alias group 

	task_id = ccsm_get_id_task(current);
	if (!(ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id))) {
		if(ccsm_is_member_by_id_quick(priv->ccsm_set_handle,fif)){
			ts = get_pid_task(tag, PIDTYPE_PID);
			task_id = ccsm_get_id_task(ts);
			ret = add_component_to_traceme_set(priv,task_id,CCSM_TYPE_TASK);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered named pipe task to the CCSM Set \n");
				return FLTR_PASS;
			}
		}
		return FLTR_ACCEPT;

	// if the thread already exist in our task alias group then we check whether it is using the same named pipe,
	// if not then we try to add the inode id to our list, because the named pipe is accessed by one of the thread 
	// already registered with the task alias group
	} else {
		if(!ccsm_is_member_by_id_quick(priv->ccsm_set_handle,fif)){
			ret = add_component_to_traceme_set(priv,fif,CCSM_TYPE_FIFO);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered named pipe to the CCSM Set \n");
				return FLTR_PASS;
			}
		}
	}
	return FLTR_PASS;
}

/*
 * This instrumentation is used for attaching threads that use file locking methods 
 * to the task alias group, we check whether the threads that we care about uses the
 * same file or a different file for usage, if it uses a different file we add the 
 * inode id of the file to our list 
*/ 
int fileLockingAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){
	flock_info_t file_info;
	struct task_struct *ts;
	struct ccsm_component_file_system *fileLoc;
	struct ccsm_component_task *task_id;
	int ret;
		
	file_info = *(flock_info_t *)extra_data;
	fileLoc = ccsm_get_id_file(file_info.sys_id,file_info.inode_id);

	// if the thread is not already present in the group , we check whether it access any of the file inode id's
	// to be locked if so then we add that thread to the task alias group

	task_id = ccsm_get_id_task(current);
	if (!(ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id))) {
		if(ccsm_is_member_by_id_quick(priv->ccsm_set_handle,fileLoc)){
			ts = get_pid_task(tag, PIDTYPE_PID);
			task_id = ccsm_get_id_task(ts);
			ret = add_component_to_traceme_set(priv,task_id,CCSM_TYPE_TASK);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered File Locking thread to the CCSM Set \n");
				return FLTR_PASS;
			}
		}
		return FLTR_ACCEPT;

		// if the thread already exist in our group then we try to check whether it uses the same file to be locked,
		// if not then we try to add the new inode id of the file that a thread that we care about accesses to our list
	} else {
		if(!ccsm_is_member_by_id_quick(priv->ccsm_set_handle,fileLoc)){
			ret = add_component_to_traceme_set(priv,fileLoc,CCSM_TYPE_FILE);
			if(ret){
				printk(KERN_CRIT "Cannot add Discovered File Locking File to the CCSM Set \n");
				return FLTR_PASS;
			}
		}
	}
	return FLTR_PASS;
}

/**
 * Whenever we are going to encounter a thread exit event from a thread part of the
 * traceme CCSM set we remove or destroy the set representing the thread from the 
 * traceme CCSM set.
 */
int threadExitAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){
	struct ccsm_component_task *task_id;
	
	task_id = ccsm_get_id_task(current);
	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {
	
		return FLTR_ACCEPT;
	}
	return FLTR_REJECT;
}

/**
 * Whenever we encounter a close on a file descriptor representing the passive components
 * pipes/named pipes/file/socket we remove the corresponding ccsm set from the traceme ccsm set.
 */
int closeAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data){
	struct ccsm_component_task *task_id;
	struct ccsm_component_file_system *close_id;
	open_close_info_t *close_info;

	close_info = (open_close_info_t *)extra_data;
	task_id = ccsm_get_id_task(current);
	close_id = ccsm_get_id_file(close_info->sys_id, close_info->inode_id);

	if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,task_id)) {
		if (ccsm_is_member_by_id_quick(priv->ccsm_set_handle,close_id)) {
			return FLTR_ACCEPT;
		}
	}
	return FLTR_REJECT;
}

/**
 * HashTable that is going to be used within the traceme active filter.
 */
#define TRACEME_CCSM_HASH_TABLE_SIZE 14
struct list_head tracemeCCSMDeidHashTable[TRACEME_CCSM_HASH_TABLE_SIZE];

/*
 * Create an entry into the list of known events that we care about in this filter.
 * and also add it to the hash table.
 */
int insertEventWeCare(int ceid,char *family_name,char *event_name, unsigned int deid, struct dscvr_filter_priv *priv){
	struct deid_to_ceid *tmpdmp;
	struct list_head *bucket;
	u32 hash;
	unsigned int pointer_to_deid = 0;
	int arrayIndex = 0;

	tmpdmp = kmalloc(sizeof(struct deid_to_ceid), GFP_KERNEL);
	tmpdmp->ceid = ceid;
	tmpdmp->deid = deid;
	strncpy(tmpdmp->family_name,family_name,NAME_MAX+1);
	strncpy(tmpdmp->event_name,event_name,NAME_MAX+1);
	list_add(&(tmpdmp->list), &(priv->ptrs.list));
#ifdef CONFIG_DSKI_HASH_TABLE	
	pointer_to_deid = (unsigned int) &deid;
	hash = jhash((u32*)pointer_to_deid, (u32)sizeof(pointer_to_deid), 0);
	arrayIndex = hash & (TRACEME_CCSM_HASH_TABLE_SIZE-1);
	bucket = &(tracemeCCSMDeidHashTable[arrayIndex]);
	// FIXME.b:
	// search for duplicates bedore inserting......
	// add a DSKI_INTERNAL_ERROR............
	list_add(&tmpdmp->hash_list, bucket);
#endif

	return 0;
}

/**
 * Initializes the Hash Table that is going to be used as part of the Hash Table.
 */
int initializeHashMap(){
	struct list_head *cur;
	int i = 0;

	for (i = 0; i < TRACEME_CCSM_HASH_TABLE_SIZE; i++) {
		cur = &(tracemeCCSMDeidHashTable[i]);
		INIT_LIST_HEAD(cur);
	}
	return 0;
}

/*
 * Preloading the set of events that we are going to look out for in
 * this filter.
 */
void insertingEvents(struct dscvr_filter_priv *priv){
#ifdef CONFIG_DSKI_HASH_TABLE
	initializeHashMap();
#endif
	insertEventWeCare(TRACE_DO_FORK,"FORK","DO_FORK",get_deid_by_name("FORK","DO_FORK"),priv);
	insertEventWeCare(TRACE_SEND_SIGNAL,"SIGNAL","SEND_SIGNAL",get_deid_by_name("SIGNAL","SEND_SIGNAL"),priv);
	insertEventWeCare(TRACE_SHM_AT,"SHMEM","SHMAT",get_deid_by_name("SHMEM","SHMAT"),priv);
	insertEventWeCare(TRACE_FIFO,"FIFO","FIFO_OPEN",get_deid_by_name("FIFO","FIFO_OPEN"),priv);
	insertEventWeCare(TRACE_PIPE,"PIPE","DO_PIPE",get_deid_by_name("PIPE","DO_PIPE"),priv);
	insertEventWeCare(TRACE_FILE_OPEN,"FILE","OPEN",get_deid_by_name("FILE","OPEN"),priv);
	insertEventWeCare(TRACE_CLOSE,"FILE","CLOSE",get_deid_by_name("FILE","CLOSE"),priv);
	insertEventWeCare(TRACE_EXIT,"EXIT","DO_EXIT",get_deid_by_name("EXIT","DO_EXIT"),priv);
	insertEventWeCare(TRACE_ACCEPT,"SOCKET","ACCEPT",get_deid_by_name("SOCKET","ACCEPT"),priv);
	insertEventWeCare(TRACE_LOCAL_CONNECT,"SOCKET","LOCAL_CONNECT",get_deid_by_name("SOCKET","LOCAL_CONNECT"),priv);
	insertEventWeCare(TRACE_TCP_CONNECT,"SOCKET","TCP_CONNECT",get_deid_by_name("SOCKET","TCP_CONNECT"),priv);
	insertEventWeCare(TRACE_CONNECT_END,"SOCKET","CONNECT_END",get_deid_by_name("SOCKET","CONNECT_END"),priv);
	insertEventWeCare(TRACE_BIND,"SOCKET","BIND",get_deid_by_name("SOCKET","BIND"),priv);
	insertEventWeCare(TRACE_FCNTL_DUP,"FLOCK","DUP",get_deid_by_name("FLOCK","DUP"),priv);
	insertEventWeCare(TRACE_DUP,"FILE","DUP",get_deid_by_name("FILE","DUP"),priv);
	insertEventWeCare(TRACE_DUPFD,"FILE","DUPFD",get_deid_by_name("FILE","DUPFD"),priv);
	insertEventWeCare(TRACE_SYS_CALL,"SYSCALL","SYSTEM_CALL",get_deid_by_name("SYSCALL","SYSTEM_CALL"),priv);
	insertEventWeCare(TRACE_SYS_TR_FILTER,"SYSCALL","SYS_TR_FILTER",get_deid_by_name("SYSCALL","SYS_TR_FILTER"),priv);
}

/*
 * Get the constant eid value for the corresponding dynamic eid value.
 */
int getCeid(unsigned int deid, struct dscvr_filter_priv *priv){
	struct deid_to_ceid *tmpdmp;
	struct list_head *bucket;
	u32 hash;

#ifdef CONFIG_DSKI_HASH_TABLE
	// hash table search
	hash = jhash((u32*)&deid, (u32)sizeof(unsigned int), 0);
	bucket = &(tracemeCCSMDeidHashTable[hash & (TRACEME_CCSM_HASH_TABLE_SIZE - 1)]);
	list_for_each_entry(tmpdmp, bucket, hash_list) {
		if (tmpdmp->deid == deid)
			return tmpdmp->ceid;
	}
#endif
	// list based search... reach here only if you don't find it as part
	// of the hash based search. which is bad..
	list_for_each_entry(tmpdmp, &(priv->ptrs.list), list) {
		if (tmpdmp->deid == deid)
			// FIXME.b:
			// create a DSKI_INTERNAL_ERROR if you find it as part of the list
			// and not as part of the hash table.
			return tmpdmp->ceid;
	}
	return TRACE_EVENT_UNMAPPED;
}

int traceme_c_func(struct datastream *d, void **data, union dski_ioc_filter_ctrl_params *params){

	struct dscvr_filter_priv *priv;
	struct ccsm_set *set;

	/* allocating filter's private data which is used to 
	 * maintain the filter state to track Information required 
	 * to deduce computation structure from a series of events */
	priv = kmalloc(sizeof(struct dscvr_filter_priv), GFP_KERNEL);
	if (!priv) {
		return -ENOMEM;
	}

	/* Get the user-space name ptr and then copy the ccsm set name
	 * from user space into the filter's private data structure.*/
	if (copy_from_user(priv->ccsm_set_name, params->dscvr_filter.name, NAME_MAX+1)) {
		kfree(priv);
		return -EFAULT;
	}
	
	/* 
	 * Attempt to get a 'handle' to the named set and store in our private
	 * data structure.If the set is not alive, then the find set returns the
	 * handle to the created one.
	 */
	set = ccsm_find_set_by_name(priv->ccsm_set_name);
	if (IS_ERR(set)) {
		printk(KERN_CRIT "CCSM is not able to find the set by name .....%s\n",priv->ccsm_set_name);
		kfree(priv);
		return PTR_ERR(set);
	}
	priv->ccsm_set_handle = set;


	/* Initialize the list that holds the mapping of dynamic event ids 
	 * to constant event ids
	 * FIXME.b: 
	 * This list is slated to go away in the future version. In the future there is going
	 * to be mappings based only on the hash table.*/
	INIT_LIST_HEAD(&(priv->ptrs.list));

	/* Creating the Mapping of dynamic event ids to constant event ids 
	 * that this filter cares about.
	 * FIXME.b:
	 * note that this routine both the hashtable and the linked list mapping
	 * and the linked list mapping should go away soon.
	 */
	insertingEvents(priv);
	
	/* link up rest of private data that supports the tracking of passive
	 * components that are being used by the computation.
	 * FIXME.b:
	 * These Lists are going to go away once we have the capability of 
	 * having a passive component as a component set. 
	 */
	priv->traceme_pid = current->pid;
	INIT_LIST_HEAD(&(priv->inets.list));
	INIT_LIST_HEAD(&(priv->dups.list));

	printk("Traceme pid = %d\n",priv->traceme_pid);

	/* Setting the pointer to the active filter private data in the calling context, 
	 * a pointer to which was passed in as the data parameter. The calling context 
	 * will supply this as an argument when the traceme_f_func and the traceme_d_func
	 * are called .*/
	*data = priv;

	return 0;
}

int traceme_f_func(struct datastream *d, struct ds_event_record *evt, void *data, int data_len, const void *extra_data){

	struct dscvr_filter_priv *priv = data;
	unsigned int eid = evt->id;
	unsigned int tag = evt->event_tag;
	int retval = FLTR_PASS;
 	
	/*
	 * Every event is labeled with its dynamic Id. Unfortunately, the dynamic id can change 
	 * whenever the kernel is compiled or a module is loaded. Therefore we use the getCeid to 
	 * map the dynamic id to the constant event id which can be used in the switch statement 
	 * defined below. This makes the filter code much easier to understand but requires the 
	 * traceme_c_func routine to build the hash table with the dynamic to constant event id 
	 * mapping using insertEvents().
	 */
	int ceid = getCeid(eid,priv);
	switch(ceid){
		case TRACE_DO_FORK:
		 	retval = forkAction(priv, tag);
		break;
#ifdef BALA_NOT_USED
		case TRACE_SEND_SIGNAL:	
	         	retval = sendSignalAction(priv, tag);	
		break;
		case TRACE_DUP:
		case TRACE_FCNTL_DUP:
			 retval = duplicateFDAction(priv,tag);
		break;
		case TRACE_DUPFD:
		 	retval = duplicateFDSecondTypeAction(priv,tag,extra_data);
		break;
		case TRACE_ACCEPT:
		 	retval = socketAcceptAction(priv,tag, extra_data);
		break;
		case TRACE_LOCAL_CONNECT:
		 	retval = localConnectAction(priv,tag,extra_data);
		break;
		case TRACE_TCP_CONNECT:
		 	retval = tcpConnectAction(priv,tag,extra_data);
		break;
		case TRACE_CONNECT_END:
		 	retval = connectEndAction(priv,tag,extra_data);
		break;
		case TRACE_BIND:
			retval = bindAction(priv,tag,extra_data);
		break;
		case TRACE_SHM_AT:
		 	retval = sharedMemoryAction(priv,tag,extra_data);
		break;
		case TRACE_SYS_CALL:
			retval = syscallAction(priv,tag,extra_data);
		break;
		case TRACE_SYS_TR_FILTER:
			retval = FLTR_ACCEPT;
		break;
		case TRACE_FIFO:
			retval = namedPipeAction(priv,tag,extra_data);
		break;
		case TRACE_PIPE:
			retval = unnamedPipeAction(priv,tag,extra_data);
		break;
		case TRACE_LOCK:
			retval = fileLockingAction(priv,tag,extra_data);
		break;
		case TRACE_FILE_OPEN:
			retval = fileOpenAction(priv, tag,extra_data);
		break;
		case TRACE_EXIT:
			retval = threadExitAction(priv,tag,extra_data);
		break;
		case TRACE_CLOSE:
			retval = closeAction(priv,tag,extra_data);
		break;
#endif
		case TRACE_EVENT_UNMAPPED:
			retval = FLTR_PASS;
		break;
		default:
			/*FIXME.b 
			 * Send an internal event that tells us that get_ceid 
			 * returned an unknown and impossible value
			 */
			retval = FLTR_PASS;
		break;
	}
	
	return retval;
}

void traceme_d_func(struct datastream *d, void *data){

	struct dscvr_filter_priv *priv = data;
	struct dup_lst *duptmp;
	struct list_head *pos, *t;
	struct inet_id_lst *tmpinet;
	struct deid_to_ceid *tmpdeid_to_ceid;

	/**
	 * We are in the destroy area and we try to free up all the different state
	 * lists that we have accumulated for our analysis in this filter.
	 * FIXME.b:
	 * Most or all of these private data lists will be gone when the passive components
	 * are fully in CCSM.
	 */

	/* And the sockets lists */
	list_for_each_safe(pos, t,&(priv->inets.list)){
		tmpinet = list_entry(pos, struct inet_id_lst, list);
		list_del(pos);
		kfree(tmpinet);
	}
	
	/* And the dups list */
	list_for_each_safe(pos, t ,&(priv->dups.list)){
		duptmp = list_entry(pos, struct dup_lst, list);
		list_del(pos);
		kfree(duptmp);
	}


	/* Free the Deid_to_ceid Structure which mapped the dynamic to 
	 * constant event id. Note we free the list version of the mapping 
	 * and the hashtable version of the mapping.
	 * FIXME.b:
	 * Obviously we do need the list version when the list goes away.
	 * hashtable will still be freed.
	 */
	list_for_each_safe(pos, t , &(priv->ptrs.list)) {
		tmpdeid_to_ceid = list_entry(pos, struct deid_to_ceid, list);
		list_del(pos);
		kfree(tmpdeid_to_ceid);
	}
	

	/*
	 * Destroy the CCSM set that represents the computation, because we 
	 * no longer are using it.
	 * FIXME.b:
	 * This is completely appropriate when the set has been used by traceme 
	 * during the lifetime of the computation being traced and the filter is
	 * destroyed is only after the computation is completed. Therefore destroying
	 * the set is fine. If the set has also been used for group scheduling purposes 
	 * then there maybe one or more user of the set and a CCSM_release_set maybe
	 * more appropriate.
	 */
	if(!(ccsm_destroy_set_by_name(priv->ccsm_set_name)==0)){
		printk(KERN_CRIT "Cannot Destroy the CCSM SET %s\n",priv->ccsm_set_name);
	}

	/*
	 * Free the last of the private data.
	 */
	kfree(priv);
}

