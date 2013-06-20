#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/time.h>
#include <time.h>

#include <sched_gsched.h>

int main(int argc, char **argv)
{
	int fd, pid;

	if (argc != 2)
		printf("usage: ./%s <pid>\n", argv[0]);

	pid = atoi(argv[1]);

	fd = grp_open();
	if (fd < 0) {
		perror("grp_open");
		return fd;
	}

	gsched_set_exclusive_control(fd, pid);
	printf("setting exclusive control: %d\n", pid);

	close(fd);
	return 0;
}
