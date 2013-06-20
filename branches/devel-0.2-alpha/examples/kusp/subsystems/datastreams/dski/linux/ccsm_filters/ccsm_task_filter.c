#include <asm/uaccess.h>
#include <linux/limits.h>
#include <linux/sched.h>
#include <linux/file.h>
#include <linux/kernel.h>
#include <linux/list.h>
#include "dski_common.h"
#include <linux/string.h>
#include <linux/ccsm.h>



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
	long		pid;				/* legacy mode, allowing use of a single pid */
	char     	ccsm_set_name[NAME_MAX+1];	/* name of ccsm set filtering against */
	struct ccsm_set *ccsm_set_handle;		/* handle to ccsm set filtering against */
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
	int ret, i, numpids;

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
	if (copy_from_user(&priv->ccsm_set_name, &task_filter_params->set_name, NAME_MAX+1)) {
		kfree(priv);
		return -EFAULT;
	}

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
	 * Attempt to get a 'handle' to the named set.
	 * - get a handle to the named set for quick reference in the filter
	 *   body of the Active Filter
	 *   - NOTE: CCSM will create the set as empty if it does not already
	 *   exist.
	 * - consider having the API call return whether or not it needed to
	 *   create the set or not
	 * - consider creating and dumping an error event into the stream
	 *   indicating that the API call needed to create the set
	 */



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
	/*
	 * Check currently executing thread against set membership
	 *
	 * If the current task is not a member of the set:
	 * - determine if we should accept or reject the event for logging as the setup
	 *   for the filter as specified by its mode

	 * If the current task is a member of the set:
	 * - determine if we should accept or reject the event for logging as the setup
	 *   for the filter as specified by its mode
	 *
	 * - attempt to notify the ccsm set of the action represented by the
	 *   event being filtered
	 *   - internally determine:
	 *      - is this an event ccsm EVER cares about.
	 *   	- is the event one that this ccsm set cares about (dependent on
	 *   	ccsm flags for this set)
	 *
	 *   	- determine deferred context or immediate context
	 *   		- if immediate context, call relevant ccsm event
	 *   		notifier
	 *	- in deferred context, forward the event to the deferred
	 *	instance of this filter
	 */

#endif
	/*
	 * Return the accept or reject flag
	 */
	return FLTR_PASS;
	//return FLTR_REJECT;
	//return FLRT_ACCEPT;
}

/*
 * Destroy the resources gathered by the CCSM filter.
 */
/*
 * FIXME.j - this should return an error as a matter of course, look into this
 */
void
taskfilter_d_func(struct datastream *d, void *data)
{
#ifdef CONFIG_CCSM
	/*
	 * Clean up the per-instance data structures allocated to help
	 * with this filter
	 * - name of set we care about
	 * - handle/reference to the set
	 * - mode
	 */
#endif
}

