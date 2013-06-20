#
#
#
<gsh-installation>
local-root = "bp"
attachment-point = "gsched_top_seq_group"

#
# SDF Specifications
#
<sdf-specification>

# Standard sequential sdf with integer priority.
#
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
# Balanced progress SDF
#
sdf_balanced_progress = {
	name = "Balanced Progress"
	per_group_data = {}
	per_member_data = {}
	
}

#
# Group Definitions
#
<groups>
bp = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [pipe1, pipe2, pipe3, pipe4]
	member_name = "bp"	
	comment = ""
}

pipe1 = {
	sdf = "sdf_seq"
	attributes = []
	per_group_data = {}
	members = [p1t1, p1t2, p1t3, p1t4]
	member_name = "pipe1"
	comment = ""
}

pipe2 = {
	sdf = "sdf_seq"
	attributes = []
	per_group_data = {}
	members = [p2t1, p2t2, p2t3, p2t4]
	member_name = "pipe2"
	comment = ""
}


pipe3 = {
	sdf = "sdf_seq"
	attributes = []
	per_group_data = {}
	members = [p3t1, p3t2, p3t3, p3t4]
	member_name = "pipe3"
	comment = ""
}

pipe4 = {
	sdf = "sdf_seq"
	attributes = []
	per_group_data = {}
	members = [p4t1, p4t2, p4t3, p4t4]
	member_name = "pipe4"
	comment = ""
}

<threads>
p1t1 = "simple-thread-4"
p1t2 = "simple-thread-3"
p1t3 = "simple-thread-2"
p1t4 = "simple-thread-1"

p2t1 = "simple-thread-4"
p2t2 = "simple-thread-3"
p2t3 = "simple-thread-2"
p2t4 = "simple-thread-1"

p3t1 = "simple-thread-4"
p3t2 = "simple-thread-3"
p3t3 = "simple-thread-2"
p3t4 = "simple-thread-1"

p4t1 = "simple-thread-4"
p4t2 = "simple-thread-3"
p4t3 = "simple-thread-2"
p4t4 = "simple-thread-1"

<thread-specification>
simple-thread-1 = {
	attributes = [exclusive]
	per_member_data = {
		priority = 1
	}
	comment = "should create a member with priority 1"
}

simple-thread-2 = {
	attributes = [exclusive]
	per_member_data = {
		priority = 2
	}
	comment = "should create a member with priority 2"
}

simple-thread-3 = {
	attributes = [exclusive]
	per_member_data = {
		priority = 3
	}
	comment = "should create a member with priority 3"
}

simple-thread-4 = {
	attributes = [exclusive]
	per_member_data = {
		priority = 4
	}
	comment = "should create a member with priority 4"
}

