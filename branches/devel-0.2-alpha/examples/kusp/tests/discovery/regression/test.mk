all:
	cd pipe ; echo; echo "Testing: pipe";\
	if traceme ./pipe ; then echo "Pipe Passed!"; \
	else echo 'Failed'; exit 1; \
	fi;
	
	@echo
	cd socket ;echo; echo "Testing: socket"; \
	if traceme ./socket;\
	then echo "Socket Passed!"; else echo 'Failed'; exit 2; \
	fi;
	
	@echo
	cd namepipe ;echo; echo "Testing: namepipe"; \
	if traceme ./namepipe -p 3 -t 5 ; \
	then echo "passed"; else echo 'Failed'; exit 3; \
	fi;
	
	@echo
	cd shmem ;echo; echo "Testing: shmem"; \
	if traceme ./shmem ; \
	then echo "passed"; else echo 'Failed'; exit 4; \
	fi;
	
	@echo
	cd fcntl ;echo "Testing: fcntl"; \
	if traceme ./fileloc ; \
	then echo "passed"; else echo 'Failed'; exit 5; \
	fi;
	