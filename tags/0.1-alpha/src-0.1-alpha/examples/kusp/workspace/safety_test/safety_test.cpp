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

#include "safety_test_dsui.h"

#define gettid() syscall(__NR_gettid)

int grp_fd = -1;

const int NUM_LOOPER_LOOPS = 10000000;
const int NUM_SLEEPER_LOOPS = 5000;
char const* const safety_group = "safety";
char const* const safety_mem = "safety_mem";
char const* const test_group = "safety_test";
char const* const test_mem = "safety_test_mem";

void* light_sleeper(void* arg)
{
	char name[15]; // The name of the thread
	int tid	= gettid();
	timespec sleep_time = { 0, 1 }; // 1 nanosecond, like that will happen

	/* Create a name to be used for this thread */
	memset(name, 0, sizeof(name));
	sprintf(name, "sleeper-%d", tid);

	/* Add the thread to group scheduling using its pid */
	printf("adding light sleeper %d to the group\n", tid);
	grp_pid_join_group(grp_fd, test_group, tid, name);		
		
	gsched_set_exclusive_control(grp_fd, tid);

	double avar = 0;
	double avar2 = 48484;	
	for(int i = 0;i < NUM_SLEEPER_LOOPS;++i) {
		/* Nonsense calculations */
		avar2 = avar * 0.48439;
		avar = 9 * avar2 + (38383 + avar) * 1.5;
		
		if (rand() % 100 < 5) {
			if (nanosleep(&sleep_time, NULL)) {
				perror("nanosleep");
				exit(1);
			}
		}
	}

	gsched_clear_exclusive_control(grp_fd, tid);

	grp_leave_group(grp_fd, test_group, name);
	return NULL;
}

void* looper(void* arg)
{
	int tid = gettid();

	/* Add the thread to group scheduling using its pid */
	printf("adding looper %d to the group\n", tid);
	grp_pid_join_group(grp_fd, test_group, tid, "looper");		
		
	gsched_set_exclusive_control(grp_fd, tid);

	double avar = 0.12342;
	double avar2 = 0.43483;
	for(int i = 0;i < NUM_LOOPER_LOOPS;++i) {
		avar = (avar2 + 0.29393) * 0.999393;
		avar2 = avar2 * 0.991112;
	}
	
	gsched_clear_exclusive_control(grp_fd, tid);

	grp_leave_group(grp_fd, test_group, "looper");
	return NULL;
}

int main(int argc, char** argv)
{
	const int THREADS = 4;
	pthread_t thread_ids[THREADS]; 

	srand(0);
	
	DSUI_BEGIN(&argc, &argv);
	
	grp_fd = grp_open();
	if (grp_fd < 0) {
		perror("grp_fd");
		return 1;
	}

	if (grp_create_group(grp_fd, safety_group, "sdf_safe")) {
		perror("create group");
		return 1;
	}

	if (grp_create_group(grp_fd, test_group, "sdf_seq")) {
		perror("create group");
		return 1;
	}

	if (grp_group_join_group(grp_fd, safety_group, test_group, test_mem)) {
		perror("group join group");
		return 1;
	}
	
	if (gsched_install_group(grp_fd, safety_group, safety_mem)) {
		perror("install group");
		return 1;
	}

	printf("Starting timeout test...\n");

	DSTRM_EVENT(TEST, TIMEOUT_START, 0);

	if (pthread_create(&thread_ids[0], NULL, looper, NULL)) {
		fprintf(stderr, "failed creating thread");
		return 1;
	}

	pthread_join(thread_ids[0], NULL);

	DSTRM_EVENT(TEST, TIMEOUT_END, 0);

	printf("Timeout test complete.\n");
		
	printf("Starting force linux test...\n");

	DSTRM_EVENT(TEST, LINUX_START, 0);

 	/* Create the threads. */
	for (int i = 0; i < THREADS; ++i) {
		if (pthread_create(&thread_ids[i], NULL, light_sleeper, NULL)) {
			fprintf(stderr, "failed creating thread");
			return 1;
		}
	}
	
	printf("Created %d threads\n", THREADS);
	
	/* Wait for threads. */
	for (int i = 0; i < THREADS; ++i) {
		pthread_join(thread_ids[i], NULL);
	}

	DSTRM_EVENT(TEST, LINUX_END, 0);
	
	printf("Force linux test complete.\n");

	/* Cleanup the group we created to represent the pipeline */
	if (gsched_uninstall_group(grp_fd, safety_mem)) {
		perror("uninstall group");
	}

	if (grp_leave_group(grp_fd, safety_group, test_mem)) {
		perror("leave group");
	}

	if (grp_destroy_group(grp_fd, test_group)) {
		perror("destroy test_group");
	}

	if (grp_destroy_group(grp_fd, safety_group)) {
		perror("destroy safety_group");
	}

	close(grp_fd);
	
	DSUI_CLEANUP();
	
	return 0;
}
