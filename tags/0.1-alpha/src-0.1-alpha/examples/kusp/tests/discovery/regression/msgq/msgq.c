#include <getopt.h>
#include <mqueue.h>
#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>

#define BUFFER_SIZE 100

char const* const message = "This is a message that is used for testing discovery.";

// This is constant after the progrm arguments are parsed.
// No CC is needed.
int threads = 1;

// If security is not enabled then the maximum number of messages
// in ANY queue is really low(10 for my kernel).
struct mq_attr attr = {
  .mq_maxmsg = 8,
  .mq_msgsize = BUFFER_SIZE,
  .mq_flags = 0
};

mqd_t outq_open(int thread, char* buffer)
{
  mqd_t mqd;

  sprintf(buffer, "/queue-%d", thread);

  mqd = mq_open (buffer, O_WRONLY | O_CREAT, 
                    0664, &attr);

  if(mqd < 0) {
    perror("out queue open");
    exit(1);
  }

  return mqd;
}

mqd_t inq_open(int thread, char* buffer)
{
  mqd_t mqd;

  sprintf(buffer, "/queue-%d", thread - 1);

  mqd = mq_open (buffer, O_RDONLY | O_CREAT,
		 0664, &attr);

  if(mqd < 0) {
    perror("in queue open");
    exit(1);
  }

  return mqd;
}

void* thread(void* arg)
{
  char buffer[BUFFER_SIZE];
  char inq_name[BUFFER_SIZE];
  char outq_name[BUFFER_SIZE];
  mqd_t inq;
  mqd_t outq;
  const int thread = (int)arg;
  int ret;
  struct mq_attr attr;

  inq = inq_open(thread, inq_name);

  mq_getattr(inq, &attr);

  printf("%s: maxmsg=%ld msgsize=%ld\n", inq_name, attr.mq_maxmsg, attr.mq_msgsize);

  ret = mq_receive(inq, buffer, BUFFER_SIZE, NULL);
  if(ret < 0) {
    perror("mq_receive");
    exit(1);
  }
  mq_close(inq);
  mq_unlink(inq_name);

  printf("Thread %d received %d bytes: %s\n", thread, ret, buffer);

  // Don't output if this is the last thread.
  if(thread < threads) {
    outq = outq_open(thread, outq_name);
    mq_send(outq, buffer, strlen(buffer) + 1, 0);
    mq_close(outq);
  }

  return 0;
}

int main(int argc, char** argv)
{
  char c;
  pthread_t* thread_ids;
  void* thread_ret;
  int i;
  char buffer[BUFFER_SIZE];
  mqd_t outq;

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

  printf("Starting threads...\n");

  // Create the threads.
  for(i = 0;i < threads;++i) {
    pthread_create(&thread_ids[i], NULL, thread, (void*)i + 1);
  }

  outq = outq_open(0, buffer);
  if(mq_send(outq, message, strlen(message) + 1, 0)) {
    perror("mq_send");
    exit(1);
  }
  mq_close(outq);

  // Wait for threads.
  for(i = 0;i < threads;++i) {
    pthread_join(thread_ids[i], &thread_ret);
  }

  printf("Pipeline complete.\n");

  free(thread_ids);
  return 0;
}
