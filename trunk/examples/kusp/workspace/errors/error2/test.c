#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>

#include <sched.h>
#include <pthread.h>
#include <errno.h>
#include <sched_gsched.h>
#include <time.h>
#include <linux/unistd.h>

#include "test_dsui.h"

#include <sys/types.h>


//#define gettid() syscall(__NR_gettid)

#define gettid getpid

int grp_fd = -1;

const int NUM_LOOPS = 500000;
char const* const safety_group = "safety";
char const* const safety_mem = "safety_mem";

void* looper(void* arg)
{
		
	int tid = gettid();
	double avar = 0;
	double avar2 = 48484;
	int i = 0;

	/* Add the thread to group scheduling using its pid */
	printf("adding looper %d to the group\n", tid);
	grp_pid_join_group(grp_fd, safety_group, tid, "looper");				
	gsched_set_exclusive_control(grp_fd, tid);

	for(i = 0;i < NUM_LOOPS;++i) {

		/* Nonsense calculations */
		avar2 = avar * 0.48439;
		avar = 9 * avar2 + (38383 + avar) * 1.5;
	}

	avar = avar + avar2;

       	DSTRM_EVENT(LOOPER, EXIT, gettid());
	return NULL;
}

int main(int argc, char** argv)
{
	pthread_t thread;
	int tid = gettid();
	
	DSUI_BEGIN(&argc, &argv);

       	DSTRM_EVENT(TEST, START, gettid());
	
	grp_fd = grp_open();
	if (grp_fd < 0) {
		perror("grp_fd");
		return 1;
	}

	if (grp_create_group(grp_fd, safety_group, "sdf_rr")) {
		perror("create group");
		return 1;
	}
	
	if (gsched_install_group(grp_fd, safety_group, safety_mem)) {
		perror("install group");
		return 1;
	}

	printf("(%d) Starting loop test...\n", tid);
#if 0
	if (pthread_create(&thread, NULL, looper, NULL)) {
		fprintf(stderr, "failed creating thread");
		return 1;
	}


	pthread_join(thread, NULL);

	DSTRM_EVENT(TEST, JOIN, gettid());
#endif

	looper(NULL);

	printf("Loop test complete.\n");

	/* When commented out, a kernel panic occurs. */
	/* When not commented out, a kernel panic does not occur. */
#if 0
	gsched_clear_exclusive_control(grp_fd, tid);
#endif

#if 1
	/* Cleanup the group we created to represent the pipeline */
	if (gsched_uninstall_group(grp_fd, safety_mem)) {
		perror("uninstall group");
	}
#endif

	printf("before close\n");
       	close(grp_fd);
	printf("after close\n");

	printf("before dsui cleanup\n");

	DSUI_CLEANUP();

	printf("after dsui cleanup\n");

	printf("exiting\n");
	return 0;
}
