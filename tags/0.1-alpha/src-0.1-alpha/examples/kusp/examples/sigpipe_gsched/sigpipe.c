#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>
#define __USE_GNU
#include <sched.h>
#include <sys/mman.h>
#include <getopt.h>
#include <pthread.h>
#include <signal.h>
#include <errno.h>
#include <sys/types.h>
#include <linux/unistd.h>
#include <ccsm.h>
#include <sched_gsched.h>
#include <stdarg.h>
#include "sigpipe_dsui.h"

#define gettid() syscall(__NR_gettid)

pthread_mutex_t	 thread_count_lock    = PTHREAD_MUTEX_INITIALIZER;	/* Mutex protecting our condition variable */
pthread_cond_t	 thread_count_control = PTHREAD_COND_INITIALIZER;	/* Our condition variable */
int		 thread_count	      = 0;	                        /* Critical section data */
pthread_mutex_t	 signal_mutex	      = PTHREAD_MUTEX_INITIALIZER; 
pthread_cond_t	 signal_end	      = PTHREAD_COND_INITIALIZER;
pthread_t	*threads	      = NULL;	                        /* Thread references */
int		*tidlist	      = NULL;	                        /* Thread tids */
int		 signals_to_be_sent;	                                /* Signals to send through pipeline */
int		 pipeline_len;	                                        /* Number of stages (threads) in pipeline */
int		 stop		      = 0;
int		 use_gs		      = 0;
int		 use_ccsm	      = 0;
int		 grp_fd		      = -1;
int		 ccsm_fd	      = -1;
int              num_cpus             = 1;

static void sigint_handler(int i)
{
	stop = 1;
}

#define help_string "\
\n\nusage %s --threads=<int> --stimuli=<int> [-g] [-c] [--help]\n\n\
\t--stimuli=\tnumber of stimuli to send through pipeline\n\
\t--threads=\tnumber of threads in pipeline\n\
\t--cpus=\t\tthe number of cpus to use\n\
\t-g=\t\trun under group scheduling\n\
\t-c=\t\tcreate a ccsm set representing the computation\n\
\t--help\t\tthis menu\n\n"

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
		  signals_to_be_sent = atoi(optarg);
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
	
	if (signals_to_be_sent <= 0) {
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

static void *thread_code (void *arg)
{
	int id = (int)arg, numsigs, sigcnt=0;
	char name[12];
	
	/* Record the start of execution of this thread */
	DSTRM_EVENT(THREAD_TEST, THREAD_START, id);
	
	sigset_t newset;
	pthread_t *next_thread;
	
	/* Save this threads pid */
	tidlist[id] = gettid();
	
	/* Set a link to the next thread */
	next_thread = (id == (pipeline_len - 1)) ? NULL : &threads[id+1];
	
	/* Create a name to be used for this thread */
	memset(name, 0, sizeof(name));
	sprintf(name, "thread-%d", id);
	
	/* If we are supposed to identify the components of the application then
	 * create a component that represents this thread and add the component
	 * to the set that represents the pipeline.
	 */
	if(use_ccsm) {
		printf("Creating component for T-%d\n", id);
		ccsm_create_component_self(ccsm_fd, name);
		printf("Adding T-%d to the set\n", id);
		ccsm_add_member(ccsm_fd, "pipeline_group", name);
	}
	
	/* If we are supposed to use group scheduling then we need to add this
	 * thread to group scheduling.
	 */
	if(use_gs) {
		/* If we are using ccsm then we can name the thread. */		
		if(use_ccsm) {
			/* Add the thread to group scheduling by name. */
			printf("Adding T-%d to the group by name\n", id);
			grp_name_join_group(grp_fd, "pipeline_group", name, 0);
		} else {
			/* Add the thread to group scheduling using its pid */
			printf("adding T-%d to the group by pid\n", id);
			grp_pid_join_group(grp_fd, "pipeline_group", tidlist[id], name);
		}
		
		// Lower priority is better
		gsched_set_member_param_int(grp_fd, "pipeline_group", name, pipeline_len - id);
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
		gsched_set_exclusive_control(grp_fd, tidlist[id]);
	}
	
	printf("T-%d running\n",id);
	
	
	/* Until we receive the kill signal... */
	while (1) {
		sigemptyset(&newset);
		sigaddset(&newset, SIGUSR1);
		sigaddset(&newset, SIGUSR2);
		sigwait (&newset, &numsigs);
		
		/* If signal SIGUSR1 is recieved, kill the thread */
		if (numsigs == SIGUSR2) break;
		
		/* If any other signal received, ignore, but notify user */
		if (numsigs != SIGUSR1) printf("Bad Signal: %d\n", numsigs);
		
		sigcnt++;
		
		/*
		 * Generate a unique event tag based on thread ID
		 * and signal sequence number. Note that we are using
		 * the (thread ID + 1) as the unique value for this thread
		 * in the tag value. The ID value is used as the index
		 * into the tid[] array which keeps tracks of only the
		 * child thread. However, we also need the parent thread
		 * to have an ID since it generates each signal representing
		 * messages moving through the pipeline. Since we want the
		 * parent thread to have location value 0, we use the index
		 * + 1 for each of the threads.
		 *
		 * In this case, the tag value for each event must encode both
		 * the pipeline stage location value and the signal sequence
		 * number. We chose the convention of using the top five bits
		 * of the tag value for the pipeline stage location and the
		 * bottom 27 bits for the message sequence number.
		 */
		unsigned int unique_id = id+1;
		unique_id <<= 27;
		unique_id |= sigcnt;
		
		/* Generate a signal recieved event */
		DSTRM_EVENT(GAP_TEST, SIG_RCVD, unique_id);
		
		/*
		 * Every 1000 signals we print a message to the user,
		 * so that they know progress is being made
		 */
		if (sigcnt % 1000 == 0)
			printf("T-%d thread [%d] received %d signals\n",
			       id, tidlist[id], sigcnt);
		
		if (!next_thread) {
			
			/*
			 * Record he exiting of signal from the
			 * pipeline. The signal has not actually
			 * exited to some other thread, but as
			 * this is the end of the pipeline, this
			 * is the last place the signal will be
			 * received.
			 */
			DSTRM_EVENT(PIPE_TEST, PIPE_END, sigcnt);
			
			/* Notify the sender that the pipeline is ready to receive another signal */
			pthread_mutex_lock(&signal_mutex);
			pthread_cond_signal(&signal_end);
			pthread_mutex_unlock(&signal_mutex);
			
			continue;
		}
		
		/* Generate a signal sent event */
		DSTRM_EVENT(GAP_TEST, SIG_SENT, unique_id);
		
		pthread_kill(*next_thread, SIGUSR1);
	}
  
	/* Pass on the kill signal to the next thread in the pipeline */
	if (next_thread) pthread_kill(*next_thread, SIGUSR2);
	
	/* Record the end of exection of this thread */
	DSTRM_EVENT(THREAD_TEST, THREAD_END, id);
	
	printf("T-%d exiting\n", id);
	return NULL;
}

int main(int argc, char **argv)
{
	int i;
	sigset_t newset;
	cpu_set_t cpuset;
	
	/* Open DSUI */
	DSUI_BEGIN(&argc, &argv);
	
	/* Record the start of main() */
	DSTRM_EVENT(FUNC_MAIN, IN_MAIN_FUNC, 0);
	
	/* Process incoming arguments to setup experiment */
	process_options(argc, argv);

	/* If we are supposed to name the components of this computation
	 * then we create a named set to contain the components.
	 */
	if(use_ccsm) {
		ccsm_fd = ccsm_open();
		if (ccsm_fd < 0) {
			perror("ccsm_fd");
			return 1;
		}
		
		if (ccsm_create_set(ccsm_fd, "pipeline_group", 0)) {
			perror("create set");
			return 1;
		}
	} 
	
	/* If we are using group scheduling then create a group
	 * to contain the threads of this application.
	 */
	if(use_gs) {
		grp_fd = grp_open();
		if (grp_fd < 0) {
			perror("grp_fd");
			return 1;
		}

		if (grp_create_group(grp_fd, "pipeline_group", "sdf_seq")) {
			perror("create group");
			return 1;
		}
		
		/* This could be done after all of the threads have been
		 * added to the group.
		 */
		if(gsched_install_group(grp_fd, "pipeline_group", "pipeline_group_mem")) {
			perror("install group");
			return 1;
		}
	}
	
	/*
	 * Set up signal masking. We do this to prevent
	 * any random system signals from interrupting
	 * our experiment
	 */
	sigemptyset(&newset);
	sigaddset(&newset, SIGUSR1);
	sigaddset(&newset, SIGUSR2);
	sigprocmask (SIG_BLOCK, &newset, NULL);
	
	signal(SIGINT, sigint_handler);
	signal(SIGTERM, sigint_handler);
	
	
	/* Allocate memory to hold references to pthreads */
	threads = malloc(sizeof(pthread_t) * pipeline_len);
	if (!threads) {
		perror("pthread malloc");
		exit(1);
	}
	
	/* Allocate memory to hold TIDs for pthreads */
	tidlist = malloc(sizeof(int) * pipeline_len);
	if (!tidlist) {
		perror("tidlist malloc");
		exit(1);
	}
	
	/* Create the threads using the thread code declared above */
	for (i = 0; i < pipeline_len; i++) {
		if (pthread_create (&threads[i], NULL, thread_code, (void *) i)) {
			fprintf(stderr, "Failed on pthread_create. %d\n", errno);
			exit(1);
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
	
	/* While there are still signals to be sent... */
	if (signals_to_be_sent) {
		int sigs = 0, i = 0, cpu_pipeline_stage = 0, cpu = 0;
		
		printf("Sending first signal to T-%d [%d]\n", 0, tidlist[0]);
		for(i = 0;i < signals_to_be_sent;++i) {
      
			/*
			 * Mark when a signal is first sent. Note that
			 * we mark this point twice, with two different
			 * events. Each event supports a different set
			 * of information we are gathering
			 */
			unsigned int pipeline_stage = 0;
			pipeline_stage <<= 27;
			pipeline_stage |= sigs + 1;
			DSTRM_EVENT(GAP_TEST, SIG_SENT, pipeline_stage);
			
			DSTRM_EVENT(PIPE_TEST, PIPE_START, sigs + 1);
			
			// We need to lock the signal mutex here becuase
			// rarely a context switch will happen when we pthread_kill
			// and we wont get to wait on the signal condition before it gets signaled.
			pthread_mutex_lock(&signal_mutex);
			
			/* Send the signal to the first thread in the pipeline */
			pthread_kill(threads[0], SIGUSR1);
			
			/*
			 * Wait until the signal reaches the end
			 * of the pipeline
			 */
			pthread_cond_wait(&signal_end, &signal_mutex);
			pthread_mutex_unlock(&signal_mutex);
			
			sigs++;
			
			/* Every 100 signals we switch the cpu of a thread */
			if (sigs % 100 == 0) {
				cpu_pipeline_stage = (cpu_pipeline_stage + 1) % pipeline_len;
				cpu = (cpu + 1) % num_cpus;
				
				CPU_ZERO(&cpuset);
				CPU_SET(cpu, &cpuset);
				
				sched_setaffinity(tidlist[cpu_pipeline_stage], sizeof(cpu_set_t), &cpuset);
			}
		} 
		
		printf("Received all signals from last thread in pipeline\n");
		
		/* Record tid of each thread that was used... */
		for (i = 0; i < pipeline_len; i++){
			DSTRM_EVENT(THREAD, THREAD_ID, tidlist[i]);
		}
		/* ...including the main thread! */
		DSTRM_EVENT(THREAD, THREAD_ID, gettid());
	}
	
	/* Send a kill signal which terminates each pipeline stage */
	pthread_kill(threads[0], SIGUSR2);
	
	/* Wait for each thread to terminate. */
	for (i = 0; i < pipeline_len; i++)
		pthread_join (threads[i], NULL);
	
	/* Cleanup the group we created to represent the pipeline */
	if (use_gs) {
		gsched_uninstall_group(grp_fd, "pipeline_group_mem");
		if (grp_destroy_group(grp_fd, "pipeline_group")) {
			perror("destroy pipeline group");
		}
		close(grp_fd);
		
	}
	
	/* Cleanup the set we created to represent the pipeline */
	if(use_ccsm) {
		if (ccsm_destroy_set(ccsm_fd, "pipeline_group")) {
			perror("destroy pipeline set");
		}
		
		close(ccsm_fd);    
	}
	
	/* Record the end of main() */
	DSTRM_EVENT(FUNC_MAIN, IN_MAIN_FUNC, 0);
	
	/* Exit DSUI */
	DSUI_CLEANUP();
	
	return 0;
}
