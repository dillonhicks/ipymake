#define _GNU_SOURCE
#include <getopt.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <sched.h>
#include <sys/syscall.h>

#ifdef HAVE_LIBGSL
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#endif

#include <configfile.h>
#include <sched_gsched.h>
#include "bp_ccsm_dsui.h"

#define MAX_LEN 25
#define MAX_PIPELINE_MESSAGE 100

#define gettid() syscall(__NR_gettid)

/*
 * A note on a node's workloop:
 *
 * GNU Scientific draws from a poisson distribution. This should be specified in
 * the configuration file, which it is not. I'm not sure if the change is hard
 * or easy, but I do some people are going to be making a pass on this code in
 * the near future.
 */

#ifdef HAVE_LIBGSL
/* gnu scientific state */
static const gsl_rng_type *T;
static gsl_rng *r;
#endif

/* Calibrated: 10ms on Noah's computer */
#define WORKLOOP_ITERS 159
static float dummy = 2.7;
static inline void workloop(char* name)
{
	unsigned int i, loops;

#ifdef HAVE_LIBGSL
	loops = gsl_ran_poisson(r, (double)WORKLOOP_ITERS);
#else
	loops = WORKLOOP_ITERS;
#endif
	for (i = 0; i < loops; i++) {
		dummy *= 2.7;
	}

	printf("Node %s: Completed Workloop.\n", name);
}

struct node {
	char name[MAX_LEN];
	int id;
	pthread_t t;
	int read_fd;
	int write_fd;
	struct pipeline *pipeline;
};

struct pipeline {
	int id;
	char name[MAX_LEN];
	struct node *nodes;
	int num_nodes;
	int message_count;
	char bp_grp_name[MAX_LEN];
	char seq_grp_name[MAX_LEN];
};

struct message {
	int id;
};

struct dd {
	int pipeline_id;
	int message_id;
};

static int num_pipelines;
static struct pipeline *pipelines;

static char *config_file;
static hashtable_t *config;

static int grp_fd;
static int use_gs;

static void init_pipeline(struct pipeline *p, char *name, hashtable_t *pipeline_config)
{
	list_t *nodes, *cur;
	int i, fds[2];

	if (use_gs) {
		sprintf(p->bp_grp_name, "bp-g-%s", name);
		sprintf(p->seq_grp_name, "seq-g-%s", name);

		grp_create_group(grp_fd, p->bp_grp_name, "sdf_balanced_progress");
		grp_create_group(grp_fd, p->seq_grp_name, "sdf_rr");

		grp_group_join_group(grp_fd, p->bp_grp_name, p->seq_grp_name, p->seq_grp_name);
		grp_group_join_group(grp_fd, "balanced", p->bp_grp_name, p->bp_grp_name);
	}

	unhash_list(pipeline_config, "nodes", &nodes);
	unhash_int(pipeline_config, "messages", &p->message_count);

	p->num_nodes = 0;
	list_for_each(cur, nodes) {
		p->num_nodes++;
	}

	p->nodes = malloc(sizeof(*p->nodes)*p->num_nodes);
	strcpy(p->name, name);

	for (i = 0; i < p->num_nodes; i++) {

		p->nodes[i].id = i;
		p->nodes[i].pipeline = p;

		if (i == 0)
			sprintf(p->nodes[i].name, "node-%d-source", i);
		else if (i == p->num_nodes - 1)
			sprintf(p->nodes[i].name, "node-%d-sink", i);
		else
			sprintf(p->nodes[i].name, "node-%d", i);

		if (i == 0) {
			p->nodes[i].read_fd = -1;
			continue;
		}

		if (socketpair(AF_UNIX, SOCK_STREAM, 0, fds) < 0) {
			perror("socketpair");
		}

		p->nodes[i-1].write_fd = fds[0];
		p->nodes[i].read_fd = fds[1];

		if (i == p->num_nodes-1)
			p->nodes[i].write_fd = -1;
	}
}

static int init_pipelines(hashtable_t *config)
{
	hashtable_itr_t itr;
	hashtable_t *pipeline_config;
	int pipeline_index;

	num_pipelines = hashtable_count(config);
	if (num_pipelines == 0)
		return 0;

	pipelines = malloc(sizeof(*pipelines)*num_pipelines);

	init_iterator(&itr, config);
	pipeline_index = 0;

	do {
		char *key = hashtable_iterator_key(&itr);
		struct pipeline *p = pipelines + pipeline_index++;

		p->id = pipeline_index;
		unhash_hashtable(config, key, &pipeline_config);
		init_pipeline(p, key, pipeline_config);

	} while (hashtable_iterator_advance(&itr));

	return 0;
}

static void *node_code(void *arg)
{
	struct node *n = arg;
	struct message msg;
	char str[MAX_PIPELINE_MESSAGE];
	/* generation counter for source node */
	int msg_generated = 0;
	cpu_set_t cpu_mask;
	struct dd dd;

	memset(&dd, 0, sizeof(dd));
	dd.pipeline_id = n->pipeline->id;

	CPU_ZERO(&cpu_mask);
	CPU_SET(0, &cpu_mask);

	if (sched_setaffinity(gettid(), sizeof(cpu_mask), &cpu_mask))
		perror("sched_setaffinity");

	if (use_gs) {
		/* if source */
		if (n->read_fd == -1)
			grp_pid_join_group(grp_fd, n->pipeline->bp_grp_name, gettid(), n->name);
		else
			grp_pid_join_group(grp_fd, n->pipeline->seq_grp_name, gettid(), n->name);

		gsched_set_exclusive_control(grp_fd, gettid());
	}

	do {
		/*
		 * the source does not read() - it generates messages
		 * n->read_fd == -1 corresponds to the source node
		 */
		if (n->read_fd == -1) {

			if (msg_generated == n->pipeline->message_count)
				msg.id = -1;
			else
				msg.id = ++msg_generated;
		} else
			read(n->read_fd, &msg, sizeof(msg));

		/*
		 * do some processing on whatever data was generated/read
		 */
		workloop(n->name);

		/*
		 * the sink does not write() - it discards messages
		 * n->write_fd == -1 corresponds to the sink node
		 */
		if (n->write_fd == -1) {

			if (msg.id != -1) {
				dd.message_id = msg.id;
				DSTRM_EVENT_DATA(BP_PIPELINE, MSG_CONSUMED, 0, sizeof(dd), &dd, "pipeline_dd");
			}

		} else
			write(n->write_fd, &msg, sizeof(msg));

		/*
		 * update progress for sink and source nodes
		 */
		if (use_gs && msg.id != -1) {
			/*
			 * if this is the source its progress is updated in the
			 * pipeline's balanced progress group. the source is
			 * balanced with the rest of the pipeline
			 */
			if (n->read_fd == -1)
				gsched_set_member_param_int(grp_fd,
						n->pipeline->bp_grp_name,
						n->name, msg.id);

			/*
			 *
			 */
			else if (n->write_fd == -1) {

				gsched_set_member_param_int(grp_fd, "balanced",
						n->pipeline->bp_grp_name, msg.id);

				gsched_set_member_param_int(grp_fd,
						n->pipeline->bp_grp_name,
						n->pipeline->seq_grp_name,
						msg.id);
			}
		}

		if (msg.id == -1) {
			printf("node [%s:%d] terminating\n", n->pipeline->name, n->id);
			sprintf(str, "node [%s:%d] terminating\n", n->pipeline->name, n->id);
			break;
		}

	} while (1);

	if (use_gs) {
		gsched_clear_exclusive_control(grp_fd, gettid());

		if (n->read_fd == -1)
			grp_leave_group(grp_fd, n->pipeline->bp_grp_name, n->name);
		else
			grp_leave_group(grp_fd, n->pipeline->seq_grp_name, n->name);
	}

	if (n->write_fd != -1)
		close(n->write_fd);

	return NULL;
}

static void start_pipeline(struct pipeline *p)
{
	struct node *n;
	int i;

	for (i = 0; i < p->num_nodes; i++) {
		n = p->nodes + i;
		pthread_create(&n->t, NULL, node_code, n);
	}
}

static void start_pipelines(void)
{
	struct pipeline *p;
	int i;

	for (i = 0; i < num_pipelines; i++) {
		p = pipelines + i;
		start_pipeline(p);
	}
}

static void wait_pipelines(void)
{
	struct pipeline *p;
	int i, j;

	for (i = 0; i < num_pipelines; i++) {
		p = pipelines + i;
		for (j = 0; j < p->num_nodes; j++) {
			pthread_join(p->nodes[j].t, NULL);
		}
	}

	if (use_gs) {
		for (i = 0; i < num_pipelines; i++) {
			p = pipelines + i;
			grp_leave_group(grp_fd, p->bp_grp_name, p->seq_grp_name);
			grp_leave_group(grp_fd, "balanced", p->bp_grp_name);
			grp_destroy_group(grp_fd, p->seq_grp_name);
			grp_destroy_group(grp_fd, p->bp_grp_name);
		}
	}
}

static void display_help(char **argv) {
	printf("Usage: ./%s [-hg] -c <config file>\n", argv[0]);
	printf("Options:\n");
	printf("-c  <config-file> The configuration file that specifies the hierarchy\n");
	printf("                     of the pipelines for the experiment.\n");
  	printf("-g                Use group scheduling to run the example.\n");
       	printf("-v                Explain what is being done.\n");
      	printf("-h                display this help and exit.\n");


}

int main(int argc, char **argv)
{
	DSUI_BEGIN(&argc, &argv);

	while (1) {
		int option_index = 0;

		static struct option options[] = {
			{"config", 0, 0, 'c'},
			{"help", 0, 0, 'h'},
			{"with-gsched", 0, 0, 'g'},
			{NULL, 0, 0, 0}
		};

		char c = getopt_long(argc, argv, "c:hg", options, &option_index);

		if (c == -1)
			break;

		switch (c) {
		case 'c':
			config_file = optarg;
			break;

		case 'h':
			display_help(argv);
			exit(0);

		case 'g':
			use_gs = 1;
			break;

		default:
			display_help(argv);
			exit(1);
		}
	}

	if (config_file == NULL) {
		fprintf(stderr, "no config file specified\n");
		display_help(argv);
		exit(1);
	}

	config = parse_config(config_file);

	if (config == NULL) {
		fprintf(stderr, "failed to parse config file: %s\n", config_file);
		exit(1);
	}

	if (use_gs) {
		grp_fd = grp_open();
		if (grp_fd < 0) {
			perror("grp_open");
			exit(0);
		}
	}

	if (use_gs)
		grp_create_group(grp_fd, "balanced", "sdf_balanced_progress");

#ifdef HAVE_LIBGSL
	/* gnu scientific stuff */
	gsl_rng_env_setup();
	T = gsl_rng_default;
	r = gsl_rng_alloc(T);
#endif

	init_pipelines(config);

	start_pipelines();

	if (use_gs) {
		gsched_install_group(grp_fd, "balanced", "balanced_mem");
	}

	wait_pipelines();

	if (use_gs) {
		gsched_uninstall_group(grp_fd, "balanced_mem");
		grp_destroy_group(grp_fd, "balanced");
		close(grp_fd);
	}

	DSUI_CLEANUP();

	return 0;
}

