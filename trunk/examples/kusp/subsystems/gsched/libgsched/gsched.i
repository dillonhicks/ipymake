 /* gsched.i 
 *
 * SWIG Interface file for gsched.c.
 * 
 */
 %module gsched
 %inline %{

 typedef int pid_t;
  
 extern	int grp_open(void);
 extern int grp_close(int);
 
 extern int grp_create_group(int fd, const char *group_name, const char *sched_name);
 extern int grp_set_group_parameters(int fd, const char *group_name, void *parameter_ptr,
		size_t size);
 extern int grp_get_group_parameters(int fd, const char *group_name, void *parameter_ptr,
		size_t size);
 extern int grp_set_group_opts(int fd, const char* group_name, int opts);
 extern int grp_get_group_opts(int fd, const char* group_name, int* opts);
 extern		int grp_set_member_parameters(int fd, const char *group_name, const char *member_name,
 		void *parameter_ptr, size_t size);
 extern		int gsched_set_member_param_int(int fd, const char *group, const char *member, int value);
 extern		int grp_get_member_parameters(int fd, const char *group_name, const char *member_name,
		void *parameter_ptr, size_t size);
 extern		int gsched_get_member_param_int(int fd, const char *group, const char *member, int *value);
 extern		int grp_name_join_group(int fd, const char *group_name, const char *member_name, int exclusive);
 extern		int grp_group_join_group(int fd, const char *group_name, const char *add_group_name,
		const char *member_name);
 extern		int grp_leave_group(int fd, const char *group_name, const char *member_name);
 extern		int grp_destroy_group(int fd, const char *group_name);
 extern		int gsched_install_group(int fd, char *group, char *member_name);
 extern		int gsched_uninstall_group(int fd, char *member_name);

 %}
 

/* 
 * Redefinitions that play nicer with python.
 */
int gsched_set_exclusive_control(int fd, int pid)
{
  pid_t new_pid = (pid_t)pid;
  return gsched_set_exclusive_control(fd, new_pid);
}

int gsched_clear_exclusive_control(int fd, int pid)
{
  pid_t new_pid = (pid_t)pid;
  return gsched_clear_exclusive_control(fd, new_pid);
}


int grp_pid_join_group(int fd, const char *group_name, int pid, const char *member_name){

    return grp_pid_join_group(fd, group_name, pid, member_name);
}
