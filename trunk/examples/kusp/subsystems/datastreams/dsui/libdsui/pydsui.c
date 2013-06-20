#include "pydsui_dsui.h"


extern void PYDSTRM_BEGIN(int *argcp, char **argvp, const char * filename){  
  dsui_start(argcp, argvp, filename);
}

extern void PYDSTRM_CLEANUP(void){
  DSUI_CLEANUP();
}

/*
sighandler_t PYDSTRM_SIGNAL(int signum, sighandler_t handler){
  DSUI_SIGNAL(signum, handler);
}
*/
extern void PYDSTRM_EVENT_DATA(const char *fname, const *ename, int tag, const char *str_data ){
  int data_len = strlen(str_data);
  DSTRM_EVENT_DATA(fname, ename, tag, data_len, str_data, "print_string");
}
