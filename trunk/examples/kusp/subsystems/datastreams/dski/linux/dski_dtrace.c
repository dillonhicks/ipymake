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


struct dscvr_filter_priv {
	char *process_name;
	int pid;
	struct task_struct *process_struct;
	int eids[IPS_MAX];
};

// Filter function..............
int dtrace_f_func(struct datastream *d, struct ds_event_record *evt, void *data, int data_len, const void *extra_data){
	
//	printk("Dtrace f func\n");
	struct dscvr_filter_priv *priv = data;
	unsigned int eid = evt->id;
	unsigned int tag = evt->event_tag;

//	if(eid == priv->eids[SEND_SIGNAL]){
	 	if (priv->pid == tag){
			printk("matched\n");
			return FLTR_ACCEPT;
		}
//	}
	
	return FLTR_REJECT;
}

// Configuration Function..............
int dtrace_c_func(struct datastream*d, void **data, union dski_ioc_filter_ctrl_params *params){
//	printk("Dtrace c func\n");
	struct dscvr_filter_priv *priv;
	struct dski_dscvr_ip *ueips, *ueipsptr, *cureip, *tmpeip;
	char *process_name, *process_name_ptr;
	int pidValue,i;
	pid_t pidval;


	process_name_ptr = params->dtFilter.process_name;
	if(!process_name_ptr)
		return -EINVAL;
	
	process_name = kmalloc(NAME_MAX+1, GFP_KERNEL);
	if(!process_name)
		return -ENOMEM;

	// copy the procfilename that is going to be used for creating the proc file from the user side.
	if (copy_from_user(process_name, process_name_ptr, NAME_MAX+1)){
		kfree(process_name);
		return -EFAULT;
	}

	pidValue = params->dtFilter.pid;
	/* Now, do the list of ueips */
	ueipsptr = params->dtFilter.eips;
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

	priv->process_name = process_name;
	priv->pid = pidValue;
	pidval = (pid_t)pidValue;
	priv->process_struct = find_task_by_pid(pidval);

	*data = priv;

	/* At this point, we can free up the ueips list as well */
	for (cureip = ueips; cureip != NULL;) {
		tmpeip = cureip;
		cureip = cureip->next;
		kfree(tmpeip);
	}
	return 0;
}

// Destroy Function.......
void dtrace_d_func(struct datastream *d, void *data){
//	printk("Dtrace d func\n");

	struct dscvr_filter_priv *priv = data;
	struct list_head *pos, *t;

	kfree(priv);
	
}
