#include <cstdio>
#include <unistd.h>
#include <sys/wait.h>

#include <errno.h>
#include <argp.h>
#include <ccsm.h>

#include "cfgu.h"

using namespace cfgu;

#define MAX_ARGS 10
#define MAX_ARG_LENGTH 100

static int stimuli = 1;
static int use_ccsm = 0;
static const char* config_file = "launch.conf";

/* The options we understand. */
static struct argp_option options[] = {
	{"stimuli",    's', "1+",       0,  "# of messages to send" },
	{"conf",        1,  "file",     0,  "configuration file"    },
	{ 0 }
};
          
/* Parse a single option. */
error_t parse_opt (int key, char *arg, struct argp_state *state)
{
	
	switch (key) {
	case 's':
		stimuli = atoi(arg);
		if (stimuli <= 0) {
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
	"launch -- exec sender and pipes on the same machine",
};

int main(int argc, char** argv)
{
	char args[MAX_ARGS][MAX_ARG_LENGTH];
	int rv;
	int ccsm_fd;

	argp_parse (&argp, argc, argv, 0, 0, 0);

	try {
		Config config;
		config.load(config_file);
		
		List pipes = config.get("pipelines").list();
		
		List senders = config.get("senders").list();
		
		if (config.find("ccsm") && config.get("ccsm").is_true()) {
			use_ccsm = 1;
			ccsm_fd = ccsm_open();
			if (ccsm_fd < 0) {
				perror("ccsm_fd");
				return 1;
			}
			
			if (ccsm_create_set(ccsm_fd, "bp", 0)) {
				perror("ccsm_create_set");
				return 1;
			}
		}
	
		List::Iterator piter = pipes.begin();
		while (piter.has_next()) {
			Object pipe = piter.next().obj(); 
			
			if (use_ccsm) {
				const char* name = pipe.get("name").str();
				ccsm_create_set(ccsm_fd, name, 0);
				ccsm_add_member(ccsm_fd, "bp", name);
			}
			
			snprintf(args[0], MAX_ARG_LENGTH, "--conf=%s", pipe.get("config").str());
			
			rv = fork();
			if (-1 == rv) {
				perror("fork");
				return 1;
			}
			
			if (rv)
				continue;
			else {
				execl("sockpipe", "sockpipe", args[0], NULL);
			}
			
		}

		List::Iterator siter = senders.begin();
		while (siter.has_next()) {
			Object sender = siter.next().obj();
			
			snprintf(args[0], MAX_ARG_LENGTH, "--stimuli=%d", stimuli);
			snprintf(args[1], MAX_ARG_LENGTH, "--conf=%s", sender.get("config").str());
			
			rv = fork();
			if (-1 == rv) {
				perror("fork");
				return 1;
			}
			
			if (rv)
				continue;
			else {
				execl("sender", "sender", args[0], args[1], NULL);
			}		
		}
		
		int children = piter.pos() + siter.pos();
		while(children) {
			wait(NULL);
			--children;
		}

		if (use_ccsm) {
			if (ccsm_destroy_set(ccsm_fd, "bp")) {
				perror("ccsm_destroy_set");
			}
			
			close(ccsm_fd);    
		}

	} catch(cfgu::Exception e) {
		fprintf(stderr, "Config file error: %s\n", e.what());
	}
	
	return 0;
}
