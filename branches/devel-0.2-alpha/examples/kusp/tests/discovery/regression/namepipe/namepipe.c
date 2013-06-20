#include <pthread.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/syscall.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#ifdef CONFIG_DSUI
#include <namepipe_dsui.h>
#endif

/*
 * This is the namepipe experiment. Based off command line
 * arguments, it creates a number of named pipes to do a
 * number of write / read transfers on. Each pipe is assigned
 * a pair of threads. One thread writes into the pipe, and the
 * other simply reads from it. 
 */

/*
 * TODO: Update the instrumentation in here.
 * TODO: Extend this so we can have a pipeline
 * of threads reading / writing on the same
 * named pipe
 */

#define MESSAGE "I am iron man"

void *producer ();
void *consumer ();

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
int *pipeClean;
int num_pairs, num_transfers;

struct thread_data {
	char pipeName[20];
	int pairNum;
};

int main(int argc, char **argv) {

	int i, t1, t2, num_threads;
	char namebuf[20], numbuf[10], c;
	static pthread_t *threads;
	struct thread_data *thread_args;
	void *ret;

#ifdef CONFIG_DSUI
	DSUI_BEGIN(&argc, &argv);
	DSTRM_EVENT(FUNC_MAIN,MAIN_THREAD,getpid());
#endif

	num_pairs = num_transfers = 0;
	while (1) {
		c = getopt(argc, argv, "p:t:");
		if (c == -1) {
			break;
		}
		switch (c) {
		case 'p':
			num_pairs = atoi(optarg);
			break;
		case 't':
			num_transfers = atoi(optarg);
			break;
		default:
			printf("Unknown option %c. Valid options are:\n"
			       "-p <number of pairs of named pipes to create>\n"
			       "-t <number of transfers to make for each thread pair>\n",
				optopt);
			exit(1);
		}
	}
	
	if (!num_pairs || !num_transfers) {
		printf("You must specify how many pipes and transfers on each pipe are to be made.\n"
				"namepipe -p [NUM_PIPES] -t [NUM_TRANSFERS]\n");
	}
	
	num_threads = 2 * num_pairs;
	threads = malloc(sizeof(pthread_t) * num_threads);
	
	if (!threads){
		fprintf(stderr, "can't initialise threads\n");
		exit(1);
	}
	
	pipeClean = malloc(sizeof(int) * num_pairs);
	if (!pipeClean) {
		fprintf(stderr, "can't initialize pipeClean\n");
		exit(1);
	}

	for (i=0; i<num_pairs; i++) {
        
		/* Map i to thread indexes*/
		t2 = (i*2)+1;
		t1 = t2-1;

		thread_args = malloc(sizeof(struct thread_data));

		/* Create unique name for the pipe */
		sprintf(numbuf, "%d", i);
		strcat(strcpy(namebuf, "name.out."), numbuf);
		strcpy(thread_args->pipeName, namebuf);
		
		/* pairNum used for concurrency control between pairs of threads */
		thread_args->pairNum = i;
		
		/* Create named pipe */
		if (mkfifo(namebuf,0666) < 0) {
			fprintf(stderr, "creation of named pipe %s failed. Exiting...\n", namebuf);
			exit(1);
		}
	
		/*
		 * Set pipeClean so we always start with the
		 * writer thread
		 */
		pipeClean[i] = 1;
				
		/* Create the threads */
#ifdef CONFIG_DSUI
		DSTRM_EVENT(FUNC_MAIN,CREATE_THREAD_PRODUCER,i);
#endif
	        if (pthread_create(&threads[t1],NULL,producer,(void *) thread_args)){
	        	fprintf(stderr, "failed creating writing thread");
        		exit(1);
        	}

#ifdef CONFIG_DSUI
		DSTRM_EVENT(FUNC_MAIN,CREATE_THREAD_CONSUMER,i);
#endif
        	if (pthread_create(&threads[t2],NULL,consumer,(void *) thread_args)){
        		fprintf(stderr, "failed creating reading thread");
			exit(1);
        	}
	}

	/* Wait for all threads to finish */
	for (i=0; i<num_threads; i++) {
		pthread_join(threads[i], &ret);
	}

	/* Delete named pipes so future runs don't error out */
	if (num_threads)
		system("rm -f name.out.*");

#ifdef CONFIG_DSUI
        DSTRM_EVENT(FUNC_MAIN,CLOSING_ALL_THREADS,getpid());
        DSUI_CLEANUP();
#endif

        return 0;
}

 
void *producer(void *thread_args) {

	int fd,i,size;
	struct thread_data *data = (struct thread_data *) thread_args;

#ifdef CONFIG_DSUI
	DSTRM_EVENT(PRODUCER_THREAD,ENTER,0);	
#endif
	if ((fd=open(data->pipeName,O_RDWR)) < 0){
		fprintf(stderr, "opening named pipe for writing failed");
		exit(1);
	}

	printf("producer for pipename %s will now write %d \"%s\" messages to the pipe\n", data->pipeName, num_transfers, MESSAGE);
	
	for (i=0;i<num_transfers;){

		pthread_mutex_lock(&mutex);
		if (pipeClean[data->pairNum]) {	
	
			if ((size=write(fd,MESSAGE,strlen(MESSAGE))) < 0){
				fprintf(stderr, "writing to the named pipe failed");
				exit(1);
			}

			pipeClean[data->pairNum] = 0;
			i++;

#ifdef CONFIG_DSUI
			DSTRM_EVENT_DATA(PRODUCER_THREAD, WRITTEN_TO_PIPE, 0,
					size, MESSAGE, "print_string");
#endif
		}
		pthread_mutex_unlock(&mutex);
	}

	printf("producer for pair %d is done\n", data->pairNum);

#ifdef CONFIG_DSUI
	DSTRM_EVENT(PRODUCER_THREAD,EXIT,0);
#endif
	close(fd);
	return NULL;
}

void *consumer(void *thread_args) {

	int fd,i,size;
	struct thread_data *data = (struct thread_data *) thread_args;
	char buf[strlen(MESSAGE)];

#ifdef CONFIG_DSUI
	DSTRM_EVENT(CONSUMER_THREAD,ENTER,0);
#endif
	if ((fd=open(data->pipeName,O_RDWR)) < 0) {
		fprintf(stderr, "opening named pipe for reading failed");
		exit(1);
	}

	printf("consumer for pipename %s starting\n", data->pipeName);
		
	for(i=0;i<num_transfers;) {

		pthread_mutex_lock(&mutex);
		if (!pipeClean[data->pairNum]) {
			
			if ((size=read(fd,buf,strlen(MESSAGE))) < 0) {
				fprintf(stderr, "reading from the named pipe failed");
				exit(1);
			}
			
			pipeClean[data->pairNum] = 1;
			i++;

#ifdef CONFIG_DSUI
			DSTRM_EVENT_DATA(CONSUMER_THREAD, READ_FROM_PIPE, 0,
					size, buf, "print_string");
#endif
		}
		pthread_mutex_unlock(&mutex);
	}

	printf("consumer for pair %d is done\n", data->pairNum);
	close(fd);
#ifdef CONFIG_DSUI
	DSTRM_EVENT(CONSUMER_THREAD,EXIT,0);
#endif
	free(data);
	return NULL;
}
