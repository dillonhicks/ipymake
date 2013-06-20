#define _GNU_SOURCE
#include <stdio.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <stdlib.h>
#include <netinet/in.h> //htons, sockaddr
#include <string.h> //memset

#define DATA2 "More more more more yayayaya more more more more more more more more...."

#define PORT 4000
#define ADDRESS "127.0.0.1"
#define BACKLOG 1

main()
{
   int server_sock, send_sock;
   struct sockaddr_in my_addr;
   char buf[1024];
   int yes = 1;

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

   send_sock = accept(server_sock, 0, 0);

   // The other side has already been registered. Don't need to sleep.
   
   if (send(send_sock, DATA2, sizeof(DATA2), 0) < 0)
     perror("writing stream message");

   close(send_sock);
   close(server_sock);
}
