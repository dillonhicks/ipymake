#include <fcntl.h>
#include <stdio.h>
#include <sys/ioctl.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>

#include <linux/sched_gsched.h>
#include <sched_gsched.h>

#define fprintf(f, s, ...)

/**
 * Open the group scheduling device to get a file descriptor through
 * which we can interact with the system scheduling policies
 *
 * @retval  File-descriptor used to interact with device through ioctl()
 * @retval  -EINVAL group scheduling device unavailable
 */
int grp_open(void)
{
	int file_desc = open("/dev/group_sched", 0);

	if (file_desc < 0) {
	  return -errno;
	}

	return file_desc;
}

/* Closes the group. */
int grp_close(int fd)
{
	int retval = 0;
	retval = close(fd);
	return retval;
}

/**
 * Create a group with the specified name and associate
 * the named scheduler with the new group
 *
 * @param  fd          File descriptor to the group scheduling device
 * @param  group_name  String to identify the group to be created
 * @param  sched_name  String identifier of the scheduler to be used for the group
 * @param  flags       Currently unused
 *
 * @retval integer ID of created group
 * @retval -ENOMEM "insufficient kernel memory to create group"
 * @retval -EINVAL "bad parameter"
 * @retval -EEXIST "group already exists"
 *
 *
 * Creates a group with the name group_name, using the scheduler
 * identified by sched_name to schedule the group members. The flags
 * value is currently unused, but available for future expansion
 */
int grp_create_group(int fd, const char *group_name, const char *sched_name)
{
	int retval = 0;
	grp_ioctl_create_group_t ioctl_args;

	if (strlen(group_name) >= GSCHED_NAME_LEN ||
			strlen(sched_name) >= GSCHED_NAME_LEN)
		return -EINVAL;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.group_name, group_name);
	strcpy(ioctl_args.sched_name, sched_name);

	retval = ioctl(fd, GRP_IOCTL_CREATE_GROUP, &ioctl_args);
	if (retval < 0)
	  retval = -errno;

	if (retval) {
		fprintf(stderr, "grp_create_group: group_name [%s] "\
				"sched_name [%s] error [%d:%s]\n", group_name,
				sched_name, retval, strerror(errno));
	}

	return retval;
}

/**
 * Set one or more group level parameters, using the group name to
 * identify it
 *
 * @param  fd             File descriptor connected to the group scheduling device
 * @param  group_name     Name of the desired group
 * @param  parameter_ptr  Void pointer to the scheduler-specific structure giving parameter
 * @param  size           Size of scheudler-specific information
 *
 * @retval 0 for success
 * @retval -EFAULT
 * @retval -EINVAL
 * @retval -ENOMEM
 *
 * Set a parameter while idenitfying the group by name
 */
int grp_set_group_parameters(int fd, const char *group_name, void *parameter_ptr,
		size_t size)
{
	int retval = 0;
	grp_ioctl_group_parameters_t ioctl_args;

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

	return retval;
}

/**
 * get a group level parameter using the group name
 *
 * @param  fd            File descriptor connected to the group scheduling device
 * @param  group_name    name of the group for which the parameter is sought
 * @param  parameter_ptr Void pointer to the scheduler-specific structure receiving the parameter
 * @param  size          Size of the parameter receiving structure
 *
 * @retval 0 for success
 * @retval -EFAULT
 * @retval -EINVAL
 * @retval -ENOMEM
 */
int grp_get_group_parameters(int fd, const char *group_name, void *parameter_ptr,
		size_t size)
{
	int retval = 0;
	grp_ioctl_group_parameters_t ioctl_args;

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

	return retval;
}

int grp_set_group_opts(int fd, const char* group_name, int opts)
{
	int retval = 0;
	grp_ioctl_set_group_opts_t ioctl_args;

	if (strlen(group_name) >= GSCHED_NAME_LEN)
		return -EINVAL;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.group_name, group_name);
	ioctl_args.opts = opts;

	retval = ioctl(fd, GRP_IOCTL_SET_GROUP_OPTS, &ioctl_args);
	if (retval < 0) {
	    retval = -errno;
	}

	if (retval) {
		fprintf(stderr, "grp_set_group_opts: group_name [%s] "\
				"opts [%d] error [%d:%s]\n",
				group_name, opts,
				retval, strerror(errno));
	}

	return retval;

}

int grp_get_group_opts(int fd, const char* group_name, int* opts)
{
	int retval = 0;
	grp_ioctl_get_group_opts_t ioctl_args;

	if (strlen(group_name) >= GSCHED_NAME_LEN)
		return -EINVAL;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.group_name, group_name);
	ioctl_args.opts = opts;

	retval = ioctl(fd, GRP_IOCTL_GET_GROUP_OPTS, &ioctl_args);
	if (retval < 0)
	  retval = -errno;

	return retval;
}

/**
 * Set the parameters of a member of a group, using the names of the group
 * and the member to identify the element whose parameters are set
 *
 * @param  fd            File descriptor connected to the group scheduling device
 * @param  group_name    Name of the group
 * @param  member_name   Name of the member
 * @param  parameter_ptr Void pointer to the scheduler-specific structure giving parameter
 * @param  size          Size of scheduler-specific information
 *
 * @retval 0 for success
 * @retval -EFAULT
 * @retval -EINVAL
 * @retval -ENOMEM
 */
int grp_set_member_parameters(int fd, const char *group_name, const char *member_name,
		void *parameter_ptr, size_t size)
{

	int retval = 0;
	grp_ioctl_member_parameters_t ioctl_args;

	if (strlen(group_name) >= GSCHED_NAME_LEN ||
			strlen(member_name) >= GSCHED_NAME_LEN)
		return -EINVAL;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	ioctl_args.rw = GRP_IOCTL_PARAMETERS_WRITE;
	strcpy(ioctl_args.group_name, group_name);
	strcpy(ioctl_args.member_name, member_name);
	ioctl_args.parameter_ptr = parameter_ptr;
	ioctl_args.size = size;

	retval = ioctl(fd, GRP_IOCTL_MEMBER_PARAMETERS, &ioctl_args);
	if (retval < 0) {
	    retval = -errno;
	}

	if (retval) {
		fprintf(stderr, "grp_set_member_parameters: group_name [%s] "\
				"member_name [%s] size/param [%lu/%lu] "\
				"error [%d:%s]\n", group_name, member_name,
				(unsigned long)parameter_ptr,
				(unsigned long)size, retval, strerror(errno));
	}

	return retval;
}

int gsched_set_member_param_int(int fd, const char *group, const char *member, int value)
{
	int param = value;

	return grp_set_member_parameters(fd, group, member, &param, sizeof(param));
}

/**
 * get a group member parameter using the group and member names
 *
 * @param  fd            File descriptor connected to the group scheduling device
 * @param  group_name    Group name
 * @param  member_name   Member name
 * @param  parameter_ptr Void pointer to the scheduler-specific structure giving parameter
 * @param  size          Size of scheduler-specific information
 *
 * @retval 0 for success
 * @retval -EFAULT
 * @retval -EINVAL
 * @retval -ENOMEM
 */
int grp_get_member_parameters(int fd, const char *group_name, const char *member_name,
		void *parameter_ptr, size_t size)
{

	int retval = 0;
	grp_ioctl_member_parameters_t ioctl_args;

	if (strlen(group_name) >= GSCHED_NAME_LEN ||
			strlen(member_name) >= GSCHED_NAME_LEN)
		return -EINVAL;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	ioctl_args.rw = GRP_IOCTL_PARAMETERS_READ;
	strcpy(ioctl_args.group_name, group_name);
	strcpy(ioctl_args.member_name, member_name);
	ioctl_args.parameter_ptr = parameter_ptr;
	ioctl_args.size = size;

	retval = ioctl(fd, GRP_IOCTL_MEMBER_PARAMETERS, &ioctl_args);
	if (retval < 0)
	  retval = -errno;

	return retval;
}

int gsched_get_member_param_int(int fd, const char *group, const char *member, int *value)
{
	int param, ret;

	ret = grp_get_member_parameters(fd, group, member, &param, sizeof(param));
	*value = param;

	return ret;
}

int grp_pid_join_group(int fd, const char *group_name, pid_t pid, const char *member_name)
{
	int retval;
	grp_ioctl_pid_join_group_t ioctl_args;

	if (strlen(group_name) >= GSCHED_NAME_LEN ||
			strlen(member_name) >= GSCHED_NAME_LEN)
		return -EINVAL;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.group_name, group_name);
	strcpy(ioctl_args.member_name, member_name);
	ioctl_args.pid = pid;

	retval = ioctl(fd, GRP_IOCTL_PID_JOIN_GROUP, &ioctl_args);
	if (retval < 0)
		retval = -errno;

	if (retval) {
		fprintf(stderr, "grp_pid_join_group: group_name [%s] "\
				"pid [%d] member_name [%s] "\
				"error [%d:%s]\n",
				group_name, pid, member_name,
				retval, strerror(errno));
	}

	return retval;
}

int grp_name_join_group(int fd, const char *group_name, const char *ccsm_name, int exclusive)
{
	int retval;
	grp_ioctl_name_join_group_t ioctl_args;

	if (strlen(group_name) >= GSCHED_NAME_LEN ||
			strlen(ccsm_name) >= GSCHED_NAME_LEN){
		printf("***************ERROR 1*************");
		return -EINVAL;
	}

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.group_name, group_name);
	strcpy(ioctl_args.ccsm_name, ccsm_name);
	ioctl_args.exclusive = exclusive;

	retval = ioctl(fd, GRP_IOCTL_NAME_JOIN_GROUP, &ioctl_args);
	if (retval < 0){

		retval = -errno;
		printf("***************ERROR 2***************\n");
		printf("fd: %d\nGRP_IO_CMD %d\n",fd, GRP_IOCTL_NAME_JOIN_GROUP);
		printf("gn: %s\nccsm %s\nexcl %d\n", ioctl_args.group_name,
				ioctl_args.ccsm_name,
				ioctl_args.exclusive);
	}
	if (retval) {
		printf("grp_name_join_group: group_name [%s] "\
				"ccsm_name [%s] exclusive [%d] "\
				"error [%d:%s]\n",
				group_name, ccsm_name, exclusive,
				retval, strerror(errno));
	}

	return retval;
}

int grp_group_join_group(int fd, const char *group_name, const char *add_group_name,
		const char *member_name)
{
	int retval;
	grp_ioctl_group_join_group_t ioctl_args;

	if (strlen(group_name) >= GSCHED_NAME_LEN ||
			strlen(member_name) >= GSCHED_NAME_LEN ||
			strlen(add_group_name) >= GSCHED_NAME_LEN)
		return -EINVAL;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.group_name, group_name);
	strcpy(ioctl_args.member_name, member_name);
	strcpy(ioctl_args.add_group_name, add_group_name);

	retval = ioctl(fd, GRP_IOCTL_GROUP_JOIN_GROUP, &ioctl_args);
	if (retval < 0)
		retval = -errno;

	if (retval) {
		fprintf(stderr, "grp_group_join_group: group_name [%s] "\
				"add_group_name [%s] member_name [%s] "\
				"error [%d:%s]\n", group_name, add_group_name,
				member_name, retval, strerror(errno));
	}

	return retval;
}

/**
 * An entity leaves a group with the group identified by name
 *
 * @param  fd             File descriptor connected to the group scheduling device
 * @param  group_name     name of group being left
 * @param  member_name    member name the entity leaving the group
 *
 * @retval    0         for success
 * @retval    -EINVAL   invalid operation, perhaps the group does not exist or entity is already a member of the group
 * @retval    -EFAULT   Error copying IOCTL parameter structure into OS
 */
int grp_leave_group(int fd, const char *group_name, const char *member_name)
{
	int retval;
	grp_ioctl_leave_t ioctl_args;

	if (strlen(group_name) >= GSCHED_NAME_LEN ||
			strlen(member_name) >= GSCHED_NAME_LEN)
		return -EINVAL;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.group_name, group_name);
	strcpy(ioctl_args.member_name, member_name);

	retval = ioctl(fd, GRP_IOCTL_LEAVE, &ioctl_args);
	if (retval < 0)
	  retval = -errno;

	if (retval) {
		fprintf(stderr, "grp_leave_group: group_name [%s] member_name [%s] "\
				"error [%d:%s]\n", group_name, member_name,
				retval, strerror(errno));
	}

	return retval;
}

/**
 * We destroy a group identified by name
 *
 * @param  fd             File descriptor connected to the group scheduling device
 * @param  group_name     Name of group being Destroyed
 *
 * @retval    0         for success
 * @retval    -EINVAL   invalid operation, perhaps the group does not exist or entity is already a member of the group
 * @retval    -EFAULT   Error copying IOCTL parameter structure into OS
 * @retval    -EEXIST   Group does not exist
 * @retval    -EBUSY    Group is not empty of members
 *
 * Removes a group from the database provided it does not have any
 * members in it
 */
int grp_destroy_group(int fd, const char *group_name)
{
	int retval;
	grp_ioctl_destroy_group_t ioctl_args;

	if (strlen(group_name) >= GSCHED_NAME_LEN)
		return -EINVAL;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	strcpy(ioctl_args.group_name, group_name);

	retval = ioctl(fd, GRP_IOCTL_DESTROY_GROUP, &ioctl_args);
	if (retval < 0)
	  retval = -errno;

	if (retval) {
		fprintf(stderr, "grp_destroy_group: group_name [%s] error [%d:%s]\n",
				group_name, retval, strerror(errno));
	}

	return retval;
}

int gsched_install_group(int fd, const char *group, const char *member_name)
{
	return grp_group_join_group(fd, GSCHED_TOP_GROUP_NAME, group, member_name);
}

int gsched_uninstall_group(int fd, const char *member_name)
{
	return grp_leave_group(fd, GSCHED_TOP_GROUP_NAME, member_name);
}

int gsched_set_exclusive_control(int fd, pid_t pid)
{
	int retval;
	grp_ioctl_exclusive_t ioctl_args;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	ioctl_args.pid = pid;

	retval = ioctl(fd, GRP_IOCTL_SET_EXCLUSIVE, &ioctl_args);
	if (retval < 0)
		retval = -errno;

	if (retval) {
		fprintf(stderr, "grp_set_exclusive_control: pid [%d] "\
				"error [%d:%s]\n", pid, retval, strerror(errno));
	}

	return retval;
}

int gsched_clear_exclusive_control(int fd, pid_t pid)
{
	int retval;
	grp_ioctl_exclusive_t ioctl_args;

	memset(&ioctl_args, 0, sizeof(ioctl_args));
	ioctl_args.pid = pid;

	retval = ioctl(fd, GRP_IOCTL_CLEAR_EXCLUSIVE, &ioctl_args);
	if (retval < 0)
		retval = -errno;

	if (retval) {
		fprintf(stderr, "grp_clear_exclusive_control: pid [%d] "\
				"error [%d:%s]\n", pid, retval, strerror(errno));
	}

	return retval;
}

