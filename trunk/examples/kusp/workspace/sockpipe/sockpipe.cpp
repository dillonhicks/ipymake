#include <cstdlib>
#include <cstdio>
#include <unistd.h>
#include <cstring>

#include <sys/socket.h>
#include <sched.h>
#include <pthread.h>
#include <errno.h>
#include <sys/types.h>
#include <linux/unistd.h>
#include <sched_gsched.h>
#include <ccsm.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <argp.h>
#include <sched_gsched.h>

#include "rdist.hpp"
#include "pipe.hpp"
#include "message.hpp"
#include "sockpipe_dsui.h"

using namespace rdist;
using namespace pipeline;

/* Routine to fetch the thread idea of pthread */
#define gettid() syscall(__NR_gettid)

int			 stimuli              = 1; /* number of messages to send: constant */
int			 use_ccsm	      = 0;
int			 ccsm_fd	      = -1;
int                      port                 = 4000;
const char*              pipe_name            = NULL;
const char*              config_file          = "pipe.conf";
int                      use_gs               = 0;
int                      grp_fd               = -1;
               
/* The options we understand. */
static struct argp_option options[] = {
	{"conf",        'c',  "file",     0,  "configuration file"    },
	{ 0 }
};
          
/* Parse a single option. */
error_t parse_opt (int key, char *arg, struct argp_state *state)
{
	
	switch (key) {
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
        "sockpipe -- create a pipeline of multiple threads linked by unix sockets",
};
     
void shift(struct Message& m)
{

	for(int i = 0;i < m.payload_len;++i) {
		
		if(m.payload[i] > 240) {
			m.payload[i] -= 10;
		}
		if(m.payload[i] < 20) {
			m.payload[i] += 15;
		}
		if(m.payload[i] > 100 && m.payload[i] < 200) {
			m.payload[i] += 3;
		}
	}

}

struct Worker: public Stage
{
	void setup();
	void process();
	int order;
	int prio;
	Distribution* work_dist;
};

void Worker::setup()
{
	int tid = gettid();

	printf("%s started %s(%d)\n", pipe_name, name, tid);

	if(use_ccsm) {
		printf("Creating component for %s\n", name);
		ccsm_create_component_self(ccsm_fd, name);
		printf("Adding %s to set %s\n", name, pipe_name);
		if (ccsm_add_member(ccsm_fd, pipe_name, name)) {
			perror("ccsm_add_member");
			exit(1);
		}
	}	
}

void Worker::process()
{
	struct Message          msg; // Buffer to store a message in.
	int			count = 0;
	unsigned int		unique_id;
	int                     work_units;
	
	while (1) {
		if (msg.read(in_fd) <= 0) {
			/* 
			 * Received interrupt signal while receiving
			 * or the other end was closed.
			 * We must be done.
			 */
			break;
		}

		++count;

		unique_id = order;
		unique_id <<= 27;
		unique_id |= count;
		
		DSTRM_EVENT(GAP_TEST, SIG_RCVD, unique_id);

		work_units = work_dist->generate();

		while(work_units > 0) {
			shift(msg);
			--work_units;
		}

		/* Progress report */		
		if (count % 5 == 0)
			printf("%s %s has processed %d messages\n",
			       pipe_name, name, count);

		gsched_set_member_param_int(grp_fd, "bp", pipe_name,
					    count);

		if(-1 == out_fd) {
			DSTRM_EVENT(PIPE_TEST, PIPE_END, count);
		} else {
			DSTRM_EVENT(GAP_TEST, SIG_SENT, unique_id);
			send(out_fd, &msg, msg.size(), 0);
		}
	}
	
	printf("%s exiting\n", name);
	return ;
}

struct Output: public Exit
{
	void process();
};

void Output::process()
{
	struct Message msg;

	while (1) {
		if (msg.read(in_fd) <= 0) {
			/* 
			 * Received interrupt signal while receiving
			 * or the other end was closed.
			 * We must be done.
			 */
			break;
		}

		/* display frame */
	}

}

struct Catcher: public Entry
{
	Catcher(int port): port(port) {}
	void setup();
	void process();
	int server_fd;
	int port;
};

void Catcher::setup()
{
	int yes = 1;
	struct sockaddr_in addr;

	addr.sin_family = AF_INET;
	addr.sin_port = htons(port);
	addr.sin_addr.s_addr = inet_addr("127.0.0.1");
	memset(addr.sin_zero, '\0', sizeof addr.sin_zero);

	if ((server_fd = socket(PF_INET, SOCK_STREAM, 0)) == -1) {
		perror("socket");
		exit(1);
	}

	if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &yes,
		       sizeof(int)) == -1) {
		perror("setsockopt");
		exit(1);
	}

	if (bind(server_fd, (struct sockaddr *)&addr, sizeof addr)) {
		perror("bind");
		exit(1);
	}

	if (listen(server_fd, 1) == -1) {
		perror("listen");
		exit(1);
	}

}

void Catcher::process()
{
	struct Message msg;
	int count = 0;
	unsigned int first;
	int in_fd;

	in_fd = accept(server_fd, NULL, 0);
        if (in_fd == -1) {
		perror("accept");
		exit(1);
        }

	close(server_fd);

	while (1) {
		if (msg.read(in_fd) <= 0) {
			/* 
			 * Received interrupt signal while receiving
			 * or the other end was closed.
			 * We must be done.
			 */
			break;
		}

		++count;

		first = 0;
		first |= count;
		
		send(out_fd, &msg, msg.size(), 0);

		DSTRM_EVENT(GAP_TEST, SIG_SENT, first);

		DSTRM_EVENT(PIPE_TEST, PIPE_START, count);
	}

	printf("catcher for port %d exiting\n", port);
}

using namespace cfgu;

int main(int argc, char** argv)
{
	Config cfgu;
	int workers  = 0;

	srand(0);

	DSUI_BEGIN(&argc, &argv);

	argp_parse (&argp, argc, argv, 0, 0, 0);
	
	printf("Pipeline starting up on port %d\n", port);

	try {
	cfgu.load(config_file);

	pipe_name = cfgu.get("name").str();

	List threads = cfgu.get("threads").list();

	workers = threads.size();

	if (0 == workers) {
		fprintf(stderr, "No workers specified.\n");
	}

	if(cfgu.find("ccsm") && cfgu.get("ccsm").is_true()) {
		use_ccsm = 1;
		ccsm_fd = ccsm_open();
		if (ccsm_fd < 0) {
			perror("ccsm_open");
			return 1;
		}
		
		if (ccsm_create_set(ccsm_fd, pipe_name, 0)) {
			perror("create set");
			return 1;
		}
	} 

	if(cfgu.find("gsched") && cfgu.get("gsched").is_true()) {
		use_gs = 1;
		grp_fd = grp_open();
		if (grp_fd < 0) {
			perror("grp_open");
			return 1;
		}
	}

	port = cfgu.get("port").real();

	std::vector<Stage*> stages;

	int i = 0;
	List::Iterator iter = threads.begin();
	while (iter.has_next()) {
		Object thread = iter.next().obj();
		Worker* worker = new Worker();
	        stages.push_back(worker);
		worker->order = i;
		worker->prio = workers - i;

		snprintf(worker->name, MAX_NAME, "%s", thread.get("name").str());

		worker->work_dist = rdist::config(thread.get("work_dist").obj());
		++i;
	}

	Pipeline pipe(stages);

	pipe.entry = new Catcher(port);
	snprintf(pipe.entry->name, MAX_NAME, "%s_catcher", pipe_name);

        pipe.exit = new Output();
        snprintf(pipe.exit->name, MAX_NAME, "%s_output", pipe_name);

	pipe.start();
	pipe.wait();

	printf("Pipeline complete.\n");
	
	} catch(cfgu::Exception e) {
		fprintf(stderr, "Config file error: %s\n", e.what());
		exit(1);
	}

	if(use_ccsm) {
		if (ccsm_destroy_set(ccsm_fd, pipe_name)) {
			perror("destroy pipeline set");
		}
		
		close(ccsm_fd);    
	}

	if(use_gs) {
		close(grp_fd);
	}

	DSUI_CLEANUP();
	
	return 0;
}
