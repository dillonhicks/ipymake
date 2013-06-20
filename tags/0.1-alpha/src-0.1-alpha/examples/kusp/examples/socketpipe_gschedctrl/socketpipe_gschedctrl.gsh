#
# Installation information is currently for reference 
# for expansion that is planned for the future. 
# Such as multiple hierarchies within a file, exectuable based
# hierarchy attachment points, etc.
#
<gsh-installation>
local-root = "socket_pipeline"
attachment-point = "sockpipe"

#
# Currently for reference, planned for future use.
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
# GROUPS are defined as:
# 
# <group-name> = {
#          sdf = "<sdf-name>"
#	   attributes = [<attr0, 
#	   	      	<...>]
#	   per_group_data = { <datum_name> = <value> }
#	   members = [  <member-0>,
#	   	        <member-2>,
#			 ... ,
#			<member-n>
#		     ]
#	   member_name = "<member-name>"
# 	   comment = "I'm a group that does _____"
# }
#
# All fields within the group specification are required, 
# but attributes, per_group_data, and members are allowed
# empty dictionary and list values.
#

<groups>
#
# Create socket_pipeline group with 7 Thread members.
#
socket_pipeline = {
	sdf = "sdf_seq"
	attributes = []
	per_group_data = {}
	members = [
				thread-0,
				thread-1,
				thread-2,
				thread-3,
				thread-4,
				thread-5,
				thread-6
			  ]
	member_name = "socket_pipeline"
	comment = ""			  
}

# Creates seven Threads that use simple-thread as a specfication
# (template).
#  <desired-thread-name> = <thread-specification-name>
#
<threads>
thread-0 = "simple-thread"
thread-1 = "simple-thread"
thread-2 = "simple-thread"
thread-3 = "simple-thread"
thread-4 = "simple-thread"
thread-5 = "simple-thread"
thread-6 = "simple-thread"

<thread-specification>
simple-thread = {
	attributes = [exclusive]
	per_member_data = {
		priority = 1
	}
	comment = "should create a member with priority 1"
}


