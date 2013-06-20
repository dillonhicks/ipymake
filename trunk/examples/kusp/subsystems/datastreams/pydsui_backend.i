/*  pydsui.i -- Swig interface file for pydsui.c
 *  
 */

%module pydsui_backend
%inline %{

  extern void dstream_close(void);
  extern void dstream_open(const char *filename);
  extern void dstream_print(char *msg);
  extern void dstream_event(char *group, char *event, int tag, char* data);
  extern void dstream_histogram_add(char *group, char *event, int increment);
  extern void dstream_counter_add(char *group, char *event, int increment);
  extern void dstream_interval_start(char *group, char *event);
  extern void dstream_interval_end(char *group, char *event, int tag);
  
%}
