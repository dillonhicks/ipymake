#include <fcntl.h>
#include <stdio.h>
#include <sys/ioctl.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>

#include <linux/ccsm.h>
#include <ccsm.h>

#define fprintf(f, s, ...)

/**
 * Open the CCSM device to get a file descriptor through
 * which we can interact with the system 
 *
 * @retval  File-descriptor used to interact with device through ioctl() 
 * @retval  -EINVAL CCSM device unavailable 
 */
int
ccsm_open(void)
{
	int file_desc = open("/dev/ccsm", 0);

	if (file_desc < 0) {
	  return -errno;
	}

	return file_desc;
}

/**
 * Close the CCSM device given its file descriptor
 *
 * @fd  File-descriptor used to interact with device through ioctl() 
 *
 * @retval  -EINVAL CCSM device unavailable 
 */
int
ccsm_close(int fd)
{
	int ret = 0;
	ret = close(fd);
	return ret;
}

/**
 * Create a set with the specified name and flags 
 * 
 * @param  fd          File descriptor to the CCSM device
 * @param  set_name    String to identify the set to be created
 * @param  flags       Set flags
 *
 * @retval 0 on success 
 * @retval -ENOMEM "insufficient kernel memory to create group"
 * @retval -EINVAL "bad parameter"
 * @retval -EEXIST "set already exists"
 *
 * Creates an empty set with the name @set_name, using the flags
 * identified by @flags to indicate several possible internal states
 */
int
ccsm_create_set(int fd, const char *set_name, unsigned int flags)
{
	int retval = 0;
	ccsm_ioctl_create_set_t ioctl_args;
	

	if (strlen(set_name) >= CCSM_MAX_NAME_LEN || flags < 0) {
		return -EINVAL;
	}

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.set_name, set_name);
	ioctl_args.flags = flags;

	retval = ioctl(fd, CCSM_IOCTL_CREATE_SET, &ioctl_args);
	if (retval < 0) {
		retval = -errno;
	}

	if (retval) {
		fprintf(stderr, "ccsm_create_set: set_name [%s] "\
				"flags [%d] error [%d:%s]\n", set_name,
				flags, retval, strerror(errno));
	}

	return retval;
}


int
ccsm_add_member(int fd, const char *set_name, const char *member_name)
{
	int retval;
	ccsm_ioctl_add_member_t ioctl_args;

	if (strlen(set_name) >= CCSM_MAX_NAME_LEN ||
			strlen(member_name) >= CCSM_MAX_NAME_LEN) {
		return -EINVAL;
	}
	
	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.set_name, set_name);
	strcpy(ioctl_args.member_name, member_name);

	retval = ioctl(fd, CCSM_IOCTL_ADD_MEMBER, &ioctl_args);
	if (retval < 0) {
		retval = -errno;
	}

	if (retval) {
		fprintf(stderr, "ccsm_add_member: set_name [%s] "\
				"member_name [%s] error [%d:%s]\n",
				set_name, member_name, retval, strerror(errno));
	}

	return retval;
}


int
ccsm_remove_member(int fd, const char *set_name, const char *member_name)
{
	int retval;
	ccsm_ioctl_remove_member_t ioctl_args;
	
	if (strlen(set_name) >= CCSM_MAX_NAME_LEN ||
			strlen(member_name) >= CCSM_MAX_NAME_LEN) {
		return -EINVAL;
	}

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.set_name, set_name);
	strcpy(ioctl_args.member_name, member_name);

	retval = ioctl(fd, CCSM_IOCTL_REMOVE_MEMBER, &ioctl_args);
	if (retval < 0) {
		retval = -errno;
	}
	
	if (retval) {
		fprintf(stderr, "ccsm_remove_member: set_name [%s] "\
				"member_name [%s] error [%d:%s]\n",
				set_name, member_name, retval, strerror(errno));
	}

	return retval;
}


int
ccsm_destroy_set(int fd, const char *set_name)
{
	int retval;
	ccsm_ioctl_destroy_set_t ioctl_args;
	
	if (strlen(set_name) >= CCSM_MAX_NAME_LEN) {
		return -EINVAL;
	}

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.set_name, set_name);

	retval = ioctl(fd, CCSM_IOCTL_DESTROY_SET, &ioctl_args);
	if (retval < 0) {
		retval = -errno;
	}

	if (retval) {
		fprintf(stderr, "ccsm_destroy_set: set_name [%s] error [%d:%s]\n",
				set_name, retval, strerror(errno));
	}

	return retval;
}


int
ccsm_set_params(int fd, const char *set_name, void *param_ptr, unsigned int type)
{
	int retval = 0;
#if 0	
	ccsm_ioctl_set_params_t ioctl_args;

	if (strlen(group_name) >= GSCHED_NAME_LEN)
		return -EINVAL;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	ioctl_args.rw = GRP_IOCTL_PARAMETERS_WRITE;
	strcpy(ioctl_args.group_name, group_name);
	ioctl_args.parameter_ptr = parameter_ptr;
	ioctl_args.size = size;

	retval = ioctl(fd, GRP_IOCTL_GROUP_PARAMETERS, &ioctl_args);
	if (retval < 0) {
	    retval = -errno;
	}

	if (retval) {
		fprintf(stderr, "grp_set_group_parameters: group_name [%s] "\
				"size/param [%lu/%lu] error [%d:%s]\n",
				group_name, (unsigned long)parameter_ptr,
				(unsigned long)size, retval, strerror(errno));
	}
#endif
	return retval;
}

int
ccsm_get_params(int fd, const char *set_name, void *param_ptr, unsigned int type)
{
	int retval = 0;
#if 0
	ccsm_ioctl_set_params_t ioctl_args;
	
	if (strlen(group_name) >= GSCHED_NAME_LEN)
		return -EINVAL;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	ioctl_args.rw = GRP_IOCTL_PARAMETERS_READ;
	strcpy(ioctl_args.group_name, group_name);
	ioctl_args.parameter_ptr = parameter_ptr;
	ioctl_args.size = size;

	retval = ioctl(fd, GRP_IOCTL_GROUP_PARAMETERS, &ioctl_args);
	if (retval < 0)
	  retval = -errno;
#endif	
	return retval;
}

int
ccsm_create_component_self(int fd, const char *component_name)
{
	int retval;
	ccsm_ioctl_create_component_self_t ioctl_args;

	if (strlen(component_name) >= CCSM_MAX_NAME_LEN) {
		return -EINVAL;
	}

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.component_name, component_name);

	retval = ioctl(fd, CCSM_IOCTL_CREATE_COMPONENT_SELF, &ioctl_args);
	if (retval < 0) {
		retval = -errno;
	}

	if (retval) {
		fprintf(stderr, "ccsm_create_component_self: component_name [%s] "\
				"error [%d:%s]\n", component_name, retval,
				strerror(errno));
	}

	return retval;
}

int
ccsm_create_component_by_pid(int fd, const char *component_name, pid_t pid)
{
	int retval;
	ccsm_ioctl_create_component_pid_t ioctl_args;

	if (strlen(component_name) >= CCSM_MAX_NAME_LEN) {
		return -EINVAL;
	}

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.component_name, component_name);
	ioctl_args.pid = pid;

	retval = ioctl(fd, CCSM_IOCTL_CREATE_COMPONENT_BY_PID, &ioctl_args);
	if (retval < 0) {
		retval = -errno;
	}

	if (retval) {
		fprintf(stderr, "ccsm_create_component_pid: pid [%d] "\
				"component_name [%s] error [%d:%s]\n",
				pid, component_name, retval,
				strerror(errno));
	}

	return retval;
}


int
ccsm_destroy_component_by_name(int fd, const char *component_name)
{
	int retval;
	ccsm_ioctl_destroy_component_t ioctl_args;
	
	if (strlen(component_name) >= CCSM_MAX_NAME_LEN) {
		return -EINVAL;
	}

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.component_name, component_name);

	retval = ioctl(fd, CCSM_IOCTL_DESTROY_COMPONENT_BY_NAME, &ioctl_args);
	if (retval < 0) {
		retval = -errno;
	}

	if (retval) {
		fprintf(stderr, "ccsm_destroy_component_by_name: set_name [%s] error [%d:%s]\n",
				set_name, retval, strerror(errno));
	}

	return retval;
}


int
ccsm_destroy_component_by_pid(int fd, pid_t pid)
{
	int retval;
	ccsm_ioctl_destroy_component_t ioctl_args;
	
	memset(&ioctl_args, 0, sizeof(ioctl_args));
	ioctl_args.pid = pid;

	retval = ioctl(fd, CCSM_IOCTL_DESTROY_COMPONENT_BY_PID, &ioctl_args);
	if (retval < 0) {
		retval = -errno;
	}

	if (retval) {
		fprintf(stderr, "ccsm_destroy_component_by_pid: set_pid [%d] error [%d:%s]\n",
				pid, retval, strerror(errno));
	}

	return retval;
}



