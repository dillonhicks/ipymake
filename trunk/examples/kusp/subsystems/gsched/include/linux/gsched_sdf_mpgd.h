#ifndef GSCHED_SDF_MPGD_H
#define GSCHED_SDF_MPGD_H
#include <linux/sched_gsched.h>

/* A string length limit used by MPGD */
#define MPGD_MAX_STR 35

/* Name of the MPGD SDF. Used by Group Scheduling for ID */
#define MPGD_SDF_NAME "sdf_mpgd"

/* Total ports available for use (includes input and output) */
#define MPGD_MAX_PORTS 12

/*
 * MPGD scheduler commands:
 */
#define MPGD_CMD_ADD_PORT		1
#define MPGD_CMD_GET_PORT_EVENT		5
#define MPGD_CMD_SET_DELTAZERO		7
#define MPGD_CMD_SET_DELAY_PHY		8
#define MPGD_CMD_PRINT_CONFIG		9
#define MPGD_CMD_ADD_CUT_PORT		10
#define MPGD_CMD_ADD_INPUT_GROUP_PORT	11
#define MPGD_CMD_ALLOC_PORT		12
#define MPGD_CMD_INIT			13

/*
 * MPGD Configurations
 *
 *   PTIDES_ES_C:		PTIDES Execution Strategy C
 */
#define PTIDES_ES_C			1

/*
 * MPGD Port Types
 *
 *  PORT_SOCK:			Network socket port (tcp/udp)
 *  PORT_CUSTOM:
 *     User-space manages event storage and transfer, but is still responsible
 *     for updating the timing information of events associated with this port
 *     in the scheduler by making Group Scheduling system calls.
 */
#define MPGD_PORT_SOCK		1
#define MPGD_PORT_CUSTOM	2

/*
 *
 */
#define MPGD_PORT_INPUT		1
#define MPGD_PORT_OUTPUT	2

/*
 * MPGD representation of +/- infinity using timespec format. This is the
 * user-space representation of time.
 *
 * MPGD_TSPEC_MAX_SEC:
 *    A large value used to mark infinity in timespec format.
 *    Must not overflow the sign bit.
 */
#define MPGD_TSPEC_MAX_SEC	(1<<30)
#define MPGD_TIMESPEC_POS_INF	{ .tv_sec = MPGD_TSPEC_MAX_SEC, .tv_nsec = 0 }
#define MPGD_TIMESPEC_NEG_INF	{ .tv_sec = (-MPGD_TSPEC_MAX_SEC), .tv_nsec = 0 }

/*
 * Event header used at the beginning of packets. Contains a known value to
 * do rudimentary consistency check, and the timestamp of the event contained in
 * the packet.
 */
#define MPGD_MAGIC_NUM 0x4321abcd
struct mpgd_event_header {
	int magic;
	struct timespec timestamp;
};

/*
 * Representation of event as a payload + header. The header contains the
 * timestamp of the event.
 */
#define MPGD_EVENT_SIZE 32
struct mpgd_event {
	struct mpgd_event_header header;
	char payload[MPGD_EVENT_SIZE];
};

#ifdef __KERNEL__

#ifdef CONFIG_MPGD_DEBUG
#define MPGD_DEBUG(fmt...) do { printk(fmt); } while (0)
#else
#define MPGD_DEBUG(fmt...)
#endif

/*
 * MPGD representation of +/- infinity using ktime_t format. This is the
 * in-kernel representation.
 */
#define MPGD_KTIME_POS_INF	(ktime_set(MPGD_TSPEC_MAX_SEC, 0))
#define MPGD_KTIME_NEG_INF	(ktime_sub(ktime_set(0, 0), ktime_set(MPGD_TSPEC_MAX_SEC, 0)))

/*
 * MPGD Configuration
 *
 * id:		integer identification (for lookups)
 * name:	string identification
 */
struct mpgd_config {
	int id;
	char name[MPGD_MAX_STR];
	int (*init)(struct gsched_group *);
	void (*enqueue)(struct gsched_group *, struct gsched_member *, struct rq *, int);
	void (*dequeue)(struct gsched_group *, struct gsched_member *, struct rq *, int);
};

/*
 * Port representation
 *
 *   type:		e.g. socket or custom
 *   idx:		id (index in various tables)
 *   inuse:		boolean usage flag
 *   member:		member (actor) port is attached to
 *   socket:		if socket-type, the in-kernel socket pointer
 *   direction;		input/output/??/...
 *   queue:
 *      queue of events for this port. this is currently only used by socket
 *      ports. for configurations that want to examine event queues we'll have
 *      to modify the MPGD framework to allow this when actors make use of
 *      custom port types (i.e. event queues might be in userspace).
 */
struct mpgd_port {
	int type;
	int idx;
	int direction;
	
	struct gsched_member *member;

	/* specific to network socket ports */
	struct socket *socket;
	struct list_head queue;

	int inuse;
};

/*
 * Per-member data
 */
struct mpgd_member_data {
	struct hrtimer next_event;
	struct mpgd_port *ports[MPGD_MAX_PORTS];
};

/*
 * Per-group data
 *
 * config:
 *   The current MPGD configuration (e.g. a given PTIDES execution strategy)
 *
 * ports:
 *   Storage for all ports. Output ports and input ports are represented with
 *   the same structure, but output ports don't need to be represented by the
 *   same data structure as input ports, that include for instance, event
 *   queues. This is not the most efficient representation and should be
 *   optimized in the future.
 *
 * delta0:
 *   effectively a direct adjacency matrix where a cost of infinity is used to
 *   indicate that a link doesn't exist. non-infinity costs indicate links and
 *   the cost is interpreted as the PTIDES specific delta0(i,o) value.
 */
struct mpgd_group_data {
	struct mpgd_config *config;

	struct mpgd_port ports[MPGD_MAX_PORTS];

	ktime_t delta0[MPGD_MAX_PORTS][MPGD_MAX_PORTS];
	ktime_t physical_delay[MPGD_MAX_PORTS];
	ktime_t offset[MPGD_MAX_PORTS];
	int dependency_cut[MPGD_MAX_PORTS][MPGD_MAX_PORTS];
	int input_group[MPGD_MAX_PORTS][MPGD_MAX_PORTS];
};

/*
 * Per-CPU run-queue structure. The MPGD scheduler runs tasks on the run-queue
 * in sequential order. A specific MPGD configuration may re-order the list to
 * implement other semantics, for example EDF.
 */
struct mpgd_run_queue {
	struct list_head wait_list;
	struct list_head run_queue;
};

/*
 * Interface to MPGD packet timestamp extraction facilties
 */
void mpgd_sentto(struct sock *sk, struct sk_buff *skb);
void mpgd_remove_member(struct gsched_member *member);
void mpgd_release_member(struct gsched_member *member);
int mpgd_register_socket(struct socket *sock, struct gsched_member *member, struct mpgd_port *port);

/*
 * In kernel representation of an event. In kernel events are put on queues, and
 * timestamps are represented using ktime_t.
 */
struct __mpgd_event {
	struct list_head queue_ent;
	ktime_t timestamp;
	struct mpgd_event data;
};
#endif

/*
 * Port configuration info used in communications between user-space and the
 * MPGD scheduler regarding a specific port.
 */
struct mpgd_port_param {
	int id;
	int type;
	int direction;
	
	/* param used with socket-type port */
	int fd;

	struct mpgd_event event;
};

/*
 * Base parameter structure used in communications between user-space and the
 * MPGD scheduler.
 */
struct mpgd_param {
	int cmd;

	struct mpgd_port_param port;
	struct mpgd_port_param port2;
	struct timespec time;

	/*
	 * temporary hack for write-back from set_mem_params
	 * - we need to implement a R/W params interface
	 */
	unsigned long addr;
};

#endif
