#include <sys/socket.h>
#include <unistd.h>
#include <pthread.h>
#include "pipe.hpp"

namespace pipeline
{

static void* helper(void* arg) 
{
	Thread* t = (Thread*)arg;

	t->setup();
	
	t->barrier->wait();

	t->process();

	return 0;
}

Pipeline::Pipeline(std::vector<Stage*> s):
	stages(s), barrier(s.size() + 2)
{
}

Pipeline::~Pipeline()
{
	for (unsigned int i = 0;i < stages.size();++i) {
		if (stages[i])
			delete stages[i];
	}
}

void Pipeline::start()
{
	int fds[2]; // Return values for socketpair
	int in_fd;

	if (socketpair(AF_UNIX, SOCK_STREAM, 0, fds) < 0) {
		perror("socketpair");
		::exit(1);
	}
	
	entry->out_fd = fds[0];

	in_fd = fds[1];
	
	/* Create the sockets.*/
	for (unsigned int i = 0;i < stages.size();++i) {
		if (socketpair(AF_UNIX, SOCK_STREAM, 0, fds) < 0) {
			perror("socketpair");
			::exit(1);
		}
		
		stages[i]->in_fd = in_fd;
		stages[i]->out_fd = fds[0];
		in_fd = fds[1];

	}

	exit->barrier = &barrier;
	exit->in_fd = in_fd;

	printf("Starting threads...\n");

	pthread_create(&exit->id, NULL, helper, (void*)exit);
	
	/* Create the threads. */
	for (unsigned int i = 0; i < stages.size(); ++i) {
		stages[i]->barrier = &barrier;
		if (pthread_create(&stages[i]->id, NULL, helper, (void *)stages[i])) {
			fprintf(stderr, "failed creating thread");
		}
	}
	
	entry->barrier = &barrier;
	pthread_create(&entry->id, NULL, helper, (void*)entry);

	printf("Created pipeline of %d threads\n", stages.size());
	
	printf("All threads started\n");

}

void Pipeline::wait()
{
	pthread_join(entry->id, NULL);
	close(entry->out_fd);

	/* Wait for threads. */
	for (unsigned int i = 0; i < stages.size(); ++i) {
		pthread_join(stages[i]->id, NULL);
		close(stages[i]->in_fd);
		close(stages[i]->out_fd);
	}
	
	pthread_join(exit->id, NULL);
	close(exit->in_fd);
}

}
