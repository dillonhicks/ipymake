sigpipe-dsui:
	./sigpipe --dsui-config sigpipe.dsui --threads=5 --stimuli=1000
	postprocess f sigpipe.pipes
	
sigpipe-dski1:
	dskictrl -c sigpipe1.dski
	postprocess f sigpipe_dski1.pipes
	
sigpipe-dski2:
	dskictrl -c sigpipe2.dski
	postprocess f sigpipe_dski2.pipes
	
sigpipe-dski1-compete-load:
	cd /tmp; svn co https://subversion.ittc.ku.edu/svn/libertos/kernel/kurt/2.6.24/2.6.24.4-rt4-groupsched/; cd 2.6.24.4-rt4-groupsched; mkdir build; make O=build defconfig >& defconfig.out; cd build; make clean >& clean.out; make >& make.out &
	dskictrl -c sigpipe1.dski
	postprocess f sigpipe_dski1.pipes	
	
sigpipe-dski2-compete-load:
	cd /tmp; svn co https://subversion.ittc.ku.edu/svn/libertos/kernel/kurt/2.6.24/2.6.24.4-rt4-groupsched/; cd 2.6.24.4-rt4-groupsched; mkdir build; make O=build defconfig >& defconfig.out; cd build; make clean >& clean.out; make >& make.out &
	dskictrl -c sigpipe2.dski
	postprocess f sigpipe_dski2.pipes		
	
sigpipe-dski2-test-load:
	cd /yggnfs/dfturner/kernels; svn co https://subversion.ittc.ku.edu/svn/libertos/kernel/kurt/2.6.24/2.6.24.4-rt4-groupsched/; cd 2.6.24.4-rt4-groupsched; mkdir build; make O=build defconfig; cd build; make clean >& clean.out; make >& make.out &
	dskictrl -c sigpipe2.dski
	postprocess f sigpipe_dski2.pipes	
	
sigpipe-dski2-compete-load-other version:
	cd /projects/kurt; mkdir -p dfturner/tmp; ln -s /projects/kurt/dfturner/tmp ~/tmp; svn co https://subversion.ittc.ku.edu/svn/libertos/kernel/kurt/2.6.24/2.6.24.4-rt4-groupsched/; cd 2.6.24.4-rt4-groupsched; mkdir build; make O=build defconfig >& defconfig.out; cd build; make clean >& clean.out; make >& make.out &
	dskictrl -c sigpipe2.dski
	postprocess f sigpipe_dski2.pipes
