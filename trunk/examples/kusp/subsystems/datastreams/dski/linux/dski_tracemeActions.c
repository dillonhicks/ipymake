#include <asm/uaccess.h>
#include <linux/limits.h>
#include <linux/sched.h>
#include <linux/file.h>
#include <linux/kernel.h>
#include <linux/list.h>
#ifdef CONFIG_TASK_ALIAS
#include <linux/taskalias.h>
#endif
#ifdef CONFIG_GROUPSCHED
#include <linux/sched_gsched.h>
#endif
#include <linux/dski.h>
#ifdef CONFIG_DISCOVERY
#include <linux/dscvr.h>
#include <linux/dski_netdata.h>
#include <linux/mount.h>
#include <linux/dcache.h>
#endif

#include <datastreams/dski.h>
#include "dski_common.h"
#include "dski_tracemeActions.h"

/**
 * This file holds all the actions that needs to be taken whenever an application
 * that we are tracing passes a instrumentation point that the traceme active 
 * filter cares about. 
 *
 * Author: Bala Sridhar
 */

/*
 *Action Handler for Fork Instrumentation point. 
 */
int forkAction(struct dscvr_filter_priv *priv, unsigned int tag){

	/*
	 * Some process in the kernel has logged a fork event
	 */

	if (task_alias_exists_quick(current, priv->alias)) {
		/*
		 * This is a process in the group of processes we are tracking
		 * Add the child it forked (represented by its pid attached as
		 * the fork event's tag value) to the group of processes we are
		 * tracking
		 */

		pid_t child_pid = (pid_t) tag;
		if (task_alias_add_alias(child_pid, priv->ta_name, 0)) {
			printk(KERN_CRIT "Failed adding fork DSCVR to task alias: %d to %s\n", child_pid, priv->ta_name);
			/* FIXME:
			 * Put in the direct dski function call that generates the error event.
			 */
			return FLTR_PASS;
		}
		//printk("Fork added %d\n", child_pid);

		/*
		 * If the traceme tool is forking off the root thread, inject
		 * its file descriptor table into the datastream.
		 *
		 * FIXME: We already call find_task_by_pid in task alias
		 * code. There should be a better way to do this.
		 */
		//struct dup_lst dups;
		if (current->pid == priv->traceme_pid) {
			emit_file_table_events(child_pid);
		}
		return FLTR_ACCEPT;
	}
	return FLTR_PASS;
}

/*
 *This is action handler for the send signal instrumentation point. 
 */
int sendSignalAction(struct dscvr_filter_priv *priv, unsigned int tag){
	if(task_alias_exists_quick(current, priv->alias)){

		/*
		 * If a task alias does not exist to the task represented by the pid of the
		 * process we are sending the signal to
		 */

		struct task_struct *ts = find_task_by_pid(tag);
		char exec_name[DSCVR_PATHNAME_LEN];

		if(!(task_alias_exists_quick(ts, priv->alias))) {
		//	struct dup_lst dups;
			if (get_exec_name(current, exec_name, DSCVR_PATHNAME_LEN)) {
				printk(KERN_CRIT "Failed getting a discovered tasks \
						exec_name. PID: %d\tGroup%s\n", \
						current->pid, priv->ta_name);
				return FLTR_PASS;
			}

			if(task_alias_add_alias((pid_t)tag, priv->ta_name, 0)){
				printk(KERN_CRIT "FAILED adding discovered task: \
						%d to %s\n",tag, \
						priv->ta_name);
				return FLTR_PASS;
			}
		//	printk("Signal added %d\n", tag);

			DSTRM_EVENT_DATA(SIGNAL, SIGSEND_ADD, 0, \
					strnlen(exec_name, DSCVR_PATHNAME_LEN), \
					exec_name, "print_string");
		}
	}
	return FLTR_PASS;
}

/*
 * In regular dup, we do not have access to the old and new
 * fd in the same spot in the kernel. Here we record the old
 * fd, and when we have access to the new fd, we emit a DUP_X
 * event in the next block of code
 */
int duplicateFDAction(struct dscvr_filter_priv *priv, unsigned int tag){

	struct dup_lst *tmpdup;

	if (task_alias_exists_quick(current, priv->alias)) {

		list_for_each_entry(tmpdup, &(priv->dups.list), list) {
			if (tmpdup->pid == current->pid)
				printk(KERN_CRIT "ERROR: Got dup evt before \
						seeing dupfd on (pid, fd): \
						(%u, %d)\n", current->pid, tag);
			return FLTR_PASS;
		}

		tmpdup = kmalloc(sizeof(struct dup_lst), GFP_KERNEL);
		tmpdup->pid = (pid_t)current->pid;
		tmpdup->fd = tag;struct dup_lst dups;
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

	if (task_alias_exists_quick(current, priv->alias)) {

		list_for_each_entry(tmpdup, &(priv->dups.list), list) {
			if (tmpdup->pid == current->pid) {
				dup_info_t *dup_data;
				open_close_info_t *info;

				info = (open_close_info_t *) extra_data;
				dup_data = kmalloc(sizeof(dup_info_t), GFP_KERNEL);
				/* FIXME.b : change this to FLTR_PASS and pass an internal error event (memory error).*/
				if(!dup_data)
					return -ENOMEM;

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
	if (!task_alias_exists_quick(current, priv->alias)) {		
		socket_info_t *sk_info = (socket_info_t *) extra_data;
		int new_conn = 0;
		if (sk_info->family == AF_UNIX) {
			struct unix_id_lst *tmpun; 
			list_for_each_entry(tmpun, &(priv->uns.list), list) {
				if (tmpun->known_inode == sk_info->known_inode && \
						(strncmp(tmpun->known_sys_id, sk_info->known_sys_id, \
							 DSCVR_SYSID_LEN)) == 0) {
					new_conn = 1;
					break;
				}
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
			char exec_name[DSCVR_PATHNAME_LEN];

			if (get_exec_name(current, exec_name, DSCVR_PATHNAME_LEN)) {
				printk(KERN_CRIT "Failed getting a discovered tasks \
						exec_name. PID: %d\tGroup%s\n", current->pid, \
						priv->ta_name);
				return FLTR_PASS;
			}

			if (task_alias_add_alias(current->pid, priv->ta_name, 0)) {
				printk(KERN_CRIT "Failed adding accept Socket to task \
						alias: %s\n", priv->ta_name);
				return FLTR_PASS;
			} 
			//printk("Server added %d\n", current->pid);

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
	if (task_alias_exists_quick(current, priv->alias)) {
		socket_info_t *sk_info = (socket_info_t *) extra_data;
		struct unix_id_lst *tmpun; 
		tmpun = kmalloc(sizeof(struct unix_id_lst), GFP_KERNEL);
		tmpun->known_inode = (unsigned long) sk_info->known_inode;
		strncpy(tmpun->known_sys_id, sk_info->known_sys_id, DSCVR_SYSID_LEN);
		list_add(&(tmpun->list), &(priv->uns.list));
		return FLTR_PASS;
	} else {
		/*
		 * Discovery needs to know the listening inode of sockets we are
		 * discovering in order to correctly pair socket connections in
		 * postprocessing
		 */
		struct unix_id_lst *tmpun; 
		list_for_each_entry(tmpun, &(priv->uns.list), list) {
			socket_info_t *sk_info = (socket_info_t *) extra_data;
			if (tmpun->known_inode == sk_info->known_inode && \
					(strncmp(tmpun->known_sys_id, sk_info->known_sys_id, \
						 DSCVR_SYSID_LEN)) == 0) {
				return FLTR_ACCEPT;
			}
		}
	}
	return FLTR_PASS;
}

/*
 * For threads we are tracking, add this port number to a list of
 * known port numbers
 */
int tcpConnectAction(struct dscvr_filter_priv *priv, unsigned int tag,const void *extra_data){
	if (task_alias_exists_quick(current, priv->alias)) {
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
	if (!task_alias_exists_quick(current, priv->alias)) {		
		socket_info_t *sk_info = (socket_info_t *) extra_data;
		int new_conn = 0;
		if (sk_info->family == AF_UNIX) {
			struct unix_id_lst *tmpun; 
			list_for_each_entry(tmpun, &(priv->uns.list), list) {
				if (tmpun->known_inode == sk_info->known_inode && \
						(strncmp(tmpun->known_sys_id, sk_info->known_sys_id, \
							 DSCVR_SYSID_LEN)) == 0) {
					new_conn = 1;
					break;
				}
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
				char exec_name[DSCVR_PATHNAME_LEN];

				if (get_exec_name(current, exec_name, DSCVR_PATHNAME_LEN)) {
					printk(KERN_CRIT "Failed getting a discovered tasks \
							exec_name. PID: %d\tGroup%s\n", current->pid, \
							priv->ta_name);
					return FLTR_PASS;
				}

				if (task_alias_add_alias(current->pid, priv->ta_name, 0)) {
					printk(KERN_CRIT "Failed adding connect Socket to task \
							alias: %s\n", priv->ta_name);
					return FLTR_PASS;
				}   
				//printk("Client added %d\n", current->pid);

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

		if (task_alias_exists_quick(current, priv->alias)) {
			socket_info_t *sk_info = (socket_info_t *) extra_data;
			/*
			 * Add to list of sockets we are tracking
			 * XXX: Not sure how to handle known_inodes == 0
			 */
			if (sk_info->family == AF_UNIX && sk_info->known_inode != 0) {
				struct unix_id_lst *tmpun;
				tmpun = kmalloc(sizeof(struct unix_id_lst), GFP_KERNEL);
				tmpun->known_inode = (unsigned long) sk_info->known_inode;
				strncpy(tmpun->known_sys_id, sk_info->known_sys_id, DSCVR_SYSID_LEN);
				list_add(&(tmpun->list), &(priv->uns.list));
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
		struct shmid_lst *tmpshm;

		if (task_alias_exists_quick(current, priv->alias)) {

			/*
			 * If the shmid represented by the tagged data is already
			 * in the list of shmids we are tracking, we don't need
			 * to do anything so jump out of here
			 */

			list_for_each_entry(tmpshm, &(priv->shmids.list), list) {
				if (tmpshm->id == tag)
					return FLTR_PASS;
			}

			/* 
			 * A process in the group we are tracking attached
			 * to a shared memory segment that is not on the list
			 * of segments we are currently tracking
			 */

			tmpshm = kmalloc(sizeof(struct shmid_lst), GFP_KERNEL);
			tmpshm->id = tag;
			list_add(&(tmpshm->list), &(priv->shmids.list));

		} else {
			/*
			 * The process is not in the group we are tracking
			 */
			list_for_each_entry(tmpshm, &(priv->shmids.list), list) {
				if (tmpshm->id == tag) {
					char exec_name[DSCVR_PATHNAME_LEN];

					if (get_exec_name(current, exec_name, DSCVR_PATHNAME_LEN)) {
						printk(KERN_CRIT "Failed getting a discovered tasks \
								exec_name. PID: %d\tGroup%s\n", current->pid, \
								priv->ta_name);
						return FLTR_PASS;
					}

					/*
					 * A process not yet in the group is attaching to a shared
					 * memory segment that a process in our group has attached to
					 */

					if(task_alias_add_alias(0, priv->ta_name, 0)){
						printk(KERN_CRIT "FAILED adding discovered task: %d to %s\n",tag, priv->ta_name);
						return FLTR_PASS;
					}
					//printk("Shmat added %d\n", tag);

					DSTRM_EVENT_DATA(SHMEM, SHMAT_ADD, 0, strnlen(exec_name, DSCVR_PATHNAME_LEN), exec_name, "print_string");
					return FLTR_PASS;
				}
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
		syscallInfo = (struct dski_syscall *)extra_data;
		int sysNum = syscallInfo->nr;

		if (task_alias_exists_quick(current, priv->alias)) {
			DSTRM_EVENT_DATA(SYSCALL, SYS_TR_FILTER, current->pid,sizeof(sysNum),&sysNum,"print_int");
		}
	return FLTR_PASS;
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
		struct fifo_dski_info fifo_info;
		unsigned long inode_id = 0;
		fifo_info = *(struct fifo_dski_info *)extra_data;
		inode_id=fifo_info.inode_id;
		struct fifo_dski_info *tmpfd;

		//printk("Inside FIFO_OPEN value of inode_id is %lu\n", inode_id);

		// we check if the thread is already present in the group, if it is not then we try to
		// check whether it is using a named pipe that we care about, if so add the thread to our 
		// task alias group 

		if (!(task_alias_exists_quick(current, priv->alias))) {
		//	printk("task does not exist\n");
			list_for_each_entry(tmpfd,&(priv->namedPips.list),list) {
				if(tmpfd->inode_id == inode_id){

					if (task_alias_add_alias((pid_t)tag, priv->ta_name, 0)) {
						printk(KERN_CRIT "Failed adding FIFO DSCVR to task alias: %lu to %s\n", inode_id, priv->ta_name);
						return -EINVAL;
					}

				}
			}
			return FLTR_ACCEPT;

		// if the thread already exist in our task alias group then we check whether it is using the same named pipe,
		// if not then we try to add the inode id to our list, because the named pipe is accessed by one of the thread 
		// already registered with the task alias group
		} else {
			//printk("task exist \n");
			list_for_each_entry(tmpfd,&(priv->namedPips.list),list){
				if(tmpfd->inode_id == inode_id)
					return FLTR_PASS;
			}
			tmpfd = kmalloc(sizeof(struct fifo_dski_info), GFP_KERNEL);
			tmpfd->inode_id = inode_id;
			list_add(&(tmpfd->list),&(priv->namedPips.list));
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
		struct file_dski_info file_info;
		unsigned long inode_id = 0;
		file_info = *(struct file_dski_info *)extra_data;
		inode_id=file_info.inode_id;
		struct file_dski_info *tmpfd;
		//printk("Inside LOCK value of inode_id is %lu\n", inode_id);

		// if the thread is not already present in the group , we check whether it access any of the file inode id's
		// to be locked if so then we add that thread to the task alias group

		if (!(task_alias_exists_quick(current, priv->alias))) {
		//	printk("task does not exist\n");
			list_for_each_entry(tmpfd,&(priv->locks.list),list) {
				if(tmpfd->inode_id == inode_id){
					if (task_alias_add_alias((pid_t)tag, priv->ta_name, 0)) {
						printk(KERN_CRIT "Failed adding fork FILELOCK to task alias: %lu to %s\n", inode_id, priv->ta_name);
						return FLTR_PASS;
					}        
				}

			}
			return FLTR_ACCEPT;

			// if the thread already exist in our group then we try to check whether it uses the same file to be locked,
			// if not then we try to add the new inode id of the file that a thread that we care about accesses to our list
		} else {
		//	printk("task exist \n");
			list_for_each_entry(tmpfd,&(priv->locks.list),list){
				if(tmpfd->inode_id == inode_id)
					return FLTR_PASS;
			}
			tmpfd = kmalloc(sizeof(struct file_dski_info), GFP_KERNEL);
			tmpfd->inode_id = inode_id;
			list_add(&(tmpfd->list),&(priv->locks.list));
		}
	return FLTR_PASS;
}

// Get the Exec name that the thread is executing.
int get_exec_name (struct task_struct *task, char *buffer, int len)
{
		struct vm_area_struct * vma;
		struct vfsmount * mnt;
		struct dentry * dentry;  
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
			mnt = mntget(vma->vm_file->f_path.mnt);
			dentry = dget(vma->vm_file->f_path.dentry);
			strncpy(buffer, d_path(dentry, mnt, buffer, len), len);
			mntput(mnt);
			dput(dentry);
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
		task = find_task_by_pid(pid);
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
}
