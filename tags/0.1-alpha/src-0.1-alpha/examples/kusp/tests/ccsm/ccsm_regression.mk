all: import-test regression-test

import-test:
	cd regression;\
	if python ccsm_import_test.py; then echo ' '; \
	else exit 1; fi;

regression-test:
	cd regression;\
	if python ccsm_regression.py; then echo ' '; \
	else exit 2; fi;

clean: 
	cd regression; make -f test.mk clean
	rm -f *.out
