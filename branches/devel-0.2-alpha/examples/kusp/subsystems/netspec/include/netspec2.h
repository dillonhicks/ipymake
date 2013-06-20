#ifndef _NETSPEC_2_H_
#define _NETSPEC_2_H_

#include <configfile.h>

#define NS_OK		0
#define NS_WARNING	1
#define NS_OK_EXIT	2
#define NS_ERROR	3
#define NS_DIED		4


/* external interface for C-based NETSPEC daemons */

/* Set a function to execute for a named phase. All phase functions
 * a configfile dictionary as a parameter. Takes ownership of all pointers passed in */
void ns_set_execute(char *phase, hashtable_t *spec,
		void (*func_ptr)(hashtable_t *config), char *doc);

/* All phase functions should call this at the end to acknowledge completion.
 * The error code should be 0 on success, or some errno value. If filename
 * is not NULL, the file will be sent back to the control machine. You can
 * send a dictionary back too, or just make it NULL */
void ns_acknowledge_files(int error, char *message, list_t *filenames,
		hashtable_t *config);

// filename can be null
void ns_acknowledge(int error, char *message, char *filename,
		hashtable_t *config);

/** scan command line parameters, returning non-zero if netspec is going to be used */
int ns_initialize(int *argc, char ***argv);


/* Once all the function pointers are set up, execute this to begin listening
 * on stdin for phase commands */
void ns_begin(void);


// protocol stuff
hashtable_t *ns_read_config(void);

// recursively frees the hashtable after it is sent
void ns_send_config(hashtable_t *data);

#endif
