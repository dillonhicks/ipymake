#include <linux/list.h>
#include <linux/fs.h>
#include <linux/relay.h>
#include <asm/semaphore.h>

#include <datastreams/dski.h>
#include <datastreams/entity.h>

/*
 * Enum containing Labels that we make use of within the traceme Active filter.
 */
enum {
	TRACE_DO_FORK,
	TRACE_SEND_SIGNAL,
	TRACE_SHM_AT,
	TRACE_LOCK,
	TRACE_FIFO,
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

struct file_dski_info{
            unsigned long inode_id;
            unsigned char filename[256];
            unsigned long fs_id;
	    char lockType[256];
	    struct list_head list;
};

struct fifo_dski_info{
            unsigned long inode_id;
            char fifoname[256];
            int mode;
	    struct list_head list;
};

struct shmid_lst {
	int id;
	struct list_head list;
};

struct fd_lst {
        unsigned int fd;
        struct list_head list;
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

struct unix_id_lst {
	unsigned long known_inode;
	char known_sys_id[DSCVR_SYSID_LEN];
	//char sun_path[DSCVR_PATHNAME_LEN];
	//unsigned long known_sock;
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
#ifdef CONFIG_TASK_ALIAS
	alias_t alias;
#endif
	char *ta_name;
	struct shmid_lst shmids;
	struct fd_lst fds;
	struct inet_id_lst inets;
	struct unix_id_lst uns;
	struct dup_lst dups;
	struct deid_to_ceid ptrs;
	struct file_dski_info locks;
	struct fifo_dski_info namedPips;
	int eids[IPS_MAX];
	pid_t traceme_pid;
};


int forkAction(struct dscvr_filter_priv *priv, unsigned int tag);
int sendSignalAction(struct dscvr_filter_priv *priv, unsigned int tag);
int duplicateFDAction(struct dscvr_filter_priv *priv, unsigned int tag);
int duplicateFDSecondTypeAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data);
int socketAcceptAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data);
int localConnectAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data);
int tcpConnectAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data);
int connectEndAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data);
int bindAction(struct dscvr_filter_priv *priv , unsigned int tag, const void *extra_data);
int sharedMemoryAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data);
int syscallAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data);
int namedPipeAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data);
int fileLockingAction(struct dscvr_filter_priv *priv, unsigned int tag, const void *extra_data);
int get_exec_name (struct task_struct *task, char *buffer, int len);
void emit_file_table_events(int pid);
