#
# comment
#
<gsh-installation>
local-root = "sigpipe"
attachment-point = "app_gsh_root"

#
# comment
#
<sdf-specification>
sdf_seq = {
	name = "Sequential"
	PGD = {}
	PMD = {
	priority = "integer"
	order = [priority]
	}
}



#
# comment
#
<groups>
sigpipe = {
	sdf = "sdf_seq"
	attributes = []
	per_group_data = {}
	members = [source, inner_1, inner_2, sink, sinking_group]
	ccsm_name = "sigpipe"
}

sinking_group = {
	sdf = "sdf_rr"
	attributes = []
	per_group_data = {}
	members = [inner_1, inner_2]
	ccsm_name = "sinking_group"
}


<threads>
source = "source"
inner_1 = "inner_1"
inner_2 = "inner_2"

#
# comment
#
<members>
source = {
	attributes = [exclusive]
	per_member_data = {
		priority = 1
	}
	comment = "should create a member with extra data 1"
	ccsm_name = "source"
}

inner_1 = {
	attributes = [exclusive]
	per_member_data = {
		priority = 2
	}
	comment = "should create a member with per_member_data 2"
	ccsm_name = "inner_1"
}

inner_2 = {
	attributes = [exclusive]
	per_member_data = {
		priority = 3
	}
	comment = "should create a member with extra data a,1"
	ccsm_name = "inner_2"
}

sink = {
	attributes = [exclusive]
	per_member_data = {
		priority = 4
	}
	comment = "should create a member with extra data a,1"
	ccsm_name = "sink"
}






