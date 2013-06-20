traceme:
	rm -rf data/*
	traceme shmem -s 4

new_data:
	postprocess f ../disco.pipes

# TODO: Write a filter that will diff the ACS PCS structures for
# on two sets of files
#
#diff:
	#postprocess f ../tmp.disco.pipes

traceme_hard:
	traceme shmem -s 20
