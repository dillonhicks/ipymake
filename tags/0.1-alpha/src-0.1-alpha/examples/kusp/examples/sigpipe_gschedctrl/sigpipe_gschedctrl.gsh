#
# comment
#
<gsh-installation>
local-root = "pipeline_group"
attachment-point = "sigpipe_gschedctrl"

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
# comment
#
<groups>
pipeline_group = {
	sdf = "sdf_seq"
	attributes = [managed]
	per_group_data = {}
	members = [thread-0, thread-1, thread-2, thread-3]
	member_name = "pipeline_group_mem"
	comment = ""
}


<threads>
thread-0 = "simple-thread"
thread-1 = "simple-thread"
thread-2 = "simple-thread"
thread-3 = "simple-thread"

<thread-specification>
simple-thread = {
	attributes = [exclusive]
	per_member_data = {
		priority = 1
	}
	comment = "should create a member with priority 1"
}


