#ifndef _KUSP_NET_H_
#define _KUSP_NET_H_
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/wait.h>

struct kusp_netconn {
	int fd;
	char *clientname;
	struct sockaddr_in client_addr;
};



int setup_server(int port);
int set_server_nonblocking(int sockfd);
struct kusp_netconn *server_accept(int sockfd);

int setup_client(const char *server_hostname, 
		unsigned short int port);


#endif
