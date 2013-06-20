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

main()
{
   int recv_sock;
   struct sockaddr_in my_addr;
   struct mpgd_param param;
   char buf[1024];
   int gfd;

   gfd = grp_open();
   if (gfd < 0) {
     perror("grp_open");
     return gfd;
   }

   my_addr.sin_family = AF_INET;
   my_addr.sin_port = htons(PORT);
   my_addr.sin_addr.s_addr = inet_addr(ADDRESS);
   memset(my_addr.sin_zero, '\0', sizeof my_addr.sin_zero);

   grp_create_group(gfd, "mpgd", "sdf_mpgd");
   grp_pid_join_group(gfd, "mpgd", getpid(), "mpgd-recv");

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

   grp_leave_group(gfd, "mpgd", "mpgd-recv");
   grp_destroy_group(gfd, "mpgd");
   close(gfd);
}
