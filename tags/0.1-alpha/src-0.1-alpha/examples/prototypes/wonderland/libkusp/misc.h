/**
 * @file
 */

#ifndef _KUSP_MISC_H_
#define _KUSP_MISC_H_

#include <sys/types.h>
#include <sys/time.h>
#include <time.h>
#include <stdint.h>

#ifndef _CYCLES_T
#define _CYCLES_T
typedef unsigned long long cycles_t;
#endif


pid_t gettid(void);

/*
 * min()/max() macros that also do
 * strict type-checking.. See the
 * "unnecessary" pointer comparison.
 */
#define min(x,y) ({ \
	typeof(x) _x = (x);	\
	typeof(y) _y = (y);	\
	(void) (&_x == &_y);		\
	_x < _y ? _x : _y; })

#define max(x,y) ({ \
	typeof(x) _x = (x);	\
	typeof(y) _y = (y);	\
	(void) (&_x == &_y);		\
	_x > _y ? _x : _y; })


/**
 * Return the timestamp counter. */


// taken from ffmpeg source code

#if defined(__x86_64__)
static inline uint64_t get_tsc(void)
{
        uint64_t a, d;
        asm volatile(   "rdtsc\n\t"
                : "=a" (a), "=d" (d)
        );
        return (d << 32) | (a & 0xffffffff);
}
#elif defined(__i386__)
static inline long long get_tsc(void)
{
        long long l;
        asm volatile(   "rdtsc\n\t"
                : "=A" (l)
        );
        return l;
}
#elif defined(__POWERPC__) 
//FIXME check ppc64
static inline uint64_t get_tsc(void)
{
    uint32_t tbu, tbl, temp;

     /* from section 2.2.1 of the 32-bit PowerPC PEM */
     __asm__ __volatile__(
         "1:\n"
         "mftbu  %2\n"
         "mftb   %0\n"
         "mftbu  %1\n"
         "cmpw   %2,%1\n"
         "bne    1b\n"
     : "=r"(tbl), "=r"(tbu), "=r"(temp)
     :
     : "cc");

     return (((uint64_t)tbu)<<32) | (uint64_t)tbl;
}
#else

#error "No get_tsc available for your arch"

#endif


char* get_relative_filename(char *currentDirectory, char *absoluteFilename);

#endif
