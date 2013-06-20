from os.path import join
from os import listdir
from pykusp import configfile

GROUP_STATE_ROOT = '/sys/class/misc/group_sched/state/' 

# Group Scheduling SysFs File Heirarchy
#
# state/
#   groups/
#      groupi/
#         members/
#            symlink to memberj
#         id
#         name
#
#   members/
#      memberl
#         id
#         name
#
#   schedulers/
#      schedulerm
#         groups/
#            symlink to groupn
#         id
#         name
#####

# specific to the sysfs layout
def group_members_dir(groupdir):
	return join(groupdir, 'members')
def scheduler_groups_dir(scheddir):
	return join(scheddir, 'groups')
def state_members_dir(statedir):
	return join(statedir, 'members')
def state_groups_dir(statedir):
	return join(statedir, 'groups')
def state_schedulers_dir(statedir):
	return join(statedir, 'schedulers')
def state_top_group_dir(statedir):
	return join(statedir, 'topgroup')
def id_file(dir):
	return join(dir, 'id')
def name_file(dir):
	return join(dir, 'name')

# specific to our representation of the layout
def member_dict(id, name):
	return {'name': name, 'id': id}
def group_dict(id, name, members):
	return {'name': name, 'id': id, 'members': members}
def scheduler_dict(id, name, groups):
	return {'name': name, 'id': id, 'groups': groups}
def state_dict(groups, members, schedulers, topgrp):
	return {'groups': groups, 'members': members,
			'schedulers': schedulers, 'topgrp': topgrp}

def read_int(file):
	file = open(file, 'r')
	i = int(file.read())
	file.close()
	return i

def read_string(file):
	file = open(file, 'r')
	s = file.read()
	if s[-1:] == '\n': s = s[:-1]
	file.close()
	return s

def read_member(dir):
	id = read_int(id_file(dir))
	name = read_string(name_file(dir))
	return member_dict(id, name)

def read_group(dir):
	id = read_int(id_file(dir))
	name = read_string(name_file(dir))
	members = read_members(group_members_dir(dir))
	return group_dict(id, name, members)

def read_groups(dir):
	groups = []
	for grpdir in listdir(dir):
		group = read_group(join(dir, grpdir))
		groups.append(group)
	return groups

def read_scheduler(dir):
	id = read_int(id_file(dir))
	name = read_string(name_file(dir))
	groups = read_groups(scheduler_groups_dir(dir))
	return scheduler_dict(id, name, groups)

def read_schedulers(dir):
	schedulers = []
	for scheddir in listdir(dir):
		scheduler = read_scheduler(join(dir, scheddir))
		schedulers.append(scheduler)
	return schedulers

def read_members(dir):
	members = []
	for memdir in listdir(dir):
		member = read_member(join(dir, memdir))
		members.append(member)
	return members

def read_top_group_name(dir):
	grpdir = listdir(dir)
	if len(grpdir) == 0:
		return ""
	if len(grpdir) > 1:
		raise Exception
	return read_string(name_file(join(dir, grpdir[0])))

def read_state(dir):
	members = read_members(state_members_dir(dir))
	groups = read_groups(state_groups_dir(dir)) 
	schedulers = read_schedulers(state_schedulers_dir(dir))
	top_group_name = read_top_group_name(state_top_group_dir(dir))
	return state_dict(groups, members, schedulers, top_group_name)
