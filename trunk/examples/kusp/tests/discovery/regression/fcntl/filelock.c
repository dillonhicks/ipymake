#include <pthread.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/syscall.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <errno.h>
#include <filelock_dsui.h>


#define SIZE 10000
#define NOTHREADS 5


void *reading();
void *writing();
void *appending();



int main(int args, char **argv){
  
  
  DSUI_BEGIN(&args,&argv);
  
  DSTRM_EVENT(FUNC_MAIN,MAIN_THREAD,getpid());
  
  //pthread_t read,writ,read1,app;
  
  int fd,i=0;
  
  if ((fd=open("result.txt",O_CREAT)) == -1){
    perror("creation error");
    exit(1);
  }
  system("chmod 0744 result.txt");
  close(fd);
  
  static pthread_t *threads;
  
  
  
  threads = malloc(sizeof(pthread_t) * NOTHREADS);
  if (!threads){
    perror("can't initialise threads\n");
    exit(1);
  }
  
  for (i=0; i<NOTHREADS;i++){
    
    if ((i%2) == 0) {
      if (pthread_create(&threads[i],NULL,writing,NULL)){
	perror("failed creating writing thread");
	exit(1);
      }
      DSTRM_EVENT(FUNC_MAIN,CREATE_THREAD_PRODUCER,i);
    }else if ((i%2) != 0) {
      if (pthread_create(&threads[i],NULL,reading,NULL)){
	perror("failed creating reading thread");
	exit(1);
      }
      DSTRM_EVENT(FUNC_MAIN,CREATE_THREAD_CONSUMER,i);
    }
    
    
  }
  printf("closing all the threads\n");
  
  for(i=0;i<NOTHREADS;i++) {
    
    pthread_join(threads[i],NULL);
    
  }
  
  /*DSTRM_EVENT(FUNC_MAIN,CREATE_THREAD_PRODUCER,1);
    
    pthread_create(&writ,NULL,writing,NULL);
    
    DSTRM_EVENT(FUNC_MAIN,CREATE_THREAD_CONSUMER,1);
    
    pthread_create(&read,NULL,reading,NULL);
    
    //pthread_create(&writ,NULL,writing,NULL);
    
    DSTRM_EVENT(FUNC_MAIN,CREATE_THREAD_APPENDER,1);
    
    pthread_create(&app,NULL,appending,NULL);
    
    DSTRM_EVENT(FUNC_MAIN,CREATE_THREAD_CONSUMER,2);
    
    pthread_create(&read1,NULL,reading,NULL);
    
    pthread_join(writ,NULL);
    
    pthread_join(read,NULL);
    
    //pthread_join(writ,NULL);
    
    pthread_join(app,NULL);
    
    pthread_join(read1,NULL);*/
  
  DSTRM_EVENT(FUNC_MAIN,CLOSING_ALL_THREADS,getpid());
  
  DSUI_CLEANUP();
  
  system("rm -f result.txt");
  
  
  return 0;
}	


void *writing(){
  
  char *jj="bala is great";
  int fd,n=0;
  
  struct flock fl;
  
  fl.l_type=F_WRLCK;
  fl.l_whence=SEEK_SET;
  fl.l_start =0;
  fl.l_len = 0;
  fl.l_pid = syscall(SYS_gettid);
  
  DSTRM_EVENT(PRODUCER_THREAD,ENTER,fl.l_pid);
  
  if((fd = open("result.txt",O_RDWR)) == -1){
    perror("open error");
    exit(1);
  }
  
  fcntl(fd,F_SETLKW,&fl);
  // printf("inside write lock\n");
  // printf("%d\n",strlen(jj));
  // printf("%s\n",jj);
  n=write(fd,jj,strlen(jj));
  DSTRM_EVENT(PRODUCER_THREAD,WRITTEN_TO_FILE,fl.l_pid);
  // printf("%d\n",n);
  fl.l_type=F_UNLCK;
  //  printf("leaving write lock\n");
  fcntl(fd,F_SETLK,&fl);

  DSTRM_EVENT(PRODUCER_THREAD,EXIT,fl.l_pid);
  
  close(fd);
}

void *reading(){
  
  char pp[SIZE];
  //char *kk="bala is great\n";
  
  int fd1,n=0;
  
  struct flock flr;

  flr.l_type=F_RDLCK;
  flr.l_whence=SEEK_SET;
  flr.l_start = 0;
  flr.l_len = 0;
  flr.l_pid = syscall(SYS_gettid);
  
  
  usleep(10000000);
  
  DSTRM_EVENT(CONSUMER_THREAD,ENTER,flr.l_pid);
  
  if((fd1 = open("result.txt",O_RDWR)) == -1){
    perror("reading open");
    exit(1);
  }

  fcntl(fd1,F_SETLKW,&flr);
 
  //printf("inside read lock\n");
  
  n=read(fd1,pp,sizeof(pp));
  
  //printf("reading %d\n",n);
  
  //n=write(2,pp,n);
  //write(2,"\n",strlen("\n"));
  DSTRM_EVENT(CONSUMER_THREAD,READ_FROM_FILE,flr.l_pid);
  //printf("\nconsole %d\n",n);
  flr.l_type=F_UNLCK;
  //printf("leaving read lock\n");
  fcntl(fd1,F_SETLK,&flr);
  
  DSTRM_EVENT(CONSUMER_THREAD,EXIT,flr.l_pid);
  
  close(fd1);
  
}

void *appending(){
  
  char *kk="body soda is doing virtual machines";
  
  int fd2,n=0,l=0;
  
  struct flock fla;
  
  fla.l_type=F_WRLCK;
  fla.l_whence=SEEK_SET;
  fla.l_start=0;
  fla.l_len=0;
  fla.l_pid=syscall(SYS_gettid);
  
  usleep(10000000);
  
  DSTRM_EVENT(APPENDER_THREAD,ENTER,fla.l_pid);
  
  if ((fd2=open("result.txt",O_RDWR)) == -1) {
    perror("appending error");
    exit(1);
  }
  
  fcntl(fd2,F_SETLKW,&fla);
  //printf("inside append lock\n");
  //printf("%s\n",kk);
  //printf("%d\n",strlen(kk));
  l=lseek(fd2,1,SEEK_END);
  //printf("%d\n",l);
  
  if((n=write(fd2,kk,strlen(kk)))== -1){
    perror("append write error");
    printf("%c\n",errno);
    exit(1);
  }
  
  DSTRM_EVENT(APPENDER_THREAD,WRITTEN_TO_FILE,fla.l_pid);
  //printf("%d\n",n);
  
  fla.l_type=F_UNLCK;
  //printf("leaving append lock\n");
  fcntl(fd2,F_SETLK,&fla);
  
  DSTRM_EVENT(APPENDER_THREAD,EXIT,fla.l_pid);
  
  close(fd2);

  
  
}

