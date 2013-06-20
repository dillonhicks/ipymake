/**
 * Various general-purpose macros and functions.
 * @file
 */

#ifndef _KUSP_COMMON_H_
#define _KUSP_COMMON_H_

#include <stdio.h>
#include <errno.h>
#include <string.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* a hack to stringify macros */
#define __xstr(s) #s
#define __str(s) __xstr(s)


/// a message that is prefixed by filename, function, and line number
#define CODE_MSG(format, ...) fprintf(stderr, __FILE__ ":%s:"  __str(__LINE__) ": " format, __func__, ##__VA_ARGS__)

/**
 * a message that is prefixed by the module name. if MODNAME is not defined,
 * just do a CODE_MSG
 */
#ifdef MODNAME
#define NAME_MSG(...) fprintf(stderr, MODNAME ": " __VA_ARGS__)
#else
#define NAME_MSG(...) CODE_MSG(__VA_ARGS__)
#endif

/// Use eprintf for error messages
#define eprintf(...) NAME_MSG("ERROR: " __VA_ARGS__)

/// use bprintf for bugs
#define bprintf(...) CODE_MSG("**BUG**: " __VA_ARGS__)

/// Warning messages
#define wprintf(...) NAME_MSG("WARNING: " __VA_ARGS__)

/// Use iprintf for information
#define iprintf(...) NAME_MSG(__VA_ARGS__)

#ifdef KUSP_DEBUG
/// debugging messages, only printed if KUSP_DEBUG is on
#define dprintf(...) CODE_MSG(__VA_ARGS__); fflush(stdout)

/// error messages that will only be shown when debugging is turned on
#define deprintf(...) eprintf(__VA_ARGS__)

/// header for a block to execute only if debugging is turned on
#define debug_action if (1)

#else // KUSP_DEBUG not defined
#define dprintf(...)
#define deprintf(...)
#define debug_action if (0) // optimizer will catch this
#endif // KUSP_DEBUG

/// just like perror, but show where in code the call happened
#define kusp_perror(str) kusp_errno(str, errno)

/// like kusp_perror(), but also specify the error code
#define kusp_errno(str, err) CODE_MSG("** SYSCALL ** %s failed: %s\n", str, strerror(err))


void print_greeting(char *module_name);


#endif // _KUSP_COMMON_H_
