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

#include <sched_gsched.h>
#include <ccsm.h>
#include "multithreads_dsui.h"

#define NUMBER_OF_THREADS 4
#define gettid() syscall(__NR_gettid)

static int pipeline_len;
int ccsm_fd;
int grp_fd;

#define help_string "\
\n\nusage %s --threads=<int> [--without-rt] [--help]\n\n\
\t--threads=\tnumber of threads in pipeline\n\
\t--help\t\tthis menu\n\n"

void display_help(char **argv)
{
	printf(help_string, argv[0]);
}

/* process command line options */
void process_options (int argc, char *argv[])
{
	int error = 0;
	
	for (;;) {
		int option_index = 0;

		static struct option long_options[] = {
			{"threads",          required_argument, NULL, 't'},
			{"help",             no_argument,       NULL, 'h'},
			{NULL, 0, NULL, 0}
		};

		/*
		 * c contains the 4th element in the lists above corresponding to
		 * the long argument the user used.
		 */
		int c = getopt_long(argc, argv, "int:c:", long_options, &option_index);

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
			pipeline_len = atoi(optarg);
			break;

		case 'h':
			error = 1;
			break;
		}				
	}

	if (pipeline_len <= 0) {
		printf("\nerror: pipeline length must be > 0");
		error = 1;
	}

	if (error) {
		display_help(argv);
		exit(1);
	}
}

void *thread_function_run(void *arg){
	char name[12];
	int id = (int)arg;

	DSTRM_EVENT(MULTITHREAD, THREAD_START, gettid());

	ccsm_create_component_self(ccsm_fd, name);

	sleep(5);

	DSTRM_EVENT(MULTITHREAD, THREAD_STOP, gettid());
}

int main(int argc, char **argv){
	pthread_t *threads;
	int i=0;
	void *ret;
	
	DSUI_BEGIN(&argc, &argv);
	
	process_options(argc, argv);
	
	DSTRM_EVENT(FUNC_MAIN, IN_MAIN_FUNC, 0);

	threads = malloc(sizeof(pthread_t) * pipeline_len);
	if (!threads){
		fprintf(stderr, "can't initialise threads\n");
		exit(1);
	}

	printf("Creating the required set of threads.....\n");
	for(i=0;i<pipeline_len;i++){
		if (pthread_create(&threads[i],NULL,&thread_function_run, (void *)i)){
		       	fprintf(stderr, "failed creating thread");
        		exit(1);
        	}
	}
	
	for(i=0;i<pipeline_len;i++){
		pthread_join(threads[i], &ret);
	}

	DSTRM_EVENT(FUNC_MAIN, IN_MAIN_FUNC, 0);

	DSUI_CLEANUP();
	
	return 0;
}

