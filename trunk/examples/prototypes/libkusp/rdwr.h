/**
 * @file
 */

#ifndef __RDWR_H__
#define __RDWR_H__

#include <pthread.h>

typedef struct rdwr_var {
  int readers_reading;
  int writer_writing;
  pthread_mutex_t mutex;
  pthread_cond_t lock_free;
} pthread_rdwr_t;

#define PTHREAD_RDWR_INITIALIZER {0, 0, PTHREAD_MUTEX_INITIALIZER, PTHREAD_COND_INITIALIZER}

typedef void *pthread_rdwrattr_t;

#define pthread_rdwrattr_default NULL

int pthread_rdwr_init_np(pthread_rdwr_t *rdwrp, pthread_rdwrattr_t *attrp);
int pthread_rdwr_rlock_np(pthread_rdwr_t *rdwrp);
int pthread_rdwr_wlock_np(pthread_rdwr_t *rdwrp);
int pthread_rdwr_runlock_np(pthread_rdwr_t *rdwrp);
int pthread_rdwr_wunlock_np(pthread_rdwr_t *rdwrp);

#endif // RDWR_H
