/**
 * Functions which are conditionally compiled for various
 * platforms end up in here.
 *
 * @file
 * @addtogroup libkusp libkusp
 */

#include <config.h>
#include <misc.h>
#include <kusp_common.h>
#include <sys/time.h>
#include <string.h>

/**
 * @fn gettid
 * get the current thread ID. on NPTL linux machines,
 * we have to do a special system call, since getpid always
 * returns the PID of the root, parent process when called
 * in a pthread
 */
#include <unistd.h>
#ifdef HAVE_LINUX_UNISTD_H
#include <linux/unistd.h>
//_syscall0(pid_t, gettid);
//pid_t gettid(void);
pid_t gettid(void) {
	return syscall(__NR_gettid);
}

#else
pid_t gettid(void) {
	return getpid();
}
#endif

// GetRelativeFilename(), by Rob Fisher.
// rfisher@iee.org
// http://come.to/robfisher

// defines
#define MAX_FILENAME_LEN 512

// The number of characters at the start of an absolute filename.  e.g. in DOS,
// absolute filenames start with "X:\" so this value should be 3, in UNIX they start
// with "\" so this value should be 1.
#define ABSOLUTE_NAME_START 1

// set this to '\\' for DOS or '/' for UNIX
#define SLASH '/'


/**
 * Given the absolute current directory and an absolute file name, returns a
 * relative file name.  For example, if the current directory is C:\foo\bar
 * and the filename C:\foo\whee\text.txt is given,
 * GetRelativeFilename will return ..\whee\text.txt.
 */
char* get_relative_filename(char *currentDirectory, char *absoluteFilename)
{
	// declarations - put here so this should work in a C compiler
	int afMarker = 0, rfMarker = 0;
	int cdLen = 0, afLen = 0;
	int i = 0;
	int levels = 0;
	static char relativeFilename[MAX_FILENAME_LEN+1];

	cdLen = strlen(currentDirectory);
	afLen = strlen(absoluteFilename);

	// make sure the names are not too long or too short
	if(cdLen > MAX_FILENAME_LEN || cdLen < ABSOLUTE_NAME_START+1 ||
		afLen > MAX_FILENAME_LEN || afLen < ABSOLUTE_NAME_START+1)
	{
		return NULL;
	}

	// Handle DOS names that are on different drives:
	if(currentDirectory[0] != absoluteFilename[0])
	{
		// not on the same drive, so only absolute filename will do
		strcpy(relativeFilename, absoluteFilename);
		return relativeFilename;
	}

	// they are on the same drive, find out how much of the current directory
	// is in the absolute filename
	i = ABSOLUTE_NAME_START;
	while(i < afLen && i < cdLen && currentDirectory[i] == absoluteFilename[i])
	{
		i++;
	}

	if(i == cdLen && (absoluteFilename[i] == SLASH || absoluteFilename[i-1] == SLASH))
	{
		// the whole current directory name is in the file name,
		// so we just trim off the current directory name to get the
		// current file name.
		if(absoluteFilename[i] == SLASH)
		{
			// a directory name might have a trailing slash but a relative
			// file name should not have a leading one...
			i++;
		}

		strcpy(relativeFilename, &absoluteFilename[i]);
		return relativeFilename;
	}


	// The file is not in a child directory of the current directory, so we
	// need to step back the appropriate number of parent directories by
	// using "..\"s.  First find out how many levels deeper we are than the
	// common directory
	afMarker = i;
	levels = 1;

	// count the number of directory levels we have to go up to get to the
	// common directory
	while(i < cdLen)
	{
		i++;
		if(currentDirectory[i] == SLASH)
		{
			// make sure it's not a trailing slash
			i++;
			if(currentDirectory[i] != '\0')
			{
				levels++;
			}
		}
	}

	// move the absolute filename marker back to the start of the directory name
	// that it has stopped in.
	while(afMarker > 0 && absoluteFilename[afMarker-1] != SLASH)
	{
		afMarker--;
	}

	// check that the result will not be too long
	if(levels * 3 + afLen - afMarker > MAX_FILENAME_LEN)
	{
		return NULL;
	}

	// add the appropriate number of "..\"s.
	rfMarker = 0;
	for(i = 0; i < levels; i++)
	{
		relativeFilename[rfMarker++] = '.';
		relativeFilename[rfMarker++] = '.';
		relativeFilename[rfMarker++] = SLASH;
	}

	// copy the rest of the filename into the result string
	strcpy(&relativeFilename[rfMarker], &absoluteFilename[afMarker]);

	return relativeFilename;
}

