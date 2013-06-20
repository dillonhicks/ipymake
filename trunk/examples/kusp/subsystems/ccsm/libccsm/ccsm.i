 /* ccsm.i 
 *
 * SWIG Interface file for ccsm.c.
 * 
 */
 %module ccsm
 %inline %{



extern int ccsm_open(void);
extern int ccsm_close(int);

extern int ccsm_destroy_set(int fd, const char *set_name);

extern int ccsm_add_member(int fd, const char *set_name, const char *member_name);
extern int ccsm_remove_member(int fd, const char *set_name, const char *member_name);

extern int ccsm_set_params(int fd, const char *set_name, void *param_ptr, unsigned int type);
extern int ccsm_get_params(int fd, const char *set_name, void *param_ptr, unsigned int type);

extern int ccsm_create_component_self(int fd, const char *component_name);
extern int ccsm_create_component_by_pid(int fd, const char *component_name, int pid);
extern int ccsm_destroy_component_by_name(int fd, const char *component_name);
extern int ccsm_destroy_component_by_pid(int fd, int pid);
 
 %}
 

/*  
 * Redefinition of ccsm_create_set that plays nicer with python typing.
 */ 
int ccsm_create_set(int fd, const char *set_name, int flags){
    unsigned int flgs = (unsigned int) flags;
    return ccsm_create_set(fd, set_name, flags);
}
