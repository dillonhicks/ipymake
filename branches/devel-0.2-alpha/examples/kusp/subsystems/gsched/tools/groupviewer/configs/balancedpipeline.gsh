#
# comment
#
<gsh-installation>
local-root = "balanced_group"
attachment-point = "app_gsh_root"

#
# comment
#
<sdf-specification>
sdf_balanced_progress = {
	name = "Balanced Progress"
	per_group_data = {}
	per_member_data = {
		progress = {
	   	           type = "Integer"
	               doc  = "Progress of the member."
	               value = 0
	               index = 0   
	               attributes = []
	   }
	}  
}

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
balanced_group = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [bp_group_0, bp_group_1, bp_group_2, bp_group_3]
	ccsm_name = "balanced_group"
}

bp_group_0 = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [seq_group_0, node_0, node_1, node_2]
	ccsm_name = "bp_group_0"
}

bp_group_1 = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [seq_group_1, node_5, node_3, node_4]
	ccsm_name = "bp_group_1"
}

bp_group_2 = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [seq_group_2, node_8, node_6, node_7]
	ccsm_name = "bp_group_2"
}

bp_group_3 = {
	sdf = "sdf_balanced_progress"
	attributes = []
	per_group_data = {}
	members = [seq_group_3, node_9, node_10, node_11]
	ccsm_name = "bp_group_3"
}


seq_group_0 = {
	sdf = "sdf_seq"
	attributes = []
	per_group_data = {}
	members = [node_0, node_1, node_2]
	ccsm_name = "seq_group_0"
}

seq_group_1 = {
	sdf = "sdf_seq"
	attributes = []
	per_group_data = {}
	members = [node_3, node_4, node_5]
	ccsm_name = "seq_group_1"
}

seq_group_2 = {
	sdf = "sdf_seq"
	attributes = []
	per_group_data = {}
	members = [node_6, node_7, node_8]
	ccsm_name = "seq_group_2"
}

seq_group_3 = {
	sdf = "sdf_seq"
	attributes = []
	per_group_data = {}
	members = [node_9, node_10, node_11]
	ccsm_name = "seq_group_3"
}

<threads>
node_0 = "node_0"
node_1 = "node_1"
node_2 = "node_2"
node_3 = "node_3"
node_4 = "node_4"
node_5 = "node_5"
node_6 = "node_6"
node_7 = "node_7"
node_9 = "node_9"
node_10 = "node_10"
node_11 = "node_11"


#
# comment
#
<members>
node_0 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_0"
}

node_1 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_1"
}

node_2 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_2"
}

node_3 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_3"
}

node_4 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_4"
}

node_5 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_5"
}

node_6 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_6"
}

node_7 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_7"
}

node_8 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_8"
}

node_9 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_9"
}

node_10 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_10"
}

node_11 = {
	attributes = []
	per_member_data = { progress = 0 }
	comment = "should create a member with extra data 1"
	ccsm_name = "node_11"
}

