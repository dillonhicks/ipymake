all: ds_import_test dski_regression 

dski_regression: socketpipe_dski

socketpipe_dski:
	cd socketpipe; if dskictrl -c socketpipe_gsched_ccsm.dski ;\
	then echo ' ' ; \
	else 'socketpipe execution failed!'; exit 1;\
	fi;
	cd socketpipe; if postprocess f socketpipe_gsched_ccsm.pipes; \
	then echo ' '; else 'socket pipe DSUI post processing failed!';\
	exit 2; fi;

socketpipe_dsui:
	cd socketpipe; if  ./socketpipe --threads=3 --stimuli=200 ;\
	then echo ' ' ; \
	else 'socketpipe execution failed!'; exit 3;\
	fi;
	cd socketpipe; if postprocess n socketpipe_gsched.pipes; \
	then echo ' '; else 'socket pipe DSUI post processing failed!';\
	exit 4; fi;

ds_import_test:
	if python datastreams_import_test.py; then echo ' ';\
	else echo 'Data Streams modules not found, import failed!';\
	exit 5; fi;

clean:
	rm -rf ./build