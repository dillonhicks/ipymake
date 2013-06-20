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
#include <ccsm.h>

#include "sockpipe_dsui.h"

/* Default size of the socket message buffer. */
#define BUFFER_SIZE 100
/* Number of times to execute the workloop for a thread.*/
#define WORKLOOP_INTERVAL 100000
/* Command line instructions */
#define help_string "\
\n\nusage %s --threads=<int> --stimuli=<int> [-g] [-c] [--help]\n\n\
\t--stimuli=\tnumber of stimuli to send through pipeline\n\
\t--threads=\tnumber of threads in pipeline\n\
\t--cpus=\t\tthe number of cpus to use\n\
\t-g=\t\trun under group scheduling\n\
\t-c=\t\tcreate a ccsm set representing the computation\n\
\t--help\t\tthis menu\n\n"

/* Routine to fetch the thread idea of pthread */
#define gettid() syscall(__NR_gettid)

const char*      message              = "This is a message.";
pthread_mutex_t	 thread_count_lock    = PTHREAD_MUTEX_INITIALIZER;	/* Mutex protecting our condition variable */
pthread_cond_t	 thread_count_control = PTHREAD_COND_INITIALIZER;	/* Our condition variable */
int		 thread_count	      = 0;	                        /* Critical section data */
pthread_t	*threads	      = NULL;	                        /* Thread references */
int		*tidlist	      = NULL;	                        /* Thread tids */
int		 pipeline_len;	                                        /* Number of stages (threads) in pipeline */
int              stimuli              = 0;
int		 use_gs		      = 0;
int		 use_ccsm	      = 0;
int		 grp_fd		      = -1;
int		 ccsm_fd	      = -1;
int              num_cpus             = 1;



/* File Descriptor Structure */
struct thread_info
{
	int order;
	int in_fd;
	int out_fd;
};

void display_help(char **argv)
{
	printf(help_string, argv[0]);
}

/* This subroutine processes the command line options */
void process_options (int argc, char *argv[])
{
	int error = 0;
	
	for (;;) {
		int option_index = 0;
		
		static struct option long_options[] = {
			{"threads",          required_argument, NULL, 't'},
			{"stimuli",          required_argument, NULL, 's'},
			{"cpus",             optional_argument, NULL, 'n'},
			{"help",             no_argument,       NULL, 'h'},
			{NULL, 0, NULL, 0}
		};
		
		/*
		 * c contains the 4th element in the lists above corresponding to
		 * the long argument the user used.
		 */
		int c = getopt_long(argc, argv, "g::c::t:s:", long_options, &option_index);
		
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
			
		case 's':
			stimuli = atoi(optarg);
			break;
			
		case 't':
			pipeline_len = atoi(optarg);
			break;
		case 'g':
			use_gs = 1;
			break;
		case 'c':
			use_ccsm = 1;
			break;
		case 'n':
			num_cpus = atoi(optarg);
		case 'h':
			error = 1;
			break;
		}
	}
	
	if (stimuli <= 0) {
		printf("\nError: signals to be sent must be > 0");
		error = 1;
	}
	
	if (pipeline_len <= 0) {
		printf("\nError: pipeline length must be > 0");
		error = 1;
	}
	
	if (num_cpus <= 0) {
		printf("\nError: the number of cpus to use must be > 0");
	}
	
	if (error) {
		display_help(argv);
		exit(1);
	}
}

void* thread_function_run(void* arg)
{
	struct thread_info*	info = (struct thread_info*)arg; // Information about this thread.
	char			buffer[BUFFER_SIZE]; // Buffer to store a message in.
	char			name[15]; // The name of the thread
	int			num_loops;
	int			count;
	int			length;
	int			tid; // Store the thread id
	int                     id;
	unsigned int		unique_id;
	
	tid = gettid();
	id = info->order;
	
	/* Create a name to be used for this thread */
	memset(name, 0, sizeof(name));
	sprintf(name, "thread-%d", id);
	
	if(use_ccsm) {
		printf("Creating component for T-%d\n", id);
		ccsm_create_component_self(ccsm_fd, name);
		printf("Adding T-%d(%d) to the set\n", id, tid);
		ccsm_add_member(ccsm_fd, "socket_pipeline", name);
	}
	
	if(use_gs) {
		if(use_ccsm) {
			printf("Adding T-%d(%d) to the group by name\n", id, tid);
			grp_name_join_group(grp_fd, "socket_pipeline", name, 0);
		} else {
			printf("adding T-%d(%d) to the group by pid\n", id, tid);
			grp_pid_join_group(grp_fd, "socket_pipeline", tid, name);
		}
		
		// Lower priority is better
		gsched_set_member_param_int(grp_fd, "socket_pipeline", name, pipeline_len - id);
	}
	
	/* Block until all threads have started. 
	 * If this is the last thread to start then notify
	 * everyone taht the pipeline is ready to go.
	 */
	pthread_mutex_lock(&thread_count_lock);
	++thread_count;
	if(thread_count < pipeline_len) {
		pthread_cond_wait(&thread_count_control, &thread_count_lock);
	} else {
		pthread_cond_broadcast(&thread_count_control);
	}
	pthread_mutex_unlock(&thread_count_lock);
	
	if(use_gs) {
		gsched_set_exclusive_control(grp_fd, tid);
	}
	
	count = stimuli;
	
	while(count > 0) {
		double phi = 1.61803;
		double thread_progress = 0.0;
		length = recv(info->in_fd, buffer, BUFFER_SIZE, 0);
		
		unique_id = info->order + 1;
		unique_id <<= 27;
		unique_id |= count;
		
		DSTRM_EVENT(GAP_TEST, SIG_RCVD, unique_id);
		
		if (count % 100 == 0)
			printf("T-%d thread [%d] has %d messages to go\n",
			       info->order, tid, count);
		
		for (num_loops = 0; num_loops < WORKLOOP_INTERVAL; num_loops++) {
			phi *= phi;
			
			thread_progress = floor(num_loops / WORKLOOP_INTERVAL);
		}
		
		if(-1 == info->out_fd) {
			DSTRM_EVENT(PIPE_TEST, PIPE_END, count);
		} else {
			DSTRM_EVENT(GAP_TEST, SIG_SENT, unique_id);
			send(info->out_fd, buffer,length, 0);
		}
		
		--count;
	}
	
	return NULL;
}


int main(int argc, char** argv)
{
	pthread_t*		thread_ids; // pthread ids of the threads in the pipeline
	struct thread_info*	tinfo; // Hold information about pipeline threads.
	int			fds[2]; // Return values for socketpair
	int			out_fd; // Receiving fd of the pipeline
	int			count;
	int			ret;
	int			i;
	unsigned int		first;
	
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
	
	if(use_ccsm) {
		ccsm_fd = ccsm_open();
		if (ccsm_fd < 0) {
			perror("ccsm_fd");
			return 1;
		}
		
		if (ccsm_create_set(ccsm_fd, "socket_pipeline", 0)) {
			perror("create set");
			return 1;
		}
	} 
	
	/* Create storage for thread ids. */
	thread_ids = malloc(sizeof(pthread_t) * pipeline_len);
	/* Create storage for thread parameters. */
	tinfo = malloc(sizeof(struct thread_info) * pipeline_len);
	
	if (socketpair(AF_UNIX, SOCK_DGRAM, 0, fds) < 0) {
		perror("socketpair");
		exit(1);
	}
	
	out_fd = fds[0];
	
	tinfo[0].in_fd = fds[1];
	tinfo[0].order = 0;
	
	/* Create the sockets.*/
	for (i = 1;i < pipeline_len;++i) {
		if (socketpair(AF_UNIX, SOCK_DGRAM, 0, fds) < 0) {
			perror("socketpair");
			exit(1);
		}
		
		tinfo[i - 1].out_fd = fds[0];
		tinfo[i].in_fd = fds[1];
		
		tinfo[i].order = i;
	}
	
	tinfo[pipeline_len - 1].out_fd = -1;
	
	printf("Starting threads...\n");
	
	/* Create the threads. */
	for (i = 0; i < pipeline_len; ++i) {
		if (pthread_create(&thread_ids[i], NULL, &thread_function_run, (void *)&tinfo[i])) {
			fprintf(stderr, "failed creating thread");
		}
	}
	
	printf("Created pipeline of %d threads\n", pipeline_len);
	
	/* Wait for the pipeline threads to start. */
	pthread_mutex_lock(&thread_count_lock);
	if(thread_count < pipeline_len) {
		pthread_cond_wait(&thread_count_control, &thread_count_lock);
	} else {
		pthread_cond_broadcast(&thread_count_control);
	}
	pthread_mutex_unlock(&thread_count_lock);
	
	printf("All threads started\n");
	
	count = stimuli;
	
	while (count > 0) {
		first = 0;
		first |= count;
		DSTRM_EVENT(GAP_TEST, SIG_SENT, first);
		
		DSTRM_EVENT(PIPE_TEST, PIPE_START, count);
				
		/* Send the message to the first thread in the pipeline */
		ret = send(out_fd, message, strlen(message) + 1, 0);
				
		--count;
	}
	
	close(out_fd);
	
	/* Wait for threads. */
	for (i = 0; i < pipeline_len; ++i) {
		pthread_join(thread_ids[i], NULL);
		close(tinfo[i].in_fd);
		close(tinfo[i].out_fd);
	}
	
	printf("Pipeline complete.\n");
	
	if (use_gs) {
		gsched_uninstall_group(grp_fd, "socket_pipeline_mem");
		if (grp_destroy_group(grp_fd, "socket_pipeline")) {
			perror("destroy pipeline group");
		}
		close(grp_fd);
	}

	if(use_ccsm) {
		if (ccsm_destroy_set(ccsm_fd, "socket_pipeline")) {
			perror("destroy pipeline set");
		}
		
		close(ccsm_fd);    
	}
  
	free(tinfo);
	free(thread_ids);
	
	DSUI_CLEANUP();
	
	return 0;
}
