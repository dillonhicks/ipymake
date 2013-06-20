#ifndef MPGD_H
#define MPGD_H

#include <unistd.h>

#include <linux/sched_gsched.h>
#include <linux/gsched_sdf_mpgd.h>

struct mpgd_port {
	int type;
	int port_id;
	char member_name[GSCHED_NAME_LEN];
	int sockfd;
};

int mpgd_send_event(int fd, struct timespec *timestamp, void *data, size_t len);
int mpgd_add_port_socket(int gsfd, int fd, char *member_name, struct mpgd_port *port);
int mpgd_recv_event(int gsfd, struct mpgd_event *event, struct mpgd_port *port);
int mpgd_print_config(int gsfd);
int mpgd_set_delta0(int gsfd, struct mpgd_port *i, struct mpgd_port *o, struct timespec *time);
int mpgd_set_physical_delay(int gsfd, struct mpgd_port *i, struct timespec *time);
int mpgd_add_cut_port(int gsfd, struct mpgd_port *a, struct mpgd_port *b);
int mpgd_add_input_group_port(int gsfd, struct mpgd_port *a, struct mpgd_port *b);
int mpgd_alloc_port(int gsfd, struct mpgd_port *p, int direction);
int mpgd_config_init(int gsfd);

#endif
