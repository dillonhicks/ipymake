#define _GNU_SOURCE
#include <stdio.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <string.h>
#include <pthread.h>

/* userspace MPGD library */
#include "mpgd.h"

#include <sched_gsched.h>
#include <linux/gsched_sdf_mpgd.h>

#define gettid() syscall(__NR_gettid)

/* sensor <--> computation channel */
static int sensor_comp_sockets[2];

/* pthreads */
static pthread_t clock1_t, clock2_t;
static pthread_t time_delay_1_t, time_delay_2_t;
static pthread_t computation_t;

static pthread_t sensor_pthread;
static pthread_t computation_pthread;
static pthread_t sink;

/* group scheduling */
static int gsfd;

/* ports */
struct mpgd_port port1_out;
struct mpgd_port port2_out;
struct mpgd_port timed_delay1_in;
struct mpgd_port timed_delay1_out;
struct mpgd_port timed_delay2_in;
struct mpgd_port timed_delay2_out;
struct mpgd_port add_subtract_in1;
struct mpgd_port add_subtract_in2;
struct mpgd_port add_subtract_out;

static void *sensor(void *arg)
{
	struct timespec timestamp;
	int cnt = 6;

	timestamp.tv_sec = 0;
	timestamp.tv_nsec = 0;
	
	while (cnt--) {
		sleep(1);
		timestamp.tv_sec = cnt;
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
