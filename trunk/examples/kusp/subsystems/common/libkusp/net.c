/** @file */

#include <net.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <errno.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/wait.h>
#include <netdb.h>
#include <unistd.h>
#include <stdlib.h>
#include <kusp_common.h>
#include <misc.h>
#include <sys/ioctl.h>

/** create a TCP server listening for connections on a specified port, returning
 * a file descriptor to call server_accept() on */
int setup_server(int port)
{
	int sockfd;
	struct sockaddr_in my_addr;	// my address information
	int yes = 1;

	if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
		kusp_perror("socket");
		return -1;
	}

	if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) ==
	    -1) {
		kusp_perror("setsockopt");
		return -1;
	}



	my_addr.sin_family = AF_INET;	// host byte order
	my_addr.sin_port = htons(port);	// short, network byte order
	my_addr.sin_addr.s_addr = INADDR_ANY;	// automatically fill with my IP
	memset(&(my_addr.sin_zero), '\0', 8);	// zero the rest of the struct

	if (bind(sockfd, (struct sockaddr *)&my_addr, sizeof(struct sockaddr))
	    == -1) {
		kusp_perror("bind");
		return -1;
	}

	if (listen(sockfd, 10) == -1) {
		kusp_perror("listen");
		return -1;
	}

	dprintf("Successfully setup server - Awaiting connection on port %d\n",
		       port);
	return sockfd;

}

/** set server to be nonblocking, i.e. return immediately from accept()
 */
int set_server_nonblocking(int sockfd)
{
	int one = 1;
	return ioctl(sockfd, FIONBIO, (char *)&one);
}

/**
 * Accept a connection. If the file descriptor has no pending connections, this
 * function will either block or return NULL depending on whether the socket is nonblocking.
 *
 * if successful, allocates and returns a kusp_netconn struct */
struct kusp_netconn *server_accept(int sockfd)
{
	struct kusp_netconn *c = malloc(sizeof(*c));
	struct sockaddr *sptr = (struct sockaddr *)(&c->client_addr);
	struct hostent *he;
	int connfd;

	socklen_t sin_size = sizeof(c->client_addr);
	connfd = accept(sockfd, sptr, &sin_size);

	if (connfd < 0) {
		if (errno != EAGAIN) {
			kusp_perror("accept");
		}
		return NULL;
	}
	he = gethostbyaddr(&(c->client_addr.sin_addr),
			sizeof(c->client_addr.sin_addr), AF_INET);
	if (!he) {
		kusp_perror("gethostbyaddr");
		c->clientname = strdup("unknown");
	} else {
		dprintf("connection from %s\n", he->h_name);
		c->clientname = strdup(he->h_name);
	}
	c->fd = connfd;

	return c;
}

/** connect to a TCP server, returning a file descriptor to read and write data */
int setup_client(const char *server_hostname, unsigned short int port)
{
	int error = 1;

	int sockfd;

	struct hostent *their;
	struct sockaddr_in their_addr;	// connector's address information

	iprintf("Attempting to connect to %s:%d...\n",
		server_hostname, port);

	their = gethostbyname(server_hostname);
	if (their == NULL) {
		eprintf("Lookup of %s failed: %s\n",
			server_hostname, strerror(errno));
		return -1;
	}

	/* create the socket for connection */
	sockfd = socket(AF_INET, SOCK_STREAM, 0);
	if (sockfd == -1) {
		eprintf("Failed to setup client socket: %s\n",
			strerror(errno));
		return -1;
	}

	their_addr.sin_family = AF_INET;
	their_addr.sin_port = htons(port);
	their_addr.sin_addr = *((struct in_addr *)their->h_addr);
	memset(&(their_addr.sin_zero), '\0', 8);

	while (error != 0) {
		error = connect(sockfd,
			(struct sockaddr *)&their_addr,
			sizeof(struct sockaddr));
		if (error < 0) {
			error = errno;
			if (error != ECONNREFUSED) {
				eprintf("Failed to connect to %s:%d: %s\n",
					server_hostname, port, strerror(errno));
				return -1;
			}
			wprintf("Connection refused from %s, trying again in 3 seconds.\n",
					server_hostname);
			sleep(3);
		}
	}

	iprintf("Successfully connected.\n");

	return sockfd;
}
