# kusp_regression.mk
# Regression tests for kusp python modules.
#

TEST_SUBDIRS =  ccsm \
		datastreams \
		discovery


.PHONY: ccsm datastreams discovery netspec gsched kuspcommon



all: ccsm datastreams discovery
	@echo 'All tests completed!'
	
ccsm:
	@echo
	@echo '--> Starting CCSM test'
	cd ccsm; if make -f ccsm_regression.mk >& ccsm_regress.out; then echo 'SUCCESS: CCSM test completed successfully'; else echo 'ERROR: CCSM test FAILED!'; exit 1; fi
	@echo
	
discovery:
	@echo
	@echo '--> Starting Discovery test'
	cd discovery/; \
	if make -f discovery_regression.mk >& ../discovery_regress.out;\
	then echo 'SUCCESS: Discovery test completed successfully'; \
	else echo 'ERROR: Discovery test FAILED!'; \
	fi
	@echo

datastreams:
	@echo
	@echo '--> Starting Data Streams test'
	cd datastreams; \
	if make -f datastreams_regression.mk >& ../datastreams_regress.out; then echo 'SUCCESS: Data Streams test completed successfully'; else echo 'ERROR: Data Streams test FAILED!'; fi
	@echo

gsched:
	@echo
	@echo '--> Starting Group Scheduling test'
	if python test_groupsched.py -t; then echo 'SUCCESS: Group Scheduling test completed successfully'; else echo 'ERROR: Group Scheduling test FAILED!'; fi
	@echo
kuspcommon:
	@echo
	@echo '--> Starting KUSP Common Software Components test'
	if python test_kuspcommon.py -t; then echo 'SUCCESS: KUSP Common Software Components test completed successfully'; else echo 'ERROR: KUSP Common Software Components test FAILED!'; fi
	@echo

netspec:
	@echo
	@echo '--> Starting netspec tests'
	if python test_netspec.py -t; then echo 'SUCCESS: netspec test completed successfully'; else echo 'ERROR: netspec test FAILED!'; fi
	@echo


clean-datastreams:
	cd datastreams; make -f datastreams_regression.mk clean

clean-ccsm:
	cd ccsm; make -f ccsm_regression.mk clean

clean-discovery:
	cd discovery; make -f discovery_regression.mk clean


clean: clean-datastreams
	rm -f *.out
