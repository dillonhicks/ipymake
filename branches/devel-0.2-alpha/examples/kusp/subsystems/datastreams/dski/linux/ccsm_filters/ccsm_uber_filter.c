#include <asm/uaccess.h>
#include <linux/limits.h>
#include <linux/sched.h>
#include <linux/file.h>
#include <linux/kernel.h>
#include <linux/list.h>
#include "dski_common.h"
#include <linux/string.h>

#ifdef CONFIG_CCSM
#include <linux/ccsm.h>
#endif

#ifdef 0

/* 
 * Might need? Registration of Callbacks into Group Scheduling from the Active
 * Filter.
 */
#ifdef CONFIG_GROUPSCHED
#include <linux/sched_gsched.h>
#endif

#endif


/*
 * FIXME.J -- NOTES ON UPDATED TO DS ACTIVE FILTER FRAMEWORK
 *
 * Updating is required to support more general use including multiple instances
 * of a filter being used simultaneously with unique per-instance data.
 *
 * The datastream framework must now include a structure representing an
 * instance of filter use. It should include:
 * - pointer to the filter function of the filter
 * - pointer to the destroy function of the filter
 * - pointer to the per-instance context argument (void *)
 *   - this should be a pointer to arbitrarily sized storate which is a
 *   structure providing context data on a per-filter-instance required for it
 *   function properly. For example:
 *      the ccsm filter's unique data would a pointer to a structure containing
 *      the name of the set and the handle to the set.
 *
 * Additions to the current interface:
 * - the filter create function should be given a pointer to the per-instance
 *   filter structure so that it can fill in the filter instance context data
 *   (void *)
 * - the Active Filter 'filter' function also needs to take the (void *) to the
 *   context data as an argument
 * - the destroy function should also receive the (void *) as an argument so
 *   that it can clean-up its per-instance-of-filter data.
 */


/*
 * This is the Computation Component Set Manager Filter (CCSM Filter).
 *
 * This is intended as a general filter because it will only accept or reject
 * events based upon CCSM set membership. The wide range of possible semantics
 * thus depends on the way in which the associated CCSM set semantics are
 * configured.
 *
 * Per-Task Filter Example:
 * 	The user-side API creates a CCSM set and adds tasks of interest to the
 * 	set using either name or PID as appropriate. The set expansion flags are
 * 	then set to add additional tasks to the set on fork or other
 * 	task interaction events as desired.
 */

/*
 * Going to need some form of global/local storage, this is just a suggestion
 */
struct ccsm_filter_data {
	unsigned int	mode;			/* see mode flags below */
	char     	*ccsm_set_name;		/* name of ccsm set filtering against */
	struct ccsm_set *ccsm_set_handle;	/* handle to ccsm set filtering against */
};

#define CCSM_FILTER_MODE_ACCEPT 0x1;
#define CCSM_FILTER_MODE_REJECT 0x2;

/*
 * Configure the CCSM filter
 */
int
ccsm_c_func(struct datastream *d, void **data,
		union dski_ioc_filter_ctrl_params *params)
{
	/*
	 * Read in from user side the name of the set we will be filtering
	 * against and and the desired filter mode and store them both for
	 * future reference.
	 */
	
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
	 * Allocate a per-filter-instance data structure and fill in the
	 * appropriate context data (ccsm_filter_data). Assign the **data pointer
	 * to the newly allocated per-filter-instance data.
	 */

	/*
	 * Note that the user-side code which is using the ccsm now determines
	 * the resulting filter semantics through the use of per-ccsm-set flags. 
	 */

	return 0;
}

/*
 * This is the active CCSM filter function
 */
int
ccsm_f_func(struct datastream *d, struct ds_event_record *evt, 
		void *data, int data_len, const void *extra_data)
{
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
void
ccsm_d_func(struct datastream *d, void *data)
{
	/*
	 * Clean up the per-instance data structures allocated to help
	 * with this filter
	 * - name of set we care about
	 * - handle/reference to the set
	 * - mode
	 */
}

