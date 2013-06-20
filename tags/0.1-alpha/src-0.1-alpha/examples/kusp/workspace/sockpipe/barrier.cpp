#include "barrier.hpp"

Barrier::Barrier(unsigned int total):
	mCount(0), mTotal(total)
{
	pthread_mutex_init(&mLock, NULL);
	pthread_cond_init(&mCond, NULL);
}

void Barrier::wait()
{
	/* 
	 * Block until all threads have started. 
	 * If this is the last thread to start then notify
	 * everyone that we are ready to go.
	 */
	pthread_mutex_lock(&mLock);
	++mCount;
	if(mCount < mTotal) {
		pthread_cond_wait(&mCond, &mLock);
	} else {
		pthread_cond_broadcast(&mCond);
	}
	pthread_mutex_unlock(&mLock);

}
