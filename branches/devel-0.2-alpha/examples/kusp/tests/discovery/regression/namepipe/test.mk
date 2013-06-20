PIPES = 0
TRANSFERS = 0

traceme:
	rm -rf data/*
	traceme namepipe -p4 -t4

new_data:
	postprocess f ../disco.pipes

# TODO: Write a filter that will diff the ACS PCS structures for
# on two sets of files
#
#diff:

traceme_hard:
	traceme namepipe -p20 -t200

traceme_general:
	traceme namepipe -p$(PIPES) -t$(TRANSFERS)
