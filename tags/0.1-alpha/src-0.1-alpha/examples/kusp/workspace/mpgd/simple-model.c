#define _GNU_SOURCE
#include <stdio.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <string.h>
#include <pthread.h>
#include <sys/time.h>

/* userspace MPGD library */
#include "mpgd.h"

#include <sched_gsched.h>
#include <linux/gsched_sdf_mpgd.h>

#define gettid() syscall(__NR_gettid)

/* sensor <--> computation channel */
static int sensor_comp_sockets[2];

/* pthreads */
static pthread_t sensor_pthread;
static pthread_t computation_pthread;
static pthread_t sink;

/* group scheduling */
static int gsfd;

/* ports */
struct mpgd_port sensor_out;
struct mpgd_port source_in;
struct mpgd_port source_computation_out;
struct mpgd_port source_feedback_out;
struct mpgd_port computation_sensor_in;
struct mpgd_port computation_source_in;
struct mpgd_port computation_out;
struct mpgd_port delay_in, delay_out;
struct mpgd_port actuator_in;

static void *sensor(void *arg)
{
	struct timeval tod;
	struct timespec timestamp;
	int cnt = 6;

	while (cnt--) {
		sleep(1);
		gettimeofday(&tod, NULL);
		timestamp.tv_sec = tod.tv_sec;
		mpgd_send_event(sensor_comp_sockets[1], &timestamp, NULL, 0);
	}

	close(sensor_comp_sockets[1]);

	pthread_exit(NULL);
}

static void *computation(void *arg)
{
	struct mpgd_event event;
	int cnt = 6;

	grp_pid_join_group(gsfd, "mpgd", gettid(), "comp1");
	mpgd_add_port_socket(gsfd, sensor_comp_sockets[0], "comp1", &computation_sensor_in);

	while (cnt--) {
		mpgd_recv_event(gsfd, &event, &computation_sensor_in);
		printf("xxxy: msg: %lu\n", event.header.timestamp.tv_sec);
	}

	close(sensor_comp_sockets[0]);

	pthread_exit(NULL);
}

int main(int argc, char **argv)
{
	struct timespec ts;

	/* START push into MPGD library */
	gsfd = grp_open();
	if (gsfd < 0) {
		perror("grp_open");
		return gsfd;
	}

	grp_create_group(gsfd, "mpgd", "sdf_mpgd");
	/* END push into MPGD library */

	/*
	 * TODO: use configuration file to specify all of these system
	 * parameters
	 */

	/* allocate sensor ports */
	mpgd_alloc_port(gsfd, &sensor_out, MPGD_PORT_OUTPUT);

	/* allocate source ports */
	mpgd_alloc_port(gsfd, &source_in, MPGD_PORT_INPUT);
	mpgd_alloc_port(gsfd, &source_computation_out, MPGD_PORT_OUTPUT);
	mpgd_alloc_port(gsfd, &source_feedback_out, MPGD_PORT_OUTPUT);

	/* allocate computation ports */
	mpgd_alloc_port(gsfd, &computation_sensor_in, MPGD_PORT_INPUT);
	mpgd_alloc_port(gsfd, &computation_source_in, MPGD_PORT_INPUT);
	mpgd_alloc_port(gsfd, &computation_out, MPGD_PORT_OUTPUT);

	/* allocate delay */
	mpgd_alloc_port(gsfd, &delay_in, MPGD_PORT_INPUT);
	mpgd_alloc_port(gsfd, &delay_out, MPGD_PORT_OUTPUT);

	/* allocate actuator */
	mpgd_alloc_port(gsfd, &actuator_in, MPGD_PORT_INPUT);

	/* setup adjacency matrix and delta0 values */
	ts.tv_sec = 0; ts.tv_nsec = 0;
	mpgd_set_delta0(gsfd, &sensor_out, &computation_sensor_in, &ts);
	mpgd_set_delta0(gsfd, &source_computation_out, &computation_source_in, &ts);
	mpgd_set_delta0(gsfd, &source_feedback_out, &source_in, &ts);
	mpgd_set_delta0(gsfd, &computation_out, &delay_in, &ts);
	mpgd_set_delta0(gsfd, &delay_out, &actuator_in, &ts);

	ts.tv_sec = 1; ts.tv_nsec = 0;
	mpgd_set_delta0(gsfd, &computation_sensor_in, &computation_out, &ts);
	ts.tv_sec = 2; ts.tv_nsec = 0;
	mpgd_set_delta0(gsfd, &computation_source_in, &computation_out, &ts);

	ts.tv_sec = 3; ts.tv_nsec = 0;
	mpgd_set_delta0(gsfd, &source_in, &source_computation_out, &ts);
	ts.tv_sec = 4; ts.tv_nsec = 0;
	mpgd_set_delta0(gsfd, &source_in, &source_feedback_out, &ts);

	ts.tv_sec = 5; ts.tv_nsec = 0;
	mpgd_set_delta0(gsfd, &delay_in, &delay_out, &ts);

	mpgd_add_cut_port(gsfd, &delay_in, &computation_sensor_in);
	mpgd_add_cut_port(gsfd, &delay_in, &computation_source_in);

	mpgd_add_input_group_port(gsfd, &delay_in, &delay_in);

	/* run initialization */
	mpgd_config_init(gsfd);

	/* print out configurations */
	mpgd_print_config(gsfd);

	if (socketpair(AF_UNIX, SOCK_DGRAM, 0, sensor_comp_sockets) < 0) {
		perror("socketpair");
		exit(1);
	}

	pthread_create(&sensor_pthread, NULL, sensor, NULL);
	pthread_create(&computation_pthread, NULL, computation, NULL);

	pthread_join(sensor_pthread, NULL);
	pthread_join(computation_pthread, NULL);

	/* Push into MPGD library */
	grp_leave_group(gsfd, "mpgd", "comp1");
	grp_destroy_group(gsfd, "mpgd");
	close(gsfd);

	return 0;
}
