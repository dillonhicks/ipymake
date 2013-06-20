
#ifdef CONFIG_CCSM
#include <linux/ccsm.h>
#endif

/*
 * Locally defined set of event identifiers of concern to this filter. Used to
 * map dynamically generated event IDs with the generated events onto values
 * that can be known at compile time and thus are usable as case arguments in a
 * switch statement.
 *
 * This set of values are returned by the classify function associated with this
 * filter. Note the EVENT_UNMAPPED value must always be present and is returned
 * for all events not otherwise explicitly listed.
 */
static enum ccsm_filter_enum {
	EVENT_UNMAPPED, 	/* Dynamic event not mapped */
	EVENT_FORK,
	EVENT_SIGNAL,
	EVENT_READ,
	EVENT_WRITE
};
#define LENGTH_OF_ENUM 4

/* event name to constant event ID */
static struct ename_to_ceid {
	int  ceid;
	char ename[MAX_NAME_LENGTH];
};

/* ? enumeration to constant event ID */
static struct ename_to_ceid ceid_vs_name[LENGTH_OF_ENUM] = {
	{.ceid = EVENT_FORK,   .ename = "DSTRM_FORK"},
	{.ceid = EVENT_SIGNAL, .ename = "DSTRM_SIGNAL"},
	{.ceid = EVENT_READ,   .ename = "DSTRM_READ"},
	{.ceid = EVENT_WRITE,  .ename = "DSTRM_WRITE"}
};

/* 
 * buckets for hash table which maps ceid's to deid's
 * @ceid:		constant event ID: constant event ID used by this 
 *                      filter so that we can write code making use of event
 *                      IDs
 * @deid:		dynamic event ID: runtime generated event ID in the
 *                      event special section
 * @hash_table_entry:	entry into hash table
 */
static struct ccsm_filter_hash_table_bucket_entry {
	int              ceid;
	int              deid;
	struct list_head bucket_list_entry;
};

static struct ccsm_filter_hash_table_bucket {
	struct list_head hash_bucket_list;
};

/*
 * This hash table is used to map the dynamic event IDs to the values enumerated
 * below for the set of events of concern to this filter.
 */
#define CCSM_FILTER_HASH_BITS 10

static struct ccsm_filter_hash_table_bucket ccsm_filter_table[1 << CCSM_FILTER_HASH_BITS];

int ccsm_filter_add_to_hash (void *dynamic_event_id) {

}

int ccsm_filter_classify (void *dynamic_event_id) {
	/*
	 * Consult the filter event hash function to see if the dynamic id of
	 * the current event is mapped or unmapped.
	 */
	struct ccsm_filter_hash_table_bucket_entry *bucket_entry;

	/* FIXME.J
	 *
	 * Create an inline or a subroutine to hold the repetitive, ugly hash
	 * code
	 *
	 * bucket = deid_lookup(dynamic_event_id);
	 */
	pointer_as_int = (unsigned int)dynamic_event_id;
	hash = jhash((u32*)pointer_as_int, (u32)sizeof(unsigned int), 0);
	bucket = &ccsm_ptr_table[hash & ((1 << CCSM_HASH_BITS) - 1)];

	list_for_each_entry_rcu(bucket_entry, &bucket->hash_bucket_list, bucket_list_entry) {
		if (bucket_entry->deid == dynamic_event_id) {
			return bucket_entry->ceid;
		}
	}

	return EVENT_UNMAPPED;
}

/**************************************************/

/*
 * Going to need some form of global/local storage, this is just a suggestion
 */
struct ccsm_filter_data {
	char     	*ccsm_set_name;		/* name of ccsm set filtering against */
	struct ccsm_set *ccsm_set_handle;	/* handle to ccsm set filtering against */
};

int
ccsm_config_func(struct datastream *d, void **data,
		union dski_ioc_filter_ctrl_params *params)
{
	/*
	 * Read in from user side the name of the set we will be filtering
	 * against and store it both for future reference.
	 */

	/*
	 * Attempt to create the named set.
	 * - initial assumption about the use of this pattern is that the
	 *   calling context will have created the named set and populated it
	 *   with some N initial members as required by the semantics of the
	 *   filter.
	 * - the ccsm_create_set routine returns a handle to the named set for quick
	 *   reference in the filter body of the Active Filter
	 *   - the created output parameter of the ccsm_create_set routine
	 *   indicates whether or not creation of the set was required.
	 */

	/*
	 * Allocate a per-filter-instance data structure and fill in the
	 * appropriate context data (ccsm_filter_data). Assign the **data pointer
	 * to the newly allocated per-filter-instance data.
	 */

	/*
	 * Assert flags associated with the set according to the semantics of
	 * the filter. Currently these flags are expressed in the CCSM set
	 * structure, but they might be in the per-filter-instance data
	 * structure.
	 */

	/*
	 * Populate the ccsm_filter_table with the set of events that we this
	 * filter cares about.
	 */
	
	/*
	 * For each element in the ceid_vs_ename table
	 *    event_name_to_deid
	 *    
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

}

