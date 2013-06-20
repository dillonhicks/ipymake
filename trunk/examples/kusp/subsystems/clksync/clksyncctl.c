#include <clksyncapi.h>
#include <stdio.h>
#include <getopt.h>
#include <kusp_common.h>
#include <stdlib.h>


static char *help = "Usage:\n"
" -f <frequency>	Set new tsckhz value for system\n"
" -d <device name>	Set network device to use\n"
" When called without parameters, show current system clksync info.\n";

int main(int argc, char ** argv) {



	char *device = NULL;
	unsigned long tsckhz = 0;
	int fd;
	int retval;
	int c;
	int irq = 0;
	clksync_info_t cinfo;

	printf("Clksync Controller");

	while (1) {
		c = getopt(argc, argv, "i:f:d:h");

		if (c == -1) {
			break;
		}

		switch (c) {
		case 'f':
			tsckhz = atol(optarg);
			break;
		case 'd':
			device = strdup(optarg);
			break;
		case 'i':
			irq = atoi(optarg);
			break;
		default:
			printf(help);
			return 0;
		}
	}

	fd = clksync_open();
	if (fd < 0) {
		eprintf("Unable to open clksync device\n");
		kusp_perror("clksync_open");
		return 1;
	}


	if (device != NULL) {
		if (clksync_set_device(fd, device)) {
			eprintf("Unable to set device to %s.\n",
					device);
			kusp_perror("clksync_set_device");
			return 1;
		} else {
			iprintf("now using network device %s.\n",
					device);
		}
	}

	if (tsckhz) {
		if (clksync_set_freq(fd, tsckhz)) {
			kusp_perror("clksync_set_freq");
			eprintf("Unable to set tsckhz to %lu.\n",
					tsckhz);
			return 1;
		} else {
			iprintf("tsckhz set to %lu.\n",
					tsckhz);
		}
	}

	if (irq) {
		if (clksync_set_irq(fd, irq)) {
			kusp_perror("clksync_set_irq");
			eprintf("Unable to set irq to %d.\n",
					irq);
			return 1;
		} else {
			iprintf("irq set to %d.\n",
					irq);
		}
	}


	retval = clksync_get_info(fd, &cinfo);
	if (retval) {
		kusp_perror("clksync_get_info");
		return 1;
	}

	iprintf("     ts: %llu\n", cinfo.ts);
	iprintf(" tsckhz: %llu\n", cinfo.tsckhz);
	iprintf(" ts_sec: %ld\n", cinfo.time.tv_sec);
	iprintf("ts_nsec: %ld\n", cinfo.time.tv_nsec);
	iprintf("    irq: %d\n", cinfo.irq);
	return 0;

}
