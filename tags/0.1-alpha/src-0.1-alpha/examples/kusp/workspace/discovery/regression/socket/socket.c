#include <getopt.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>

#define BUFFER_SIZE 100

const char* message = "This is a message that is used for testing discovery.";

struct fds
{
  int in_fd;
  int out_fd;
};

void* thread(void* arg)
{
  char buffer[BUFFER_SIZE];
  struct fds* socket_fds = (struct fds*)arg;

  recv(socket_fds->in_fd, buffer, BUFFER_SIZE, 0);

  printf("%s\n", buffer);

  send(socket_fds->out_fd, buffer, strlen(buffer) + 1, 0);

  return 0;
}

int main(int argc, char** argv)
{
  char c;
  int threads;
  pthread_t* thread_ids;
  struct fds* thread_fds;
  void* thread_ret;
  int out_fd;
  int fds[2];
  int i;

  // 1 thread by default
  threads = 1;

  while (1) {
    c = getopt(argc, argv, "t:");
    if (c == -1) {
      break;
    }
    switch (c) {
    case 't':
      threads = atoi(optarg);
      
      if(threads < 1) {
	printf("There must be at least 1 thread.\n");
	exit(1);
      }
      break;
    default:
      printf("Unknown option %c. \n"
	     "valid options are -l <length of pipeline>\n",
	     optopt);
      exit(1);
    }
  }

  // Create storage for thread ids.
  thread_ids = malloc(sizeof(pthread_t) * threads);
  // Create storage for thread fds.
  thread_fds = malloc(sizeof(struct fds) * threads);

  if(socketpair(AF_UNIX, SOCK_DGRAM, 0, fds) < 0) {
    perror("socketpair");
    exit(1);
  }

  out_fd = fds[0];

  thread_fds[0].in_fd = fds[1];

  // Create the sockets.
  for(i = 1;i < threads;++i) {
    if(socketpair(AF_UNIX, SOCK_DGRAM, 0, fds) < 0) {
      perror("socketpair");
      exit(1);
    }

    thread_fds[i - 1].out_fd = fds[0];
    thread_fds[i].in_fd = fds[1];
  }

  thread_fds[threads - 1].out_fd = -1;

  printf("Starting threads...\n");

  // Create the threads.
  for(i = 0;i < threads;++i) {
    pthread_create(&thread_ids[i], NULL, thread, (void*)(&thread_fds[i]));
  }

  send(out_fd, message, strlen(message) + 1, 0);

  close(out_fd);

  // Wait for threads.
  for(i = 0;i < threads;++i) {
    pthread_join(thread_ids[i], &thread_ret);
    close(thread_fds[i].in_fd);
    close(thread_fds[i].out_fd);
  }

  printf("Pipeline complete.\n");

  free(thread_fds);
  free(thread_ids);
  return 0;
}
