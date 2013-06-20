/**
 * @file
 * @addtogroup libkusp libkusp
 */

#include <kusp_common.h>
#include <config.h>

/**
 * Print a greeting and copyright notice
 */
void print_greeting(char *module_name)
{
	printf("%s %s\n", module_name, PACKAGE_VERSION);
	printf("part of %s\n", PACKAGE_NAME);
	printf("http://ittc.ku.edu/kusp\n");
	printf("(C) 1996-2009 The University Of Kansas\n");
	printf("\n");
}

