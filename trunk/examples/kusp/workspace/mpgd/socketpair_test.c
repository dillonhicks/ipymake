#define _GNU_SOURCE
#include <stdio.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <stdlib.h>
#include <string.h>

#include <sched_gsched.h>
#include <linux/gsched_sdf_mpgd.h>

#define DATA2 "More more more more yayayaya...."

main()
{
   int sockets[2], child;
   struct mpgd_param param;
   char buf[1024];
   struct mpgd_event_header header;
   int gfd;

   gfd = grp_open();
   if (gfd < 0) {
      perror("grp_open");
      return gfd;
   }

   if (socketpair(AF_UNIX, SOCK_DGRAM, 0, sockets) < 0) {
      perror("opening stream socket pair");
      exit(1);
   }

   grp_create_group(gfd, "mpgd", "sdf_mpgd");
   grp_pid_join_group(gfd, "mpgd", getpid(), "mpgd-recv");

   child = fork();
  
   if (child == -1)
      perror("fork");

   else if (child) {
     
      param.cmd = MPGD_CMD_ADD_PORT;
      param.port.type = MPGD_PORT_SOCK;
      param.port.fd = sockets[0];
      grp_set_member_parameters(gfd, "mpgd", "mpgd-recv", &param, sizeof(param));

      if (read(sockets[0], buf, 1024) < 0)
         perror("reading stream message");

      printf("-->%s\n", buf+sizeof(header));

   } else {

	sleep(2);

	header.magic = MPGD_MAGIC_NUM;
	header.timestamp.tv_sec = 1234;
	header.timestamp.tv_nsec = 78901;

	memset(buf, 0, sizeof(buf));
	memcpy(buf, &header, sizeof(header));
	memcpy(buf+sizeof(header), DATA2, sizeof(DATA2));

      if (write(sockets[1], buf, sizeof(buf)) < 0)
         perror("writing stream message");

   }

   /* is: if parent */
   if (child) {
   	grp_leave_group(gfd, "mpgd", "mpgd-recv");
   	grp_destroy_group(gfd, "mpgd");
   	close(gfd);
   }
}
