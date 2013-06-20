
 /* pydsui.i 
 *
 * SWIG Interface file for pydsui.c.
 * 
 */
 %module pydsui
 %inline %{

extern void PYDSTRM_BEGIN(int *argcp, char **argvp, const char * filename);
extern void PYDSTRM_CLEANUP(void);
extern void PYDSTRM_EVENT_DATA(const char *fname, const *ename, int tag, const char *str_data );

 %}
 

