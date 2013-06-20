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
#include <linux/jhash.h>
#ifdef CONFIG_DISCOVERY
#include <linux/dscvr.h>
#include <linux/dski_netdata.h>
#include <linux/mount.h>
#include <linux/dcache.h>
#endif

#include <datastreams/dski.h>

#include "dski_common.h"
#include "dski_tracemeActions.h"

#ifdef CONFIG_DISCOVERY
/**
 * HashTable that is going to be used within the traceme active filter.
 */
#define TRACEME_HASH_TABLE_SIZE 14
struct list_head tracemeDeidHashTable[TRACEME_HASH_TABLE_SIZE];

/*
 * Create an entry into the list of known events that we care about in this filter.
 * and also add it to the hash table.
 */
int insertEvent(int ceid,char *family_name,char *event_name, unsigned int deid, struct dscvr_filter_priv *priv){
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
	arrayIndex = hash & (TRACEME_HASH_TABLE_SIZE-1);
	bucket = &(tracemeDeidHashTable[arrayIndex]);
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
int initializeHashTable(){
	struct list_head *cur;
	int i = 0;

	for (i = 0; i < TRACEME_HASH_TABLE_SIZE; i++) {
		cur = &(tracemeDeidHashTable[i]);
		INIT_LIST_HEAD(cur);
	}
	return 0;
}

/*
 * Preloading the set of events that we are going to look out for in
 * this filter.
 */
void insertingEventsWeCare(struct dscvr_filter_priv *priv){
#ifdef CONFIG_DSKI_HASH_TABLE
	initializeHashTable();
#endif
	insertEvent(TRACE_DO_FORK,"FORK","DO_FORK",get_deid_by_name("FORK","DO_FORK"),priv);
	insertEvent(TRACE_SEND_SIGNAL,"SIGNAL","SEND_SIGNAL",get_deid_by_name("SIGNAL","SEND_SIGNAL"),priv);
	insertEvent(TRACE_SHM_AT,"SHMEM","SHMAT",get_deid_by_name("SHMEM","SHMAT"),priv);
	insertEvent(TRACE_FIFO,"FIFO","FIFO_OPEN",get_deid_by_name("FIFO","FIFO_OPEN"),priv);
	insertEvent(TRACE_ACCEPT,"SOCKET","ACCEPT",get_deid_by_name("SOCKET","ACCEPT"),priv);
	insertEvent(TRACE_LOCAL_CONNECT,"SOCKET","LOCAL_CONNECT",get_deid_by_name("SOCKET","LOCAL_CONNECT"),priv);
	insertEvent(TRACE_TCP_CONNECT,"SOCKET","TCP_CONNECT",get_deid_by_name("SOCKET","TCP_CONNECT"),priv);
	insertEvent(TRACE_CONNECT_END,"SOCKET","CONNECT_END",get_deid_by_name("SOCKET","CONNECT_END"),priv);
	insertEvent(TRACE_BIND,"SOCKET","BIND",get_deid_by_name("SOCKET","BIND"),priv);
	insertEvent(TRACE_FCNTL_DUP,"FLOCK","DUP",get_deid_by_name("FLOCK","DUP"),priv);
	insertEvent(TRACE_DUP,"FILE","DUP",get_deid_by_name("FILE","DUP"),priv);
	insertEvent(TRACE_DUPFD,"FILE","DUPFD",get_deid_by_name("FILE","DUPFD"),priv);
	insertEvent(TRACE_SYS_CALL,"SYSCALL","SYSTEM_CALL",get_deid_by_name("SYSCALL","SYSTEM_CALL"),priv);
	insertEvent(TRACE_SYS_TR_FILTER,"SYSCALL","SYS_TR_FILTER",get_deid_by_name("SYSCALL","SYS_TR_FILTER"),priv);
}

/*
 * Update the preloaded set of events we care about with dynamic eids that 
 * we get from the user side.:OBSOLETE
 */
void updateEventsWithDeid(unsigned int deid,char *family_name, char *event_name,struct dscvr_filter_priv *priv){
	struct deid_to_ceid *tmpdmp;
	list_for_each_entry(tmpdmp, &(priv->ptrs.list), list) {
		if ((strcmp(family_name, tmpdmp->family_name) == 0) && (strcmp(event_name, tmpdmp->event_name) == 0)) {
			tmpdmp->deid = deid;
		}
	}
}

/*
 * Get the constant eid value for the corresponding dynamic eid value.
 */
int get_ceid(unsigned int deid, struct dscvr_filter_priv *priv){
	struct deid_to_ceid *tmpdmp;
	struct list_head *bucket;
	u32 hash;

#ifdef CONFIG_DSKI_HASH_TABLE
	// hash table search
	hash = jhash((u32*)&deid, (u32)sizeof(unsigned int), 0);
	bucket = &(tracemeDeidHashTable[hash & (TRACEME_HASH_TABLE_SIZE - 1)]);
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

int dscvr_filter_c_func(struct datastream *d, void **data, 
		union dski_ioc_filter_ctrl_params *params)
{
	char *uname, *unameptr;
	struct dscvr_filter_priv *priv;
	alias_t alias;

	/* Get the user-space name ptr and then copy the task alias name
	 * from user space into a kernel allocated memory area.*/
	/* user-space name ptr */
	unameptr = params->dscvr_filter.ta_name;
	if (!unameptr)
		return -EINVAL;
	
	uname = kmalloc(NAME_MAX+1, GFP_KERNEL);
	if (!uname)
		return -ENOMEM;
		
	if (copy_from_user(uname, unameptr, NAME_MAX+1)) {
		kfree(uname);
		return -EFAULT;
	}

	/* allocating filter's private data which is used to 
	 * maintain the filter state to track Information required 
	 * to deduce computation structure from a series of events */
	priv = kmalloc(sizeof(struct dscvr_filter_priv), GFP_KERNEL);
	if (!priv) {
		kfree(uname);
		return -ENOMEM;
	}
	
	/* Initialize the list that holds the mapping of dynamic event ids 
	 * to constant event ids*/
	INIT_LIST_HEAD(&(priv->ptrs.list));
	/* Creating the Mapping of dynamic event ids to constant event ids 
	 * that this filter cares about.
	 */
	insertingEventsWeCare(priv);

#ifdef CONFIG_TASK_ALIAS
	if (task_alias_get_alias_handle_always(uname, &alias)) {
		kfree(priv);
		kfree(alias);
		printk(KERN_CRIT "dski: task_alias_get_alias_handle failed\n");
		return -ENOMEM;
	}
#else
	printk(KERN_CRIT "Tried to filter on name using non-taskalias kernel\n");
	kfree(upids);
	kfree(priv);
	kfree(elements);
	return -EINVAL;
#endif
	
	/* link up rest of private data */
	priv->alias = alias;

	/* 
	 * FIXME: Also have to keep around the name because alias_t
	 * is private to task_alias
	 */
	priv->ta_name = uname;
	priv->traceme_pid = current->pid;
	INIT_LIST_HEAD(&(priv->shmids.list));
	INIT_LIST_HEAD(&(priv->fds.list));
	INIT_LIST_HEAD(&(priv->inets.list));
	INIT_LIST_HEAD(&(priv->uns.list));
	INIT_LIST_HEAD(&(priv->dups.list));
	INIT_LIST_HEAD(&(priv->locks.list));
	INIT_LIST_HEAD(&(priv->namedPips.list));
	// Pass the active filter private data, so that we can use it
	// in the filtering function.
	*data = priv;

	return 0;
}


int dscvr_filter_f_func(struct datastream *d, struct ds_event_record *evt, 
		void *data, int data_len, const void *extra_data)
{
	struct dscvr_filter_priv *priv = data;
	unsigned int eid = evt->id;
	unsigned int tag = evt->event_tag;
	int retval = FLTR_PASS;
 	
	int ceid = get_ceid(eid,priv);
	switch(ceid){
		case TRACE_DO_FORK:
		 	retval = forkAction(priv, tag);
		break;
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
		case TRACE_LOCK:
			retval = fileLockingAction(priv,tag,extra_data);
		break;
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

void dscvr_filter_d_func(struct datastream *d, void *data)
{
	struct dscvr_filter_priv *priv = data;
	struct shmid_lst *shmtmp;
	struct dup_lst *duptmp;
	struct list_head *pos, *t;
	struct fd_lst *fdtmp;
	struct inet_id_lst *tmpinet;
	struct unix_id_lst *tmpun;
	struct file_dski_info *tmplock;
	struct fifo_dski_info *tmpfifo;
	struct deid_to_ceid *tmpdeid_to_ceid;

	/* Free the shmids list */
	list_for_each_safe(pos, t , &(priv->shmids.list)) {
		shmtmp = list_entry(pos, struct shmid_lst, list);
		list_del(pos);
		kfree(shmtmp);
	}

	/* Free the Fifo List */
	list_for_each_safe(pos, t , &(priv->namedPips.list)) {
		tmpfifo = list_entry(pos, struct fifo_dski_info, list);
		list_del(pos);
		kfree(tmpfifo);
	}

	/* Free the locking list */
	list_for_each_safe(pos, t , &(priv->locks.list)) {
		tmplock = list_entry(pos, struct file_dski_info, list);
		list_del(pos);
		kfree(tmplock);
	}

	/* Free the Deid_to_ceid Structure */
	list_for_each_safe(pos, t , &(priv->ptrs.list)) {
		tmpdeid_to_ceid = list_entry(pos, struct deid_to_ceid, list);
		list_del(pos);
		kfree(tmpdeid_to_ceid);
	}

	/* And the fds list */
	list_for_each_safe(pos, t ,&(priv->fds.list)){
		fdtmp = list_entry(pos, struct fd_lst, list);
		list_del(pos);
		kfree(fdtmp);
	}
	/* And the sockets lists */
	list_for_each_safe(pos, t,&(priv->inets.list)){
		tmpinet = list_entry(pos, struct inet_id_lst, list);
		list_del(pos);
		kfree(tmpinet);
	}
	
	list_for_each_safe(pos, t,&(priv->uns.list)){
		tmpun = list_entry(pos, struct unix_id_lst, list);
		list_del(pos);
		kfree(tmpun);
	}

	/* And the dups list */
	list_for_each_safe(pos, t ,&(priv->dups.list)){
		duptmp = list_entry(pos, struct dup_lst, list);
		list_del(pos);
		kfree(duptmp);
	}

	kfree(priv->ta_name);
	kfree(priv);
}
#endif //CONFIG_DISCOVERY

