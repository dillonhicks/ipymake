#ifndef GROUP_SCHED_API_H
#define GROUP_SCHED_API_H

#include <sys/types.h>
#include <sched.h>

#ifdef __cplusplus
extern "C" {
#endif 

#define GSCHED_DEV_NAME "/dev/group_sched"

#define GSCHED_GO_MANAGED 0x01  /* Uninstall and destroy the group when it no longer has members */

extern int grp_open(void);
extern int grp_close(int);

extern int grp_create_group(int fd, const char *group_name, const char *sched_name);
extern int grp_set_group_parameters(int fd, const char *group_name, void *parameter_ptr, size_t size);
extern int grp_get_group_parameters(int fd, const char *group_name, void *parameter_ptr, size_t size);
extern int grp_set_group_opts(int fd, const char* group_name, int opts);
extern int grp_get_group_opts(int fd, const char* group_name, int* opts);
extern int grp_set_member_parameters(int fd, const char *group_name, const char *member_name, void *parameter_ptr, size_t size);
extern int grp_get_member_parameters(int fd, const char *group_name, const char *member_name, void *parameter_ptr, size_t size);


extern int grp_pid_join_group(int fd, const char *group_name, int pid, const char *member_name);
extern int grp_group_join_group(int fd, const char *group_name, const char *add_group_name, const char *member_name);

extern int grp_name_join_group(int fd, const char *group_name, const char *member_name, int exclusive);

extern int grp_leave_group(int fd, const char *group_name, const char *member_name);
extern int grp_destroy_group(int fd, const char *group_name);

extern int gsched_get_member_param_int(int fd, const char *group, const char *member, int *value);
extern int gsched_set_member_param_int(int fd, const char *group, const char *member, int value);

/* remove/add a task to/from the standard Linux scheduling group */
extern int gsched_set_exclusive_control(int fd, pid_t pid);
extern int gsched_clear_exclusive_control(int fd, pid_t pid);


extern int gsched_install_group(int fd, const char *group, const char *member_name);
extern int gsched_uninstall_group(int fd, const char *member_name);

#ifdef __cplusplus
}
#endif 

#endif	/* GROUP_SCHED_ABI_H */
