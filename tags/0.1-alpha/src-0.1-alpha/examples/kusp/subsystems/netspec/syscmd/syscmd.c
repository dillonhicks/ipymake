#include <netspec2.h>
#include <stdlib.h>

#define KUSP_DEBUG 1

#include <kusp_common.h>

void exec_phase(hashtable_t *config)
{
	dprintf("exec_phase starting\n");
	list_t *commands, *pos;

	unhash_list(config, "commands", &commands);

	list_for_each(pos, commands) {
		char *cmd;
		unlist_string(pos, &cmd);
		fprintf(stderr, "i would have run '%s'\n", cmd);
	}

	free_config(config);

	ns_acknowledge(NS_OK_EXIT, NULL, NULL, NULL);
}



int main(int argc, char **argv)
{
	dprintf("syscmd started\n");

	if (ns_initialize(&argc, &argv)) {
		ns_set_execute("exec", NULL, &exec_phase,"execute command");
		ns_begin();
	}

	return 0;
}



