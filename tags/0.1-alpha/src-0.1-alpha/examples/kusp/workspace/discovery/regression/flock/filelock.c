#include <pthread.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/syscall.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <string.h>
#include <errno.h>
#include <filelock_dsui.h>
#include <unistd.h>

#define SIZE 10000
#define NOTHREADS 5


void reading();
void writing();

int main(int args, char **argv){
  
  
  DSUI_BEGIN(&args,&argv);
  
  DSTRM_EVENT(FUNC_MAIN,MAIN_THREAD,getpid());

  //pthread_t read,writ,read1,app;
  
  int fd,i=0, ret = 0;
  
  // Create or truncate.
  if ((fd=creat("result.txt", 0)) == -1){
    perror("creation error");
    exit(1);
  }
  system("chmod 0744 result.txt");
  close(fd);
  
  printf("Forking children...\n");

  for (i=0; i<NOTHREADS;i++){
  
    ret = fork();
    if(-1 == ret) {
      perror("fork");
      exit(1);
    }

    if(0 == ret) {
      if ((i%2) == 0) {
	DSTRM_EVENT(FUNC_MAIN,CREATE_THREAD_PRODUCER,i);
	writing();
      }else if ((i%2) != 0) {
	DSTRM_EVENT(FUNC_MAIN,CREATE_THREAD_CONSUMER,i);
	reading();
      }    

      return 0;
    }
  }

  DSTRM_EVENT(FUNC_MAIN,CLOSING_ALL_THREADS,getpid());

  printf("All children forked.\n");
  
  DSUI_CLEANUP();
   
  return 0;
}	


void writing(){
  
  char *jj="bala is great";
  int fd,n=0;
  
  DSTRM_EVENT(PRODUCER_THREAD,ENTER,gettid());
  
  if((fd = open("result.txt",O_RDWR)) == -1){
    perror("open error");
    exit(1);
  }
  
  flock(fd, LOCK_EX);
  // printf("inside write lock\n");
  // printf("%d\n",strlen(jj));
  // printf("%s\n",jj);
  n=write(fd,jj,strlen(jj));
  DSTRM_EVENT(PRODUCER_THREAD,WRITTEN_TO_FILE,gettid());
  // printf("%d\n",n);

  //  printf("leaving write lock\n");
  flock(fd, LOCK_UN);

  DSTRM_EVENT(PRODUCER_THREAD,EXIT,gettid());
  
  close(fd);
}

void reading(){
  
  char pp[SIZE];
  //char *kk="bala is great\n";
  
  int fd1,n=0;
  
  usleep(10000000);
  
  DSTRM_EVENT(CONSUMER_THREAD,ENTER,gettid());
  
  if((fd1 = open("result.txt",O_RDWR)) == -1){
    perror("reading open");
    exit(1);
  }

  flock(fd1, LOCK_SH);
 
  //printf("inside read lock\n");
  
  n=read(fd1,pp,sizeof(pp));
  
  //printf("reading %d\n",n);
  
  //n=write(2,pp,n);
  //write(2,"\n",strlen("\n"));
  DSTRM_EVENT(CONSUMER_THREAD,READ_FROM_FILE,gettid());
  //printf("\nconsole %d\n",n);
 
  //printf("leaving read lock\n");
  flock(fd1, LOCK_UN);
  
  DSTRM_EVENT(CONSUMER_THREAD,EXIT, gettid());
  
  close(fd1);
  
}

