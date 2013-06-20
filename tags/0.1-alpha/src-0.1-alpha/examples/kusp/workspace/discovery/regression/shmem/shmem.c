#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <getopt.h>
#include <errno.h>

#define SIZE 1024
#define START_KEY 0

pthread_mutex_t thread_mutex = PTHREAD_MUTEX_INITIALIZER;

static void *server_code (void *arg)
{
	int shmid = (int) arg;
	char *shm, *s, c;


	printf("In server\n");

	/*
	 * Attach the segment.
         */
	if ((shm = shmat(shmid, NULL, 0)) == (char *) -1) {
		printf("shmat");
	        exit(1);
        }
        
	/*
	 * Now put some things into the memory for the
	 * other process to read.
	 */
	
	s = shm;
	for (c = 'a'; c <= 'z'; c++)
		*s++ = c;
	
	*s = '\0';

	/* Detach the segment */
	if (shmdt(shm) < 0) {
		printf("server shmdt\n");
		exit(1);
	}
			
	return 0;
}

static void *client_code (void *arg)
{
	int shmid = (int) arg;
	char *shm, *s;

	printf("In client\n");

	/*
	 * Attach the segment.
         */
	if ((shm = shmat(shmid, NULL, 0)) == (char *) -1) {
		printf("shmat");
	        exit(1);
        }
        
	/*
	 * Now read what the server put in the memory
	 */

	while (*shm != 'a')
		sleep(1);

	for (s = shm; *s != '\0'; s++)
		putchar(*s);	
				       
	putchar('\n');			    	
	*shm = '*';

	/* Detach the segment */
	if (shmdt(shm) < 0) {
		printf("client shmdt\n");
		exit(1);
	}

	return 0;
}

int main(int argc, char *argv[])
{
	char c;
	int shmid, key, segs, i;
	pthread_t *threads;
	void *ret;

	segs = 1;

	while (1) {
		c = getopt(argc, argv, "s:");
		if (c == -1) {
			break;
		}
		switch (c) {
		case 's':
			segs = atoi(optarg);
			break;
		default:
			printf("Unknown option %c. \n"
			       "valid options are -s <number of segments to create>\n",
			       optopt);
			exit(1);
		}
	}

	/*
 	 * Create the segment.
	 */

	key = START_KEY;
	
	for (i = 0; i < segs; i++) {

		if ((shmid = shmget(key, SIZE, IPC_CREAT | 0666)) < 0) {
			printf("shmget");
			exit(1);
		}

		threads = malloc(sizeof(pthread_t) * 2);
		if (!threads) {
			printf("pthread malloc");
			exit(1);
		}

		printf("shmid: %d\n", shmid);

		if (pthread_create (&threads[0], NULL, server_code, (void *) shmid)) {
			fprintf(stderr, "Failed on pthread_create. %d\n", errno);
			exit(1);
		}

		if (pthread_create (&threads[1], NULL, client_code, (void *) shmid)) {
			fprintf(stderr, "Failed on pthread_create. %d\n", errno);
			exit(1);
		}

		pthread_join(threads[0], &ret);
		pthread_join(threads[1], &ret);

		//key;
	}
		
	return 0;
}


