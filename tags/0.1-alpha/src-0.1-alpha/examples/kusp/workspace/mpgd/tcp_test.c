#define _GNU_SOURCE
#include <stdio.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <stdlib.h>
#include <netinet/in.h> //htons, sockaddr
#include <string.h> //memset

#include <sched_gsched.h>
#include <linux/gsched_sdf_mpgd.h>

#define DATA2 "More more more more yayayaya more more more more more more more more...."

#define PORT 4000
#define ADDRESS "127.0.0.1"
#define BACKLOG 1

main()
{
   int server_sock, send_sock, recv_sock;
   struct sockaddr_in my_addr;
   int child;
   struct mpgd_param param;
   char buf[1024];
   int gfd;
   int yes = 1;

   gfd = grp_open();
   if (gfd < 0) {
     perror("grp_open");
     return gfd;
   }

   server_sock = socket(PF_INET, SOCK_STREAM, 0);

   setsockopt(server_sock, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int));

   my_addr.sin_family = AF_INET;
   my_addr.sin_port = htons(PORT);
   my_addr.sin_addr.s_addr = inet_addr(ADDRESS);
   memset(my_addr.sin_zero, '\0', sizeof my_addr.sin_zero);

   if(bind(server_sock, (struct sockaddr *)&my_addr, sizeof my_addr)) {
     perror("address in use");
     exit(1);
   }

   if(listen(server_sock, BACKLOG)) {
     perror("couldn't start listening");
     exit(1);
   }

   grp_create_group(gfd, "mpgd", "sdf_mpgd");
   grp_pid_join_group(gfd, "mpgd", getpid(), "mpgd-recv");

   child = fork();
  
   if (child == -1)
     perror("fork");

   else if (child) {
     
     close(server_sock);

     recv_sock = socket(PF_INET, SOCK_STREAM, 0);

     param.cmd = MPGD_CMD_ADD_PORT;
     param.port.type = MPGD_PORT_SOCK;
     param.port.fd = recv_sock;
     grp_set_member_parameters(gfd, "mpgd", "mpgd-recv", &param, sizeof(param));

     if(connect(recv_sock, (struct sockaddr *)&my_addr, sizeof my_addr)) {
       perror("failed to contact sender");
       exit(1);
     }

     if (recv(recv_sock, buf, 1024, 0) < 0)
       perror("reading stream message");
     
     printf("-->%s\n", buf);

     close(recv_sock);

   } else {

     send_sock = accept(server_sock, 0, 0);

     // The other side has already been registered. Don't need to sleep.

     if (send(send_sock, DATA2, sizeof(DATA2), 0) < 0)
       perror("writing stream message");

     close(send_sock);
     close(server_sock);
   }

   /* is: if parent */
   if (child) {
     sleep(2);

   	grp_leave_group(gfd, "mpgd", "mpgd-recv");
   	grp_destroy_group(gfd, "mpgd");
   	close(gfd);
   }
}
