#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>

#include <sys/socket.h>
#define __USE_GNU
#include <math.h>
#include <sched.h>
#include <sys/mman.h>
#include <getopt.h>
#include <pthread.h>
#include <signal.h>
#include <errno.h>
#include <sys/types.h>
#include <linux/unistd.h>

#include <sched_gsched.h>
#include "socketpipe_gsched_dsui.h"

/* Default size of the socket message buffer. */
#define BUFFER_SIZE 100
/* The default number of threads is 4. */
#define NUMBER_OF_THREADS 4
/* Number of times to execute the workloop for a thread.*/
#define WORKLOOP_INTERVAL 10000
/* Command line instructions */
#define help_string "\
\n\nusage %s --threads=<int> --stimuli=<int> [--help]\n\n\
\t--stimuli=\tnumber of stimuli to send through pipeline\n\
\t--threads=\tnumber of threads in pipeline\n\
\t--with-gs\tuse group scheduling\n\
\t--help\t\tthis menu\n\n"
/* Routine to fetch the thread idea of pthread */
#define gettid() syscall(__NR_gettid)

const char* message = "This is a message.";

static int  num_threads;
static int  num_stimuli;
int         grp_fd;
int         use_gs = 1;


/* File Descriptor Structure */
struct fds
{
	int order;
	int in_fd;
	int out_fd;
};

void display_help(char **argv)
{
	printf(help_string, argv[0]);
}


/*
 * This is a good general ccsm example. It illustrates the creation of a
 * multi-member set and multiple component sets that clean themselves up during
 * task exit.
 *
 * Variations might include using the explicit set cleanup functions to ensure
 * they also work properly, or to force strange situtions which the ccsm
 * internals need to be able to handle safely.
 *
 * For example, you might create a "main" set, add all of the component sets as
 * members, and then destroy "main" prior to the exit of the component sets. The
 * component sets should remain, while the "main" set safely cleans itself up.
 *
 */
/* process command line options */
void process_options (int argc, char *argv[])
{
	int c;
	int error;
	int option_index;

	error = 0;

	for (;;) {
		option_index = 0;

		static struct option long_options[] = {
			{"threads",          required_argument, NULL, 't'},
			{"stimuli",          required_argument, NULL, 's'},
			{"with-gs",          no_argument,       NULL, 'r'},
			{"help",             no_argument,       NULL, 'h'},
			{NULL, 0, NULL, 0}
		};

		c = getopt_long(argc, argv, "int:c:", long_options, &option_index);

		if (c == -1)
			break;
		switch (c) {
		case 0:
			switch (option_index) {
			case 0:
				display_help(argv);
				exit(0);
				break;
			}
			break;

		case 't':
			num_threads = atoi(optarg);
			break;

		case 's':
		  num_stimuli =  atoi(optarg);
		  break;
		
		case 'r':
                        use_gs = 1;
			break;

		case 'h':
			error = 1;
			break;
		}
	}

	if (num_threads <= 0) {
		printf("\nerror: the number of threads must be > 0");
		error = 1;
	}

	if (error) {
		display_help(argv);
		exit(1);
	}
}

void *thread_function_run(void *arg)
{
	struct fds* socket_fds = (struct fds*)arg;

	char        buffer[BUFFER_SIZE];
	int         num_loops;
	int         count;
	int         ret;
	unsigned int unique_id;
	char name[50];

	if (use_gs) {
		memset(name, 0, sizeof(name));
		sprintf(name, "thread-%d", socket_fds->order);
		printf("adding task to group with name %s\n", name);
		grp_pid_join_group(grp_fd, "socket_pipeline", gettid(), name);
		//		gsched_set_member_param_int(grp_fd, "socket_pipeline", name, socket_fds->order);
       		gsched_set_exclusive_control(grp_fd, gettid());
	}

	count = num_stimuli;

	while(count > 0) {
		double phi = 1.61803;
		double thread_progress = 0.0;
		ret = recv(socket_fds->in_fd, buffer, BUFFER_SIZE, 0);

		unique_id = socket_fds->order;
		unique_id <<= 27;
		unique_id |= count;

		DSTRM_EVENT(GAP_TEST, SIG_RCVD, unique_id);

		for (num_loops = 0; num_loops < WORKLOOP_INTERVAL; num_loops++) {
			phi *= phi;
	    
			thread_progress = floor(num_loops / WORKLOOP_INTERVAL);
	    
			if ( (int)thread_progress % 10 == 0) {
//				printf("thread-%d Progress: %f\n", id, thread_progress);
			}
		}
		
		if(-1 == socket_fds->out_fd) {
                  DSTRM_EVENT(PIPE_TEST, PIPE_END, count);
		} else {
                  DSTRM_EVENT(GAP_TEST, SIG_SENT, unique_id);
		  send(socket_fds->out_fd, buffer, ret, 0);
		}

		--count;
	}

	if (use_gs) {
	  printf("clearing exclusive control for thread-%d\n", socket_fds->order);
	  gsched_clear_exclusive_control(grp_fd, gettid());
	}

	printf("exiting thread-%d\n", socket_fds->order);
	return NULL;
}


int main(int argc, char** argv)
{
	pthread_t*  thread_ids;
	struct fds* thread_fds;
	void*       thread_ret;
	int         fds[2];
	int         out_fd;
	int         count;
	int         ret;
	int         i;
	unsigned int first;

	DSUI_BEGIN(&argc, &argv);

	process_options(argc, argv);

	if (use_gs) {
		grp_fd = grp_open();
		if (grp_fd < 0) {
			perror("grp_fd");
			return 1;
		}
		if (grp_create_group(grp_fd, "socket_pipeline", "sdf_seq")) {
			perror("create group");
			return 1;
		}
		gsched_install_group(grp_fd, "socket_pipeline", "socket_pipeline_mem");
	}

	/* Create storage for thread ids. */
	thread_ids = malloc(sizeof(pthread_t) * num_threads);
	/* Create storage for thread fds. */
	thread_fds = malloc(sizeof(struct fds) * num_threads);

	if (socketpair(AF_UNIX, SOCK_DGRAM, 0, fds) < 0) {
		perror("socketpair");
		exit(1);
	}

	out_fd = fds[0];

	thread_fds[0].in_fd = fds[1];
        thread_fds[0].order = 1;

	/* Create the sockets.*/
	for (i = 1;i < num_threads;++i) {
		if (socketpair(AF_UNIX, SOCK_DGRAM, 0, fds) < 0) {
			perror("socketpair");
			exit(1);
		}

		thread_fds[i - 1].out_fd = fds[0];
		thread_fds[i].in_fd = fds[1];

		// Need to reserve 0 for this thread for DSUI.                                                              
		thread_fds[i].order = i + 1;
	}

	thread_fds[num_threads - 1].out_fd = -1;

	printf("Starting threads...\n");

	/* Create the threads. */
	for (i = 0; i < num_threads; ++i) {
		if (pthread_create(&thread_ids[i], NULL, &thread_function_run, (void *)&thread_fds[i])) {
			fprintf(stderr, "failed creating thread");
		}
	}
	
	count = num_stimuli;

	if(use_gs) {
	  grp_pid_join_group(grp_fd, "socket_pipeline", gettid(), "thread-0");
	  gsched_set_member_param_int(grp_fd, "socket_pipeline", "thread-0", 0);
	  gsched_set_exclusive_control(grp_fd, gettid());
	}

	while (count > 0) {
	  first = 0;
	  first |= count;
	  DSTRM_EVENT(GAP_TEST, SIG_SENT, first);
	  
	  DSTRM_EVENT(PIPE_TEST, PIPE_START, count);
	 
	  ret = send(out_fd, message, strlen(message) + 1, 0);
	  --count;
	}

	close(out_fd);

	if(use_gs) {
	  //gsched_clear_exclusive_control(grp_fd, gettid());
	  printf("thread-0 leaving the group\n");
	  grp_leave_group(grp_fd, "socket_pipeline", "thread-0");
	}

	/* Wait for threads. */
	for (i = 0; i < num_threads; ++i) {
	  printf("Trying to join with thread-%d\n", thread_fds[i].order);
		pthread_join(thread_ids[i], &thread_ret);
		close(thread_fds[i].in_fd);
		close(thread_fds[i].out_fd);
	}

	printf("Pipeline complete.\n");

	if (use_gs) {
	  printf("uninstalling the group\n");
	  gsched_uninstall_group(grp_fd, "socket_pipeline_mem");
	  printf("destroy the group\n");
	  if (grp_destroy_group(grp_fd, "socket_pipeline")) {
	    perror("destroy pipeline group");
	  }
	  printf("close grp_fd\n");
	  close(grp_fd);
	}
	
	printf("free thread_fds\n");
	free(thread_fds);
	printf("free thread_ids\n");
	free(thread_ids);

	printf("dsui cleanup\n");
	DSUI_CLEANUP();

	printf("exiting\n");
	return 0;
}
