#define KUSP_DEBUG 1
#include <kusp_common.h>

#include <netspec2.h>
#include <configfile.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>

struct phase {
	char *name;
	hashtable_t *spec;
	char *doc;
	void (*func_ptr)(hashtable_t *config);
};

static hashtable_t *phase_table = NULL;
static int ack_flag;

FILE *rfile = NULL;
FILE *wfile = NULL;

static void permute_argv(int *argcp, char ***argvp, int num, int *i)
{
	int j;
	for (j=(*i)+num; j < *argcp; j++) {
		(*argvp)[j-num] = (*argvp)[j];
	}
	*argcp = *argcp - num;
	(*i)--;
}

static void ns_query_phase(hashtable_t *config)
{
	hashtable_t *retval;
	hashtable_itr_t itr;

	iprintf("Got a documentation query\n");

	retval = create_dictionary();
	init_iterator(&itr, phase_table);

	do {
		hashtable_t *d = create_dictionary();
		struct phase *p = hashtable_iterator_value(&itr);
		hashtable_t *spec = p->spec;
		char *doc = p->doc;
		if (!spec) {
			spec = create_dictionary();
		}
		if (!doc) {
			doc = "No documentation for this phase";
		}

		hashtable_insert(d, strdup("doc"), encap_string(doc));
		hashtable_insert(d, strdup("spec"), encap_hash(spec));

		hashtable_insert(retval, strdup(p->name), encap_hash(d));

	} while (hashtable_iterator_advance(&itr));

	ns_acknowledge(NS_OK_EXIT, NULL, NULL, retval);
}



int ns_initialize(int *argcp, char ***argvp)
{
	int i;
	int fd;

	char **argv = *argvp;

	phase_table = create_dictionary();

	for (i=1; i < *argcp; i++) {
		if (!strcmp(argv[i], "--netspec")) {
			if ((i+1) >= *argcp) {
				eprintf("--netspec requires a file descriptor as parameter");
				exit(1);
			}
			fd = atoi(argv[i+1]);

			iprintf("NETSPEC daemon communicating over file descriptor %d\n",
					fd);

			wfile = fdopen(fd, "w");
			rfile = fdopen(fd, "r");

			permute_argv(argcp, argvp, 2, &i);

			return 1;
		}
	}

	ns_set_execute("_query", NULL, ns_query_phase, "get phases and parameters");
	return 0;
}


hashtable_t *ns_read_config()
{
	int size, size_read;
	char *buf;
	hashtable_t *retval, *retval2;

	// read the length, stored in 4 byte
	fread(&size, sizeof(int), 1, rfile);
#if 0
	// What the hell is this?
	size;
#endif

	size_read = 0;
	buf = malloc(size+1);

	size_read += fread(buf, size, 1, rfile);

	buf[size] = '\0';

	retval = parse_config_string(buf);
	free(buf);

	unhash_hashtable(retval, "serialized", &retval2);
	hashtable_destroy(retval, 0);

	return retval2;
}


void ns_send_config(hashtable_t *config)
{
	char *buf;
	size_t size;
	int sz;
	hashtable_t *cfg = create_dictionary();
	hashtable_insert(cfg, strdup("serialized"), encap_hash(config));

	config_to_string(cfg, &size, &buf);

	sz = size;
	fwrite(&sz, sizeof(sz), 1, wfile);
	fprintf(wfile, "%s", buf);
	fflush(wfile);

	free(buf);
	free_config(cfg);
}

void ns_set_execute(char *phase_name, hashtable_t *spec,
		void (*func_ptr)(hashtable_t *config), char *doc)
{
	struct phase *p = malloc(sizeof(*p));
	if (!p) {
		perror("malloc");
		return;
	}

	p->name = phase_name;
	p->spec = spec;
	p->func_ptr = func_ptr;
	p->doc = doc;


	if (hashtable_search(phase_table, phase_name)) {
		eprintf("phase %s already defined!\n", phase_name);
		free(p);
	} else {
		hashtable_insert(phase_table, strdup(phase_name), p);
	}
}



void ns_acknowledge(int error, char *message, char *filename, hashtable_t *config)
{
	if (!filename) {
		ns_acknowledge_files(error, message, NULL, config);
	} else {
		list_t *l = create_list();
		list_append(l, encap_string(filename));
		ns_acknowledge_files(error, message, l, config);
	}
}

void ns_acknowledge_files(int error, char *message, list_t *filenames, hashtable_t *config)
{
	iprintf("Phase sending acknowledgement with code %d\n", error);
	hashtable_t *retval = create_dictionary();

	if (filenames) {
		hashtable_insert(retval, strdup("files"), encap_list(filenames));
	}

	if (config)
		hashtable_insert(retval, strdup("config"), encap_hash(config));

	if (message)
		hashtable_insert(retval, strdup("message"), encap_string(message));


	hashtable_insert(retval, strdup("error"), encap_int(error));

	ns_send_config(retval);
	ack_flag = 1;

	switch (error) {
	case NS_OK:
	case NS_WARNING:
		return;
	case NS_OK_EXIT:
		iprintf("daemon exiting successfully\n");
		exit(EXIT_SUCCESS);
	case NS_ERROR:
		eprintf("daemon exiting with errors\n");
		exit(EXIT_FAILURE);
	}
}


void ns_begin(void)
{
	char *name;
	hashtable_t *phase_config, *phase_params;
	struct phase *p;
	struct vexcept *ve;

	if (wfile == NULL) {
		eprintf("ns_begin called, but NETSPEC has not been initialized\n");
		exit(1);
	}

	while (1) {
		iprintf("Waiting for command\n");
		phase_config = ns_read_config();

		ack_flag = 0;

		unhash_string(phase_config, "phase_name", &name);
		unhash_hashtable(phase_config, "params", &phase_params);

		iprintf("Got phase command %s\n", name);

		p = hashtable_search(phase_table, name);

		if (!p) {
			wprintf("Control send unknown phase %s\n", name);
			ns_acknowledge(NS_WARNING, NULL, NULL, NULL);
			continue;
		}

		if (p->spec) {
			ve = verify_config_dict(phase_params, p->spec, NULL);
			if (ve) {
				print_vexcept(ve);
				free_vexcept(ve);
				eprintf("Phase parameters did not pass verification!\n");
				ns_acknowledge(NS_ERROR, NULL, NULL, phase_params);
			}

		}


		iprintf("EXECUTING PHASE %s\n", name);


		(p->func_ptr)(phase_params);


		if (!ack_flag) {
			ns_acknowledge(NS_OK, NULL, NULL, NULL);
		}
		iprintf("PHASE %s FINISHED\n", name);

	}
}




