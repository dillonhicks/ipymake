#include <asm/uaccess.h>
#include <linux/limits.h>
#include <linux/sched.h>
#include <linux/file.h>
#include <linux/kernel.h>
#include <linux/list.h>
#include "dski_common.h"
#include <linux/string.h>
#include <linux/ccsm.h>
#include <linux/dski.h>

/*
 * This is the CCSM based Per-Task Filter.
 *
 * This is intended as a set based general per-task filter. It will only accept
 * or reject events based upon task membership in a user defined CCSM set and will
 * add all children of set members to the set, so that they too will be filtered
 * upon.
 */

/*
 * Local storage for set name, set handle, and mode of the filter. Mode is
 * limited to accepting or rejecting based upon membership in the named set.
 */
struct task_filter_data {
	unsigned int	mode;				/* see mode flags below */
	int		match_response;			/* TEMPORARY - match response, supplants mode */
	int		no_match_response;		/* TEMPORARY - no match response, supplants mode */
	long		pid;				/* legacy mode, allowing use of a single pid */
	char     	task_set_name[NAME_MAX+1];	/* name of ccsm set filtering against */
	struct ccsm_set *task_set_handle;		/* handle to ccsm set filtering against */
	unsigned int	fork_deid;			/* dynamic event id of the Fork event */
};

#define CCSM_FILTER_MODE_ACCEPT 0x1;
#define CCSM_FILTER_MODE_REJECT 0x2;

/*
 * Configure the CCSM filter
 */
/*
 * FIXME.j - personal annoyance, note that the declaration of filter functions
 * tend to be "XXXXfilter_X_func" while their structures tend to be
 * XXXX_filter_struct. Need to pick XXXXfilter or XXXX_filter naming scheme and
 * stick with it.
 */
int
taskfilter_c_func(struct datastream *d, void **data,
		union dski_ioc_filter_ctrl_params *params)
{
#ifdef CONFIG_CCSM
	struct dski_task_filter_ctrl *task_filter_params;
	struct task_filter_data *priv;
	struct ccsm_set *set;
	unsigned int deid;

	/*
	 * Read in from user side the name of the set we will be filtering
	 * against and and the desired filter mode and store them both for
	 * future reference.
	 */
	
	task_filter_params = &params->task_filter;
	if (!task_filter_params) {
		return -EINVAL;
	}

	/*
	 * Allocate a per-filter-instance data structure and fill in the
	 * appropriate context data (task_filter_data).
	 */

	priv = kmalloc(sizeof(struct task_filter_data), GFP_KERNEL);
	if (!priv) {
		return -ENOMEM;
	}

	/*
	 * Copy the name of the set to be filtered against from user space and
	 * store in our private data structure
	 */
	printk("I think the problem is here.......%s\n",params->task_filter.set_name);
	if (copy_from_user(priv->task_set_name, params->task_filter.set_name, NAME_MAX+1)) {
		kfree(priv);
		return -EFAULT;
	}

	printk("oops the problem is not here ....%s\n",params->task_filter.set_name);

	/*
	 * If a pid was supplied, ensure that it is valid, and store in our
	 * private data structure;
	 */
	if (task_filter_params->pid > 0) {
		priv->pid = task_filter_params->pid;
	} else {
		priv->pid = -1;
	}

	/*
	 * If mode was supplied, ensure that it is a valid mode, and store in
	 * our private data structure.
	 * FIXME.J - need default response validation checking
	 */
	//if (?) {
		priv->match_response = task_filter_params->match_response;
	//} else {
	//	priv->default_response = ?
	//}

	/* 
	 * Attempt to get a 'handle' to the named set and store in our private
	 * data structure.
	 */
	set = ccsm_find_set_by_name(priv->task_set_name);
	if (IS_ERR(set)) {
		kfree(priv);
		return PTR_ERR(set);
	}
	priv->task_set_handle = set;

	/*
	 * Attempt to retrieve the dynamic event ID of the Fork instrumentation
	 * point, which will be used to indicate when set addition may need to
	 * occur.
	 */
	deid = -1;
	/* FIXME.j - is this IP adequate to detect the creation of a kernel
	 * thread?
	 */
	deid = (unsigned int) find_ip_by_name("FORK","DO_FORK");
	if (deid < 0) {
		kfree(priv);
		return -EINVAL;
	}

	/*
	 * If everything was successful, assign the **data pointer to the
	 * newly allocated per-filter-instance, making it persistant data
	 * for this instance of the task_filter;
	 */
	*data = priv;
#endif
	return 0;
}

/*
 * This is the active CCSM filter function
 */
int
taskfilter_f_func(struct datastream *d, struct ds_event_record *evt, 
		void *data, int data_len, const void *extra_data)
{
#ifdef CONFIG_CCSM
	char *temp_component_name;
	struct task_struct *child_thread;
	struct task_filter_data *priv;
	ccsm_compid_task_t *task_id;
	struct ccsm_set *child_comp_set;
	int ret;

	/* Grab the private data */
	priv = data;
	
	/*
	 * Check currently executing thread against set membership
	 *
	 * If the current task is not a member of the set:
	 * - determine if we should accept or reject the event for logging as the setup
	 *   for the filter as specified by its mode
	 * 
	 * Note that the ccsm_get_id_task call increases the reference count for
	 * the id structure, and so this calling code must also free the
	 * structure exactly once along all exiting paths.
	 */
	task_id = ccsm_get_id_task(current);
#if 0
	ccsm_get_id_pipe(fs_id, inode_id);
	ccsm_get_id_socket(fs_id, inode_id);
	etc.
#endif

	ret = ccsm_is_member_by_id_quick(priv->task_set_handle, task_id);
#if 0
	ret = ccsm_is_member_by_handle_quick(priv->ccsm_set_handle, cur, CCSM_TYPE_TASK);
#endif
	if (ret) {
		ret = ccsm_free_id(task_id);
		/* FIXME.J - Output return value in intern DSTRM */
		return priv->no_match_response;
	}

	/* Is this a fork event? */
	if (evt->id == priv->fork_deid) {
		/* If so, set addition is required */
		child_thread = find_task_by_pid(evt->event_tag);
		
		/*
		 * Have CCSM attempt to generate a name for the task being added
		 * to the set and then create a component to represent that task
		 * in CCSM. Lastly, add it to the root set.
		 */
		ret = ccsm_gen_component_name(&temp_component_name, CCSM_TYPE_TASK);
		if (ret) {
			/* FIXME.J - Output DSTRM error value including the
			 * return value */
			return FLTR_PASS;
		}
		child_comp_set = ccsm_create_component(temp_component_name, task_id);
		if (IS_ERR(child_comp_set)) {
			/* FIXME.J - Output DSTRM error value including the
			 * return value */
			return FLTR_PASS;
		}
		ret = ccsm_add_member_quick(priv->task_set_handle, child_comp_set);
		if (ret) {
			/* FIXME.J - Output DSTRM error value including the
			 * return value */
			return FLTR_PASS;
		}
	}

	return priv->match_response;
#else
	return FLTR_PASS;
#endif
}

/*
 * Destroy the resources gathered by the CCSM filter.
 */
void
taskfilter_d_func(struct datastream *d, void *data)
{
#ifdef CONFIG_CCSM
	struct task_filter_data *priv;

	/*
	 * Clean up the per-instance data structures allocated to help
	 * with this filter
	 */
	priv = data;
	kfree(priv);
#endif
}

