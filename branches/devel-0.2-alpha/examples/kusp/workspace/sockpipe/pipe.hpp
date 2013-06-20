#ifndef PIPE_HPP
#define PIPE_HPP
#include <vector>
#include "barrier.hpp"
#include "rdist.hpp"

namespace pipeline
{

#define MAX_NAME 100

struct Thread
{
	virtual void setup() {}
	virtual void process() = 0; 

	pthread_t id;
	char name[MAX_NAME];
	Barrier* barrier;
};

struct Stage: public Thread
{
	int in_fd;
	int out_fd;
};

struct Entry: public Thread
{
	int out_fd;
};

struct Exit: public Thread
{
	int in_fd;
};

struct Pipeline
{

	Pipeline(std::vector<Stage*> s);
	~Pipeline();	

	void start();
	void wait();

	Entry* entry;
	std::vector<Stage*> stages;
	Exit* exit;
	Barrier barrier;
};

}

#endif
