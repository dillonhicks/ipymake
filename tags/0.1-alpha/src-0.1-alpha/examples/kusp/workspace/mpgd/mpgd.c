#include <unistd.h>
#include <stdio.h>
#include <sys/time.h>
#include <string.h>
#include <stdlib.h>

#include <sched_gsched.h>
#include <linux/gsched_sdf_mpgd.h>

#include "mpgd.h"

/* TODO: specialize based on port-type. Hard-coded now for sockets */
int mpgd_send_event(int fd, struct timespec *timestamp, void *data, size_t len)
{
	struct mpgd_event event;

	memset(&event, 0, sizeof(event));
	event.header.magic = MPGD_MAGIC_NUM;
	event.header.timestamp = *timestamp;

	if (len > MPGD_EVENT_SIZE) {
		fprintf(stderr, "mpgd_send_event: len > MPGD_EVENT_SIZE\n");
		return (len-MPGD_EVENT_SIZE);
	}

	if (data && len)
		memcpy(event.payload, data, len);

	write(fd, &event, sizeof(event));

	return 0;
}

int mpgd_add_port_socket(int gsfd, int fd, char *member_name,
		struct mpgd_port *port)
{
	struct mpgd_param param;
	int ret;

	/* setup member parameter command for adding socket port */
	param.cmd = MPGD_CMD_ADD_PORT;
	param.port.type = MPGD_PORT_SOCK;
	param.port.fd = fd;
	param.port.id = port->port_id;
	
	/* send command to group scheduling */
	ret = grp_set_member_parameters(gsfd, "mpgd", member_name, &param, sizeof(param));

	if (ret < 0) {
		fprintf(stderr, "mpgd_add_port_socket: failed to add port: ret=%d\n", ret);
		return ret;
	}

	port->type = MPGD_PORT_SOCK;
	port->sockfd = fd;
	strcpy(port->member_name, member_name);

	return 0;
}

int mpgd_alloc_port(int gsfd, struct mpgd_port *p, int direction)
{
	struct mpgd_param param;
	int ret;

	memset(p, 0, sizeof(*p));

	param.cmd = MPGD_CMD_ALLOC_PORT;
	param.port.direction = direction;

	/* send command to group scheduling */
	ret = grp_set_group_parameters(gsfd, "mpgd", &param, sizeof(param));

	if (ret < 0) {
		fprintf(stderr, "mpgd_alloc_port: failed to alloc port: ret=%d\n", ret);
		return ret;
	}

	p->port_id = ret;

	return 0;
}

int mpgd_recv_event(int gsfd, struct mpgd_event *event, struct mpgd_port *port)
{
	struct mpgd_param param;
	struct mpgd_event _event;
	int ret;

	/*
	 * Temporary hack that creates a sink for data in the socket. Actual
	 * events are delivered via IOCTL, as they may need to be reordered,
	 * something that can't be done with the events sitting in packets.
	 */
	read(port->sockfd, &_event, sizeof(_event));
	memset(&_event, 0, sizeof(_event));

	param.cmd = MPGD_CMD_GET_PORT_EVENT;
	param.addr = (unsigned long)(&_event);
	param.port.id = port->port_id;

	ret = grp_set_member_parameters(gsfd, "mpgd", port->member_name,
			&param, sizeof(param));

	if (ret < 0) {
		fprintf(stderr, "mpgd_recv_event: failed to get event: ret=%d\n", ret);
		return ret;
	}

	memcpy(event, &_event, sizeof(*event));

	return ret;
}

int mpgd_print_config(int gsfd)
{
	struct mpgd_param param;
	int ret;

	param.cmd = MPGD_CMD_PRINT_CONFIG;
	ret = grp_set_group_parameters(gsfd, "mpgd", &param, sizeof(param));

	if (ret < 0) {
		fprintf(stderr, "mpgd_print_config: failed: ret=%d\n", ret);
		return ret;
	}

	return ret;
}

int mpgd_set_delta0(int gsfd, struct mpgd_port *i, struct mpgd_port *o,
		struct timespec *time)
{
	struct mpgd_param param;
	int ret;

	param.cmd = MPGD_CMD_SET_DELTAZERO;
	param.port.id = i->port_id;
	param.port2.id = o->port_id;
	param.time = *time;

	ret = grp_set_group_parameters(gsfd, "mpgd", &param, sizeof(param));
	if (ret < 0) {
		fprintf(stderr, "mpgd_set_delay0: failed: ret=%d\n", ret);
		return ret;
	}

	return ret;
}

int mpgd_set_physical_delay(int gsfd, struct mpgd_port *i, struct timespec *time)
{
	struct mpgd_param param;
	int ret;

	param.cmd = MPGD_CMD_SET_DELAY_PHY;
	param.port.id = i->port_id;
	param.time = *time;

	ret = grp_set_group_parameters(gsfd, "mpgd", &param, sizeof(param));
	if (ret < 0) {
		fprintf(stderr, "mpgd_set_delay_phy: failed: ret=%d\n", ret);
		return ret;
	}

	return ret;
}

int mpgd_add_cut_port(int gsfd, struct mpgd_port *a, struct mpgd_port *b)
{
	struct mpgd_param param;
	int ret;

	param.cmd = MPGD_CMD_ADD_CUT_PORT;
	param.port.id = a->port_id;
	param.port2.id = b->port_id;

	ret = grp_set_group_parameters(gsfd, "mpgd", &param, sizeof(param));
	if (ret < 0) {
		fprintf(stderr, "mpgd_add_cut_port: failed: ret=%d\n", ret);
		return ret;
	}

	return ret;
}

int mpgd_add_input_group_port(int gsfd, struct mpgd_port *a, struct mpgd_port *b)
{
	struct mpgd_param param;
	int ret;

	param.cmd = MPGD_CMD_ADD_INPUT_GROUP_PORT;
	param.port.id = a->port_id;
	param.port2.id = b->port_id;

	ret = grp_set_group_parameters(gsfd, "mpgd", &param, sizeof(param));
	if (ret < 0) {
		fprintf(stderr, "mpgd_add_input_group_port: failed: ret=%d\n", ret);
		return ret;
	}

	return ret;
}

int mpgd_config_init(int gsfd)
{
	struct mpgd_param param;
	int ret;

	param.cmd = MPGD_CMD_INIT;

	ret = grp_set_group_parameters(gsfd, "mpgd", &param, sizeof(param));
	if (ret < 0) {
		fprintf(stderr, "mpgd_init: failed: ret=%d\n", ret);
		return ret;
	}

	return ret;
}

