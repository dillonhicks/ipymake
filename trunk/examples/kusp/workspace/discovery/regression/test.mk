all:
	cd pipe ; traceme ./pipe
	cd socket ; traceme ./socket
	cd namepipe ; traceme ./namepipe -p 3 -t 5
	cd shmem ; traceme ./shmem
	cd fcntl ; traceme ./filelock