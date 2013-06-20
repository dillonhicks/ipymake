#
# comment
# GSH Configuration File For the Balanced Pipeline CCSM
# example.
#
#
# Defines a hierarchy with 3 pipeline groups with 5 threads each.
#
#
<gsh-installation>
local-root = "balanced"
attachment-point = "sigpipe_gsched_ccsm"

#
# comment
#
<sdf-specification>
sdf_seq = {
	name = "Sequential"
	per_group_data = {}
	per_member_data = {
        priority = {
                   type = "Integer"
                   value = 0
                   doc  = "Progress of the member."
                   index = 0   
                   attributes = []
       }
	}
}

#
# Comment
#
sdf_balanced_progress = {
	name = "Balanced Progress"
	per_group_data = {}
	per_member_data = {}
	
}

#
# comment
#
<groups>
balanced = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [bp_0, bp_1, bp_2]
	ccsm_name = "balanced"
}

bp_0 = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [seq_0]
	ccsm_name = "bp_0"
}

seq_0 = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [thread-00, thread-01, thread-02, thread-03]
	ccsm_name = "seq_0"
}

bp_1 = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [seq_1]
	ccsm_name = "bp_1"
}

seq_1 = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [thread-10, thread-11, thread-12, thread-13]
	ccsm_name = "seq_0"
}

bp_2 = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [seq_2]
	ccsm_name = "bp_2"
}

seq_2 = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [thread-20, thread-21, thread-22, thread-23]
	ccsm_name = "seq_0"
}


<threads>
thread-00 = "simple-thread-0"
thread-01 = "simple-thread-1"
thread-02 = "simple-thread-2"
thread-03 = "simple-thread-3"
thread-04 = "simple-thread-4"

thread-10 = "simple-thread-0"
thread-11 = "simple-thread-1"
thread-12 = "simple-thread-2"
thread-13 = "simple-thread-3"
thread-14 = "simple-thread-4"

thread-20 = "simple-thread-0"
thread-21 = "simple-thread-1"
thread-22 = "simple-thread-2"
thread-23 = "simple-thread-3"
thread-24 = "simple-thread-4"

thread-30 = "simple-thread-0"
thread-31 = "simple-thread-1"
thread-32 = "simple-thread-2"
thread-33 = "simple-thread-3"
thread-34 = "simple-thread-4"

<members>
simple-thread-0 = {
	attributes = [exclusive]
	per_member_data = {
		priority = 0
	}
	comment = "should create a member with priority 0"
	ccsm_name = "simple-thread-0"
}

simple-thread-1 = {
	attributes = [exclusive]
	per_member_data = {
		priority = 1
	}
	comment = "should create a member with priority 1"
	ccsm_name = "simple-thread-1"
}

simple-thread-2 = {
	attributes = [exclusive]
	per_member_data = {
		priority = 2
	}
	comment = "should create a member with priority 2"
	ccsm_name = "simple-thread-2"
}

simple-thread-3 = {
	attributes = [exclusive]
	per_member_data = {
		priority = 3
	}
	comment = "should create a member with priority 3"
	ccsm_name = "simple-thread-3"
}

simple-thread-4 = {
	attributes = [exclusive]
	per_member_data = {
		priority = 4
	}
	comment = "should create a member with priority 4"
	ccsm_name = "simple-thread-4"
}

