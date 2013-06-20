#ifndef CCSM_H
#define CCSM_H
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <sched.h>

#define CCSM_DEV_NAME "/dev/ccsm"

#ifdef __cplusplus
extern "C" {
#endif 

extern int ccsm_open(void);
extern int ccsm_close(int);

extern int ccsm_create_set(int fd, const char *set_name, unsigned int flags);
extern int ccsm_destroy_set(int fd, const char *set_name);

extern int ccsm_add_member(int fd, const char *set_name, const char *member_name);
extern int ccsm_remove_member(int fd, const char *set_name, const char *member_name);

//extern int ccsm_set_params(int fd, const char *set_name, void *param_ptr, unsigned int type);
//extern int ccsm_get_params(int fd, const char *set_name, void *param_ptr, unsigned int type);

extern int ccsm_create_component_self(int fd, const char *component_name);
extern int ccsm_create_component_by_pid(int fd, const char *component_name, int pid);
extern int ccsm_destroy_component_by_name(int fd, const char *component_name);
extern int ccsm_destroy_component_by_pid(int fd, int pid);

#ifdef __cplusplus
}
#endif 

#endif
