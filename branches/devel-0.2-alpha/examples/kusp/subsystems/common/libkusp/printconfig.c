#include <configfile.h>
#include <stdio.h>
#include <unistd.h>
#include <misc.h>
#include <kusp_common.h>
#include <getopt.h>
#include <stdlib.h>

char *usage =
"printconfig [-s <specfile>] [-C force C-string stle output] | files ....";


void write_string_config(FILE *out, struct hashtable *config)
{
	FILE *t = tmpfile();
	char buf[512];
	int i;
	write_config(t, config);
	rewind(t);

	fprintf(out, "char *mystring =\n");
	while (fgets(buf, 512, t) != NULL) {
		fprintf(out, "\"");

		for (i=0; i < (strlen(buf)); i++) {
			char x = buf[i];

			// XXX: are these cases exhaustive?
			switch (x) {
			case '\\':
				fprintf(out, "\\\\");
				break;
			case '\"':
				fprintf(out, "\\\"");
				break;
			case '\n':
				break;
			default:
				fprintf(out, "%c", x);
			}
		}

		fprintf(out, "\\n\"\n");
	}
	fclose(t);
}


int main (int argc, char ** argv) {
	struct hashtable *config;
	char *specfile = NULL;
	int cstyle = 0;
	int isspec = 0;
	int preproc_only = 0;
	hashtable_t *spec = NULL;
	print_greeting("Configile Prettyprinter");

	while (1) {
		int c;
		int option_index = 0;
		static struct option long_options[] = {
			{"spec", 1, 0, 's'},
			{"string-style", 0, 0, 'C'},
			{"spec-file", 0, 0, 'S'},
			{"preprocess", 0, 0, 'p'},
			{0,0,0,0}
		};
		c = getopt_long(argc, argv, "s:hCSp", long_options,
				&option_index);

		if (c == -1)
			break;

		switch (c) {
		case 's':
			specfile = strdup(optarg);
			break;
		case 'S':
			isspec = 1;
			break;
		case 'C':
			cstyle = 1;
			break;
		case 'p':
			preproc_only = 1;
			break;
		case 'h':
		default:
			printf("%s\n", usage);
			exit(1);
		}
	}

	if (specfile) {
		printf("Reading spec file...\n");
		spec = parse_spec(specfile);
		if (!spec) {
			printf("Error parsing spec file %s.\n", specfile);
			return 1;
		} else {
			printf("Spec parsed successfully.\n");
			if (optind >= argc) {
				write_config(stdout, spec);
			}
		}
	}

	if (optind >= argc && !spec) {
		printf("No input files given.\n");
	}

	while (optind < argc) {



		char *filename = argv[optind++];
		printf("Reading config file %s...\n", filename);

		if (preproc_only) {
			FILE *f = fopen(filename, "r");
			preprocin = f;
			preprocout = stdout;
			preprocess();
			fclose(f);
			continue;
		}

		if (isspec) {
			config = parse_spec(filename);
		} else {
			config = parse_config(filename);
		}

		if (!config) {
			printf("Error parsing configuration file %s\n", filename);
			continue;
		}



		if (spec) {
			printf("Checking validity of %s against spec...\n", filename);
			struct vexcept *ex = verify_config_dict(config, spec, NULL);
			if (ex) {
				print_vexcept(ex);
				free_vexcept(ex);
				printf("Error in structure of %s\n", filename);
				continue;
			}
		}


		if (!cstyle) {
			write_config(stdout, config);
		} else {
			write_string_config(stdout, config);
		}
		free_config(config);
	}
	if (spec) {
		free_config(spec);
	}

	return 0;
}
