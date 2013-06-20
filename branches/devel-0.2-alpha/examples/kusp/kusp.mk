# kusp.mk
#
# SUMMARY: Easy makefile for building/installing kusp software, useful
# 	for testing.
#

# Try to log to ~/tmp and fall back on /tmp if necessary.
ifeq ($(wildcard ~/tmp),)
LOG_PATH=/tmp
else
LOG_PATH=~/tmp
endif

$(info --> Logging to $(LOG_PATH))

KUSPROOT=.
KUSP_RPM=kusp
KUSP_SUBSYSTEMS = common \
		  datastreams \
		  gsched \
		  ccsm \
		  discovery \
		  clksync \
		  netspec

# Make will access environmental variables. We don't want to set
# KUSPINSTALL and KUSPKERNELROOT here
# if they are already set in the environment.

# No reason to warn about the environment variables if they are using an rpm.
ifeq ($(findstring rpm, $(MAKECMDGOALS)),)

ifndef KUSPINSTALL
KUSPINSTALL := /tmp/kusp-install
$(info ***** WARNING: $$KUSPINSTALL not defined. Guessing: $(KUSPINSTALL) *****)
endif

ifndef KUSPKERNELROOT
KUSPKERNELROOT := $(shell echo /usr/src/kernels/`uname -r`)
$(info ***** WARNING: $$KUSPKERNELROOT not defined. Guessing: $(KUSPKERNELROOT) *****)
endif

endif

OS_VERSION=fc10
KUSP_VERSION= 0.9
BUILD_NUMBER=5

# Builds the KUSP source tree and installs the built source tree at
# KUSPINSTALL
#
all: check-build-dir kusp-configure kusp-build kusp-install

# First removes the build directory and the KUSPINSTALL directory.
# After removing the directories, it builds the KUSP source tree and
# installs the built source at KUSPINSTALL.
#
rebuild: dist-clean kusp-configure kusp-build kusp-install

# Check to see if a build directory exsists. If it does not exist,
# creates the build directory.
#
check-build-dir: 
	@echo ''
	@echo '--> CHECKING FOR PREVIOUS BUILD DIRECTORY'
	@if test -d ./build  ; \
		then \
			echo "----> BUILD DIRECTORY EXISTS"; \
		else \
			echo "----> NO BUILD DIRECTORY FOUND"; \
			echo "----> CREATING NEW BUILD DIRECTORY"; \
		mkdir ./build; \
	fi

# Builds the KUSP source tree in the KUSPROOT/build Directory
#
kusp-build: 
	@echo 
	@echo "--> BUILDING KUSP"
	@echo
	@cd $(KUSPROOT)/build; make VERBOSE=1 >& $(LOG_PATH)/kusp_mk_kusp_buid_make.out

# Configure the KUSP source with CMake.
#
kusp-configure:
	@echo 
	@echo "--> CONFIGURING KUSP"
	@echo 
	@cd $(KUSPROOT)/build;  cmake .. -DCMAKE_INSTALL_PREFIX=$(KUSPINSTALL) \
		-DKERNELROOT=$(KUSPKERNELROOT) >& $(LOG_PATH)/kusp_mk_kusp_buid_configure.out

# Install the KUSP source to KUSPINSTALL.
#
kusp-install:
	@echo 
	@echo "--> INSTALLING KUSP"
	@echo 
	@cd $(KUSPROOT)/build; make install VERBOSE=1 >& $(LOG_PATH)/kusp_mk_kusp_install.out

# Check to see if a build directory exsists for the examples. If it does not exist,
# creates the build directory.
#
check-examples-build-dir: 
	@echo ''
	@echo '--> CHECKING FOR PREVIOUS EXAMPLES BUILD DIRECTORY'
	@if test -d ./examples/build  ; \
		then \
			echo "----> EXAMPLES BUILD DIRECTORY EXISTS"; \
		else \
			echo "----> NO EXAMPLES BUILD DIRECTORY FOUND"; \
			echo "----> CREATING NEW EXAMPLES BUILD DIRECTORY"; \
		mkdir ./examples/build; \
	fi

# Build the examples...
examples: check-examples-build-dir
	@echo 
	@echo "--> CONFIGURING EXAMPLES"
	@cd $(KUSPROOT)/examples/build;  cmake .. -DCMAKE_INSTALL_PREFIX=$(KUSPINSTALL) \
		 >& $(LOG_PATH)/kuspmk_config_examples.out; 
	@echo "--> CONFIGURATION SUCCESSFUL"
	@echo
	@echo "--> BUILDING EXAMPLES"
	@cd $(KUSPROOT)/examples/build; make VERBOSE=1 >& $(LOG_PATH)/kuspmk_build_examples.out
	@echo "--> BUILD SUCCESSFUL"

# Cleans the build directory. This method is a little bogus for big
# changes since it keeps all of the old CMake files. 
#
clean: check-build-dir
	@echo 
	@echo '--> CLEANING UP'
	@echo 
	@cd $(KUSPROOT)/build; make clean VERBOSE=1 >& $(LOG_PATH)/kusp_mk_clean.out

# Removes everything from the build directory.
#
dist-clean: check-build-dir
	@echo
	@echo "--> CLEANING BUILD DIRECTORY"
	@echo
	@cd $(KUSPROOT)/build; rm -rfv ./* >&  $(LOG_PATH)/kusp_mk_dist_clean.out

# Looks for and uninstalls all of the files installed by KUSP at
# CLEAN_PREFIX.
#
uninstall:
	@echo 
	@echo "--> UNINSTALLING KUSP FROM: $(KUSPINSTALL)"
	@echo
	cd $(KUSPROOT)/misc; python do_uninstall -v -D3 -p $(KUSPINSTALL) >&  $(LOG_PATH)/kusp_mk_uninstall.out

all_subsystem_rpms:
	(for subsys in $(KUSP_SUBSYSTEMS); \
	do \
		make -f kusp.mk subsystem_rpm KUSP_RPM=$$subsys; \
		sudo rpm -Uvh ~/rpmbuild/RPMS/i386/kusp-$$subsys-$(KUSP_VERSION)-$(BUILD_NUMBER).$(OS_VERSION).`uname -i`.rpm; \
	done;)


subsystem_rpm: 
	@echo ''
	@echo '--> CHECKING FOR PREVIOUS ~/tmp/kusp-$(KUSP_RPM) DIRECTORY'
	@if test -d ~/tmp/kusp-$(KUSP_RPM)/subsystems/$(KUSP_RPM)  ; \
		then \
			echo "----> ~/tmp/kusp-$(KUSP_RPM) DIRECTORY EXISTS"; \
		else \
			echo "----> NO ~/tmp/kusp-$(KUSP_RPM) DIRECTORY FOUND"; \
			echo "----> CREATING NEW ~/tmp/kusp-$(KUSP_RPM) DIRECTORY"; \
		mkdir -p ~/tmp/kusp-$(KUSP_RPM)/subsystems/$(KUSP_RPM); \
	fi

	@echo	
	@echo "--> SYNCING SOURCE DIRECTORY WITH ~/tmp/kusp-$(KUSP_RPM)"
	rsync -v -t -p -o -g -E $(KUSPROOT)/* ~/tmp/kusp-$(KUSP_RPM)/ >& $(LOG_PATH)/kusp_mk_rsync_kusp_tmp.out		
	rsync -r -v -t -p -o -g -E $(KUSPROOT)/cmake/* ~/tmp/kusp-$(KUSP_RPM)/cmake >& $(LOG_PATH)/kusp_mk_rsync_kusp_tmp.out
	rsync -v -t -p -o -g -E $(KUSPROOT)/subsystems/* ~/tmp/kusp-$(KUSP_RPM)/subsystems/ >& $(LOG_PATH)/kusp_mk_rsync_kusp_tmp.out	
	rsync -r -v -t -p -o -g -E $(KUSPROOT)/subsystems/$(KUSP_RPM) ~/tmp/kusp-$(KUSP_RPM)/subsystems >& $(LOG_PATH)/kusp_mk_rsync_kusp_tmp.out

	@echo 
	@echo "--> REMOVING THE BUILD DIRECTORY"
	@echo
	rm -rf ~/tmp/kusp-$(KUSP_RPM)/build
	@echo 
	@echo "--> CREATING THE SOURCE TARBALL"
	@echo
	cd ~/tmp; \
	if tar -cz  kusp-$(KUSP_RPM) > kusp-$(KUSP_RPM).tar.gz; then echo ''; \
		else echo 'Tarballing Failed'; exit 1;\
	fi
	@echo 
	@echo "--> MOVING TARBALL TO RPMBUILD DIRECTORY" 
	cd ../; mv -v  ~/tmp/kusp-$(KUSP_RPM).tar.gz ~/rpmbuild/SOURCES 


	@echo 
	@echo "--> EXECUTING rpmbuild"
	@echo
	cd 'rpms'; rpmbuild -ba -vv kusp-$(KUSP_RPM).spec >& $(LOG_PATH)/kusp_mk_exec_rpmbuild.out	
	@echo
	@echo '--> kusp-$(KUSP_RPM) RPM CREATED!'



svn-update:
	@echo 
	@echo "--> UPDATING CODE FROM SVN"
	@echo
	svn up >& $(LOG_PATH)/kusp_mk_svn_update.out

# You have to check out the kusp/trunk as kusp for this step to work.
tarball:
	@echo 
	@echo "--> REMOVING THE BUILD DIRECTORY"
	@echo
	rm -rf ./build
	@echo 
	@echo "--> CREATING THE SOURCE TARBALL"
	@echo
	cd ../; \
	if tar -cz  kusp > kusp.tar.gz; then echo ''; \
		else echo 'Tarballing Failed'; exit 1;\
	fi
	@echo 
	@echo "--> MOVING TARBALL TO RPMBUILD DIRECTORY" 
	cd ../; mv -v  kusp.tar.gz ~/rpmbuild/SOURCES 


exec-rpmbuild:
	@echo 
	@echo "--> EXECUTING rpmbuild"
	@echo
	cd 'rpms'; rpmbuild -ba -vv kusp.spec >& $(LOG_PATH)/kusp_mk_exec_rpmbuild.out	


rpm: svn-update tarball exec-rpmbuild
	@echo
	@echo '--> RPM CREATED!'


remove-rpm:
	@echo 
	@echo "--> Searching for previously installed RPM"
	@echo
	if rpm -q kusp ; then echo ''; \
		echo '--> Installed RPM found.'; echo ''; \
		echo '--> Removing previously installed KUSP RPM.'; \
		sudo rpm -e kusp >& $(LOG_PATH)/kusp_mk_remove_rpm.out; \
		else echo '';echo '--> No Installed RPM found, skipping removal'; \
	fi

rpm-install:
	@echo 
	@echo "--> INSTALLING KUSP RPM"
	@echo
	cd ~/rpmbuild/RPMS/`uname -i` ; \
	sudo rpm -Uvh kusp-$(KUSP_VERSION)-$(BUILD_NUMBER).$(OS_VERSION).`uname -i`.rpm >& \
	$(LOG_PATH)/kusp_mk_install_rpm.out
	@echo 
	@echo '--> KUSP INSTALLATION COMPLETE'

