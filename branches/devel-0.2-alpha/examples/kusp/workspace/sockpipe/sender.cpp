#include <string>
#include <cstdlib>
#include <cstdio>
#include <unistd.h>
#include <ctime>
#include <cstring>

#include <sys/socket.h>
#include <errno.h>
#include <sys/types.h>
#include <linux/unistd.h>
#include <limits.h>
#include <algorithm>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <argp.h>

#include "sender_dsui.h"
#include "message.hpp"
#include "rdist.hpp"

using namespace rdist;

static Distribution* length_dist  = NULL;
static Distribution* send_dist = NULL;
static int stimuli = 1;
static int port = 4000;
static const char* address = "127.0.0.1";
static const char* config_file = "sender.conf";

/* The options we understand. */
static struct argp_option options[] = {
	{"stimuli",    's', "1+",       0,                    "# of messages to send" },
	{"conf",       'c',  "file",     0,                    "configuration file"    },
	{ 0 }
};
          
/* Parse a single option. */
error_t parse_opt (int key, char *arg, struct argp_state *state)
{
	
	switch (key) {
	case 's':
		stimuli = atoi(arg);
		if(stimuli <= 0) {
			argp_error(state, "Stimuli must be > 0");
		}
		break;
	case 'c':
		config_file = arg;
		break;
	default:
		return ARGP_ERR_UNKNOWN;
	}

	return 0;
}
     
/* Our argp parser. */
static struct argp argp = 
{ 
	options, 
	parse_opt,
	0,
	"sender -- create a client to send messages to a pipeline",
};

/* 
 * Randomly construct a message to send down the pipeline. 
 * meg: a message structure to store the message in
 * rand_dist_length: a random distribution to generate the length of the message
 *
 */
void build_message(struct Message& msg)
{
	using std::max;

	msg.payload_len = ((int)length_dist->generate()) % MAX_PAYLOAD;

	/* Make it a multiple of 3 */
	msg.payload_len -= msg.payload_len % 3;

	/* Check lower bound */
	msg.payload_len = max(msg.payload_len, 3);

	for(int i = 0;i < msg.payload_len;++i)
	{
		msg.payload[i] = rand() % CHAR_MAX;
	}

}

using namespace cfgu;

int main(int argc, char** argv)
{
	int count;
	int ret;
	struct Message msg;
	struct timespec send_pause = { 0, 0};
	int out_fd;
	struct sockaddr_in addr;

	DSUI_BEGIN(&argc, &argv);

	argp_parse (&argp, argc, argv, 0, 0, 0);

	Config cfgu;

	cfgu.load(config_file);

	length_dist = rdist::config(cfgu.get("length_dist").obj());

	send_dist = rdist::config(cfgu.get("send_dist").obj());

	port = cfgu.get("port").real();

	address = cfgu.get("address").str();

	addr.sin_family = AF_INET;
	addr.sin_port = htons(port);
	addr.sin_addr.s_addr = inet_addr(address);
	memset(addr.sin_zero, '\0', sizeof addr.sin_zero);

	if ((out_fd = socket(PF_INET, SOCK_STREAM, 0)) == -1) {
		perror("socket");
		exit(1);
	}

	/* Keep trying until the catcher comes online. */
	while (connect(out_fd, (struct sockaddr *)&addr, sizeof (addr))) {
		sleep(1);
	}

	printf("sender connected to %d\n", port);

	count = stimuli;

	while (count > 0) {
				
		build_message(msg);

		/* Send the message to the first thread in the pipeline */
		ret = send(out_fd, &msg, msg.size(), 0);		
		
		send_pause.tv_nsec = send_dist->generate() * 1000000;

		DSTRM_EVENT(SENDER, MESSAGE, count);
		nanosleep(&send_pause, NULL);

		--count;
	}

	close(out_fd);
	
	delete length_dist;
	delete send_dist;

	DSUI_CLEANUP();

	printf("sender to port %d exiting\n", port);
	return 0;
}
