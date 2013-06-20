#ifndef KUSP_MUTEX_H
#define KUSP_MUTEX_H

#include <kusp_common.h>
#include <pthread.h>
#include <rdwr.h>




#define km_rdwr_wlock(mutex)   	{ int retval; \
	if ((retval = pthread_rdwr_wlock_np((mutex)))) \
		kusp_errno("pthread_rdwr_wlock", retval); }
#define km_rdwr_wunlock(mutex) 	{ int retval; \
	if ((retval = pthread_rdwr_wunlock_np((mutex)))) \
	      kusp_errno("pthread_rdwr_wunlock", retval); }
#define km_rdwr_rlock(mutex)   	{ int retval; \
	if ((retval = pthread_rdwr_rlock_np((mutex)))) \
	      kusp_errno("pthread_rdwr_rlock", retval); }
#define km_rdwr_runlock(mutex) 	{ int retval; \
	if ((retval = pthread_rdwr_runlock_np((mutex)))) \
	      kusp_errno("pthread_rdwr_runlock", retval); }
#define km_rdwr_init(mutex, arg)	{ int retval; \
	if ((retval = pthread_rdwr_init_np((mutex), (arg)))) \
	      kusp_errno("pthread_rdwr_init_np", retval); }

#define km_mutex_lock(mutex)   	{ int retval; \
	if ((retval = pthread_mutex_lock((mutex)))) \
		kusp_errno("pthread_mutex_lock", retval); }
#define km_mutex_unlock(mutex) 	{ int retval; \
	if ((retval = pthread_mutex_unlock((mutex)))) \
	      kusp_errno("pthread_mutex_unlock", retval); }
#define km_mutex_init(mutex, arg)   	{ int retval; \
	if ((retval = pthread_mutex_init((mutex), (arg)))) \
	      kusp_errno("pthread_mutex_init", retval); }


#define km_cond_init(cond, attr) 	{ int retval; \
	if ((retval = pthread_cond_init((cond), (attr)))) \
	      kusp_errno("pthread_cond init", retval); }
#define km_cond_wait(cond, mutex)	{ int retval; \
	if ((retval = pthread_cond_wait((cond), (mutex)))) \
	      kusp_errno("pthread_cond wait", retval); }
#define km_cond_broadcast(cond) 	{ int retval; \
	if ((retval = pthread_cond_broadcast((cond)))) \
	      kusp_errno("pthread_cond_broadcast", retval); }
#define km_cond_signal(cond)		{ int retval; \
	if ((retval = pthread_cond_signal((cond)))) \
	      kusp_errno("pthread_cond_signal", retval); }




#endif
