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
#ifdef CONFIG_DISCOVERY
#include <linux/dscvr.h>
#include <linux/dski_netdata.h>
#include <linux/mount.h>
#include <linux/dcache.h>
#endif
#include "dski_common.h"
#include <linux/string.h>

/*
 * System Monitor Active Filter Functions Implementation. A lot has to be done in this active
 * filter code. this is just the beginning.
 * Author: Bala Sridhar.
 */

// used for storing the shared libraries list.	
struct shared_list {
	char shLibName[NAME_MAX+1];
	struct list_head list;
};
// used for storing the system call list.
struct syscall_list {
	int num;
	struct list_head list;
};

struct dscvr_filter_priv {
	char *procfile_name;
	struct shared_list shList;
	struct syscall_list ssList;
	int eids[IPS_MAX];
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

// Is not being used, but possibly useful in the future. 
struct process_info {
	char process_name[DSCVR_PATHNAME_LEN];
	int process_pid;
};

// Configuration step.
int smonitor_c_func(struct datastream *d, void **data, 
		union dski_ioc_filter_ctrl_params *params)
{
	//printk("Using SystemMonitor C\n");
	struct dscvr_filter_priv *priv;
	struct dski_dscvr_ip *ueips, *ueipsptr, *cureip, *tmpeip;
	struct dski_monitor_list *lis, *sharedList, *tempList;
	struct dski_monitor_sysList *sys, *sysList, *tempSys;
	char *procfile_name, *procfilenameptr;
	int i;

	procfilenameptr = params->smon_filter.procfile_name;
	if(!procfilenameptr)
		return -EINVAL;
	
	procfile_name = kmalloc(NAME_MAX+1, GFP_KERNEL);
	if(!procfile_name)
		return -ENOMEM;

	// copy the procfilename that is going to be used for creating the proc file from the user side.
	if (copy_from_user(procfile_name, procfilenameptr, NAME_MAX+1)){
		kfree(procfile_name);
		return -EFAULT;
	}

	lis = params->smon_filter.lists;
	if (!lis)
		return -EINVAL;

	sharedList = kmalloc(sizeof(*sharedList), GFP_KERNEL);
	if (!sharedList)
		return -ENOMEM;
	
	// copy the list of shared libraries that needs to be looked out for from the user side.
	if (copy_from_user(sharedList,lis,sizeof(*sharedList))){
		kfree(sharedList);
		return -EFAULT;
	}

	sys = params->smon_filter.sysLs;
	if (!sys)
		return -EINVAL;

	sysList = kmalloc(sizeof(*sysList), GFP_KERNEL);
	if (!sysList)
		return -ENOMEM;

	// copy the list of system calls that needs to be looked out for from the user side.
	if (copy_from_user(sysList, sys, sizeof(*sysList))){
		kfree(sysList);
		return -EFAULT;
	}
	
	/* Now, do the list of ueips */
	ueipsptr = params->smon_filter.eips;
	if (!ueipsptr)
		return -EINVAL;

	/* First, get the head of the list */
	ueips = kmalloc(sizeof(*ueips), GFP_KERNEL);
	if (!ueips)
		return -ENOMEM;

	if (copy_from_user(ueips, ueipsptr, sizeof(*ueips))) {
		kfree(ueips);
		return -EFAULT;
	}

	/* And the rest of the list */
	for ( cureip = ueips; cureip->next != NULL; cureip = cureip->next ) {
		ueipsptr = cureip->next;

		tmpeip = kmalloc(sizeof(*ueips), GFP_KERNEL);
		if (!tmpeip) {
			for (cureip = ueips; cureip != NULL;) {
				tmpeip = cureip;
				cureip = cureip->next;
				kfree(tmpeip);
			}
			return -ENOMEM;
		}

		if (copy_from_user(tmpeip, ueipsptr, sizeof(*tmpeip))) {
			for (cureip = ueips; cureip != NULL;) {
				tmpeip = cureip;
				cureip = cureip->next;
				kfree(tmpeip);
			}
			return -EFAULT;
		}

		cureip->next = tmpeip;
	}
	
	/* filter's private data */
	priv = kmalloc(sizeof(*priv), GFP_KERNEL);
	if (!priv) {
		kfree(sharedList);
		kfree(sysList);
		return -ENOMEM;
	}

	/* Each dscvr ip has its own slot in the priv->eids array.
	 * If discovery is enabled for that ip, that slot will
	 * hold the event id of that ip. Otherwise, it holds 0.
	 */

	for (i = 0; i < IPS_MAX; i++) {
		priv->eids[i] = 0;
	}

	/* Store eids from the ueips list into the eid array */
	for (cureip = ueips; cureip != NULL; cureip = cureip->next) {

		/*
		 * FIXME: Make this a function
		 */

		if ((strcmp(cureip->fname,"SMON") == 0) && (strcmp(cureip->ename, "OPEN") == 0)) {
			priv->eids[OPEN] = cureip->eid;
		} else if ((strcmp(cureip->fname,"SMON") == 0) && (strcmp(cureip->ename, "PINFO") == 0)) {
			priv->eids[PINFO] = cureip->eid;
		} else if ((strcmp(cureip->fname,"SYSCALL") == 0) && (strcmp(cureip->ename, "SYSTEM_CALL") == 0)) {
			priv->eids[SYSTEM_CALL] = cureip->eid;
		} else if ((strcmp(cureip->fname,"SMON") == 0) && (strcmp(cureip->ename, "PSYS") == 0)) {
			priv->eids[PSYS] = cureip->eid;
		}
		/*else {
			printk(KERN_CRIT "discovery filter: unknown ip: %s/%s\n", cureip->fname, cureip->ename);
		}*/
	}

	priv->procfile_name = procfile_name;	
	// create the proc file.
	create_proc_file(priv->procfile_name);
	INIT_LIST_HEAD(&(priv->shList.list));
	INIT_LIST_HEAD(&(priv->ssList.list));

	for (tempList = sharedList; tempList != NULL; tempList= tempList->next){
		printk("names : %s\n",tempList->shLibName);	
		struct shared_list *tmp_l;
		tmp_l = kmalloc(sizeof(struct shared_list), GFP_KERNEL);
		strcpy(tmp_l->shLibName, tempList->shLibName);
		list_add(&(tmp_l->list), &(priv->shList.list));
	}

	for(tempSys = sysList; tempSys != NULL; tempSys = tempSys->next){
		printk("sys num : %d\n", tempSys->num);
		struct syscall_list *tmp_s;
		tmp_s = kmalloc(sizeof(struct syscall_list), GFP_KERNEL);
		tmp_s->num = tempSys->num;
		list_add(&(tmp_s->list), &(priv->ssList.list));
	}

	*data = priv;

	/* At this point, we can free up the ueips list as well */
	for (cureip = ueips; cureip != NULL;) {
		tmpeip = cureip;
		cureip = cureip->next;
		kfree(tmpeip);
	}

	return 0;
}

/**
 * Getting the name of the executable that the current thread is executing. 
 * From the memory structure of the process we are able to get the dentry structure 
 * and from the dentry structure we are able to get the full path to the executable.
 */
int get_name (struct task_struct *task, char *buffer, int len)
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

/*
 * This is the active filter func.
 */
int smonitor_f_func(struct datastream *d, struct ds_event_record *evt, 
		void *data, int data_len, const void *extra_data)
{
	struct dscvr_filter_priv *priv = data;
	unsigned int eid = evt->id;
	unsigned int tag = evt->event_tag;
	open_close_info_t *info;
	struct dski_syscall *syscallInfo;
	struct shared_list *shLib;
	struct syscall_list *ssLis;
	int count = 0,sysNum;
	char *name;

	// the file open system call is used for reading in shared libraries.
	// so we pass only that event that is an open on 
	// the shared libraries that we care about.we also send a datastream event 
	// with the thread pid and the executable name 
	// that opened the shared library.
	if(eid == priv->eids[OPEN]){
		info = (open_close_info_t *) extra_data;
		char exec_name[DSCVR_PATHNAME_LEN];

		list_for_each_entry(shLib, &(priv->shList.list),list) {	
			name = shLib->shLibName;
			//printk("name : %s\n", name);
			if (strstr(info->pathname,name)){
				//printk("UsingSystemMonitor F\n");
				write_to_procfile(current->pid);
				get_name(current, exec_name, DSCVR_PATHNAME_LEN);
				if (exec_name != NULL) {
					// debugging purposes
					printk("name to be found : %s : %s : %d : %s \n",info->pathname,name, current->pid, exec_name);	
				}
				count = count + 1;
			}
		}	
		
		if (count == 1){
			DSTRM_EVENT_DATA(SMON,PINFO,current->pid,strnlen(exec_name, DSCVR_PATHNAME_LEN), exec_name,"print_string");
		} else {
		 	return FLTR_REJECT;
		}

	} else if (eid == priv->eids[PINFO]){
		//printk("within pinfo\n");
		return FLTR_ACCEPT;

	// same is the case with the system calls with one difference we send just the thread pid that issued the system call.
	} else if (eid == priv->eids[SYSTEM_CALL]){
		syscallInfo = (struct dski_syscall *) extra_data;
		list_for_each_entry(ssLis, &(priv->ssList.list),list){
			sysNum = syscallInfo->nr;
			if (sysNum == ssLis->num){
			//	printk("Found Match\n");
				count = count +1;
			}
		}
		if (count == 1) {
			DSTRM_EVENT(SMON,PSYS,current->pid);
			//DSTRM_INTERNAL_EVENT(SMON,PSYS,current->pid);
		}else {
			return FLTR_REJECT;
		}

	} else if (eid == priv->eids[PSYS]){
		return FLTR_ACCEPT;
	}

	return FLTR_PASS;
}

/*
 * Destroy the resources gathered by the system Monitor filter.
 */
void smonitor_d_func(struct datastream *d, void *data)
{
	//printk("UsingSystemMonitor D\n");

	struct dscvr_filter_priv *priv = data;
	struct shared_list *tempdump;
	struct syscall_list *tempsys;
	struct list_head *pos, *t;

	list_for_each_safe(pos, t , &(priv->shList.list)){
		tempdump = list_entry(pos, struct shared_list, list);
		list_del(pos);
		kfree(tempdump);
	}

	list_for_each_safe(pos, t, &(priv->ssList.list)){
		tempsys = list_entry(pos, struct syscall_list, list);
		list_del(pos);
		kfree(tempsys);
	}

	if(priv->procfile_name){
		remove_proc_file(priv->procfile_name);
	}

	kfree(priv);
}

