#ifndef BARRIER_HPP
#define BARRIER_HPP
#include <pthread.h>

class Barrier
{
public:
	Barrier(unsigned int total = 0);
	void wait();
private:
	pthread_mutex_t	mLock;    
	pthread_cond_t mCond;
	unsigned int mCount;
	const unsigned int mTotal;
};

#endif
