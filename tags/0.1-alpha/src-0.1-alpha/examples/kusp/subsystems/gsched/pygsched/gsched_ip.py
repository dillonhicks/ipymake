"""
:mod:`gsched_ip` -- Group Scheduling with IPython
====================================================
    :synopsis: A match made in heaven.

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>
"""
import sys
import os
import signal 
import string
import pygsched.gssession as session
from pygsched.gsstructures import GSGroup, GSThread, GSHierarchy
import pygsched.gsprocutils as gsproc
import pykusp.configutility as config

import IPython.ipapi
ip = IPython.ipapi.get()

class LogLevels:
    NORMAL = 0
    VERBOSE = 1
    VERY_VERBOSE = 2
    DEBUG = 3
    VERBOSE_DEBUG = 4
    
class GS_IP:
    """
    A class to provide an interactive/interperator shell for thoe
    Group Scheduling API and utilities.
    """
    def __init__(self):
        self.gsched_session = session.GSSession(open=False)
        try:
            global Params
            Params.debug_level
        except NameError:
            class FallbackParams:
                debug_level = 0
                verbose_level = 0

            Params = FallbackParams()


        
    def write(self, out_string, log_level=LogLevels.NORMAL):
        """
        Writes the out_string to stdout. This is more flexible than
        'print' because it provides a log_level argument that works
        with the global Params object to see if the verbosity and/or
        debug levels are high enough to write out diagnostic messages.
        """
        write_message = False
        if log_level == LogLevels.NORMAL:
            write_message = True
        else:
            if log_level >= LogLevels.DEBUG:
                # log_level - 3 to translate it to proper debug level.
                if log_level-2 <= Params.debug_level:
                    write_message = True
                    
            else:
                if log_level >= LogLevels.VERBOSE and \
                        log_level <= LogLevels.VERY_VERBOSE:
                    if log_level >= Params.verbose_level:
                        write_message = True

        if write_message:
            sys.stdout.write(out_string)
                

    

    ##############################################
    # Private Methods 
    # -- Background helper routines for the public
    # callable routines, Should not be callable by the user.
    ##############################################

    def find_empty_group(self, group_name):
        gsh = gsproc.parse()
        matching_groups = filter( lambda member: isinstance(member, GSGroup) and \
                                      member.get_name() == group_name,
                                  gsh.get_empty_groups())
        if len(matching_groups) == 0:
            self.write("No empty Groups with name matching: %s\n" % group_name, LogLevels.DEBUG)
            return None
        if len(matching_groups) > 1:
            self.write( "More than one group matched with that group name,"
                        " returning first group matched.\n")
        return matching_groups[0]
        

    def remove_group_R(self, group):
        if not isinstance(group, GSGroup):
            raise TypeError("Error(1): group is not of type GSGroup\n", group.__class__) 
    
        self.write('Uninstalling group: %s\n' % str(group))
        self.gsched_session.uninstall_group(group)
        members = group.get_members()
        mem_threads = filter(lambda member: isinstance(member, GSThread),
                         members)
        mem_groups = filter(lambda member: isinstance(member, GSGroup),
                        members)
        
        # First order of business is to clear the exclusive control
        # of each thread, remove them from the group, and kill them.
        for mem_thread in mem_threads:
            self.write('Removing thread: %s\n' % mem_thread.get_name())
            self.gsched_session.thread_clear_exclusive(mem_thread)
            self.gsched_session.remove_thread_from_group(group, mem_thread)
        
        for mem_thread in mem_threads:
            pid = int(mem_thread.get_pid())
            if os.path.exists("/proc/%i"%pid):
                self.write("Sending signal SIGKILL to process: %i\n" % pid, 
                           LogLevels.DEBUG)
                os.kill(pid, signal.SIGKILL)
            else:
                self.write("Process %i not found, skipping process kill step.\n" % pid,
                           LogLevels.DEBUG)

        # Remove each member group from the parent group.
        for mem_group in mem_groups:
            self.write('Removing group: %s\n' % str(mem_group))
            self.gsched_session.remove_group_from_group(group, mem_group)
            
        # Now that all of the members have been removed, it is
        # possible to destroy the group.

        self.write('Destroying group: %s\n' % str(group))
        self.gsched_session.destroy_group(group)

        # It is unlikely that we will re-attach these hanging groups
        # to other hierarchies, so recursively destroy all member
        # groups as well.
        #
        for mem_group in mem_groups:
            self.remove_group_R(mem_group)

    ######## END PRIVATE METHODS #############
    






setattr(ip, 'gsched_ip', GS_IP())

########################################
#  Important Function Decorators 
########################################

# Wraps a gsched_* function to transform the space delimiated string
# args into an list of strings.  IPython sends the arguments to the
# magic function in the single string format, which is inconvient, and
# would have to be applied to all of the functions anyway -- hence the
# decorator.
def split_args(function):
    def wrapped_function(self, args): 
        function(self, *args.split(' '))
    wrapped_function.__doc__ = function.__doc__
    wrapped_function.__name__ = function.__name__
    return wrapped_function

# Ensures that there is not a continuously open GSSession by wrapping
# the functions that use GSSession to open the gschedapi file
# descriptor before use, and closing it after use.
def manage_session(function):
    def wrapped_function(self, *args): 
        self.api.gsched_ip.gsched_session.open()
        function(self, *args)
        self.api.gsched_ip.gsched_session.close()
    wrapped_function.__doc__ = function.__doc__
    wrapped_function.__name__ = function.__name__
    return wrapped_function
    
  ###### END DECORATORS #######


##################################################################
# Public "Command" or "Action" Methods 
#        
# These are callable by the user by typing their name, and sending
# a list of space seperated arguements. The help text for each
# method is generated by its docstring.
###################################################################

@manage_session
@split_args
def gsched_create_group(self, group=None, schedule=None, *args):
    """Creates a new uninstalled group within group scheduling.
    
    usage: create_group <group-name> <schedule-name>
    
    Note: Extra arguments to create group are ignored.
    """
    
    # Check if the group and schedule are specified, print error
    # messages and return from the method if they are not since
    # group creation will fail.
    if group is None:
        self.api.gsched_ip.write("Error: No Group specified to create!\n")
        return 
    
    if schedule is None:
        self.api.gsched_ip.write("Error: No schedule specified for Group %s\n" % group)
        return 
    
    if len(args) > 0:
        # There were extra arguments given, so just ignore them
        # for now.
        self.api.gsched_ip.write("Warning: Ignoring extra arguments to create_group: \n")
        for arg in args: self.api.gsched_ip.write("%s\n" % arg)
        self.api.gsched_ip.write("\n")
        
        
    # Attempt to create the group and store the return value of the 
    # group retrieved by the GSSession backend.
    retval = self.api.gsched_ip.gsched_session.create_group(group, schedule)
        
    if retval == 0:
        # Great, group creation was successful
        self.api.gsched_ip.write("Created Group %s with schedule %s.\n" % (group, schedule))
    else:
        # No there was an error, tell the user that group creation
        # failed and give the error code which is designated by
        # the return value.
        self.api.gsched_ip.write("Error: Unable to create Group"
                   " %s with schedule %s (Error Code %i).\n" % (group, schedule, retval))

        
ip.expose_magic("gsched_create_group", gsched_create_group)

@manage_session
@split_args
def gsched_add_thread(self, thread=None, group=None, *args):
    """*codestub* Registers a CCSM named member task join a Group.
    """
    pass

ip.expose_magic("gsched_add_thread", gsched_add_thread)

@manage_session
@split_args
def gsched_add_group(self, group=None, member_group=None, *args):
    """Registers a CCSM named Group to join another Group.
    
    usage: add_group_by_name <group-name> <group-to-add-name>
    """
    if group is None:
        self.api.gsched_ip.write("Error: No parent Group specified!\n")
        return 
    
    if member_group is None:
        self.api.gsched_ip.write("Error: No member Group specified to add to `%s'\n" % group)
        return 
    
    if len(args) > 0:
        # There were extra arguments given, so just ignore them
        # for now.
        self.api.gsched_ip.write("Warning: Ignoring extra arguments to create_group: \n")
        for arg in args: self.api.gsched_ip.write("%s\n" % arg)
        self.api.gsched_ip.write("\n")


    # Attempt to create the group and store the return value of the 
    # group retrieved by the GSSession backend.
    retval = self.api.gsched_ip.gsched_session.add_group_by_name(group, member_group)
    
    if retval == 0:
        # Great, group creation was successful
        self.api.gsched_ip.write("Registered Group `%s' as a member of Group `%s'.\n" % (member_group, group))
    else:
        # No there was an error, tell the user that group creation
        # failed and give the error code which is designated by
        # the return value.
        self.api.gsched_ip.write("Error: Unable to register Group "
                   " `%s' as a member of Group `%s' "
                   "(Error Code %i).\n" % (member_group, group, retval))

ip.expose_magic("gsched_add_group", gsched_add_group)
        
@manage_session
@split_args
def gsched_leave_group(self, *args):
    """*code stub* Have a member Group leave another Group.
    """
    pass
ip.expose_magic("gsched_leave_group", gsched_leave_group)

@manage_session
@split_args
def gsched_set_exclusive(self, pid=None, *args):
    """Set a thread with some pid to have exclusive control.
    
    usage: set_exclusive <thread-pid>
    """
    self.api.gsched_ip.gsched_session.thread_set_exclusive(pid)
ip.expose_magic("gsched_set_exclusive", gsched_set_exclusive)

@manage_session
@split_args
def gsched_clear_exclusive(self, *args):
    """Clear the exclusive control attribute of a thread with some pid.
    
    usage: clear_exclusive <thread-pid>
    """
    self.api.gsched_ip.gsched_session.thread_clear_exclusive(pid)
    pass
ip.expose_magic("gsched_clear_exclusive", gsched_clear_exclusive)

@split_args
def gsched_print_group(self, *args):
    """Prints the SDF and members for a given group.
    
    usage: group_info <group-name>
        
    The format of the information for each group is in the form:
        
    group_name (SDF)
    (T) - member_thread0 (PID)
    (T) - member_thread1 (PID)
    (G) - member_group (SDF)
    """
    if len(args) == 0:
        # No groups, stop action
        self.api.gsched_ip.write("\nNo group specified.\n")
        return
    elif len(args) > 1:
        # More than one group specified, we think, so call group
        # info individually for each group.
        for grp in args: 
            self.api.gsched_ip.group_info(grp)
        return

    # There should only be one element in args, the name of the
    # group about which the user wants info.
    group_name = args[0]
    group = self.api.gsched_ip.find_group(group_name)
    if group is None:
        # Apparently the group doesn't exist in the hierarchy.
        self.api.gsched_ip.write("Error: Unable to display information "\
                       "for unknown Group `%s'\n" % group_name)
        return
        
    self.api.gsched_ip.write("\n")
    # Print out the string representation of the group
    # (i.e. <group-name> (<sdf>))
    self.api.gsched_ip.write(str(group)+'\n')

    members = group.get_members()
    
    # We want to give seperate representations to each of member
    # types (group and thread) so make two sublists from the
    # members list segregated by member type.
    mem_threads = filter(lambda member: isinstance(member, GSThread),
                         members)
    mem_groups = filter(lambda member: isinstance(member, GSGroup),
                        members)

        
    for mem_group in mem_groups:
        # Print each member group with 4 spaces of padding, for
        # clarity.
        thread_string = "    (G) - %s\n" % str(mem_group)
        self.api.gsched_ip.write(thread_string)


    for mem_thread in mem_threads:
        # Print each member thread with 4 spaces of padding, for
        # clarity.
        thread_string = "    (T) - %s\n" % str(mem_thread)
        self.api.gsched_ip.write(thread_string)

    self.api.gsched_ip.write('\n')
ip.expose_magic("gsched_print_group", gsched_print_group)


@split_args
def gsched_print_groups(self, *args):
    """Print all of the groups on the system.
    
    usage: gsched_print_groups
    
    Displays all of the Groups that are currently managed by Group
    Scheduling. Groups that are still in Group Scheduling but are
    not installed are currently refered to as `empty groups' and
    are not part of the system Hierarchy. So there are two
    different lists outputted by print_groups:
    
    Groups in the main hierarchy [ name (sdf) ]:
    > group_0 (some_sdf)
    > group_1 (another_sdf)
    ...
    
    Empty or unattached Groups [ name (sdf) ]:
    > unattached_group_0 (some_sdf)
    > unattached_group_1 (another_sdf)
    ...

    Note that, this method will not print out the essential Group
    Scheduling root Group `gsched_top_seq_group' since it is not
    editable.
    """
    gsh = gsproc.parse()
    groups = filter( lambda member: isinstance(member, GSGroup),
                     gsh.get_all_members())

    self.api.gsched_ip.write('\n')
    self.api.gsched_ip.write("Groups in the main hierarchy [ name (sdf) ]:\n")
    if len(groups) > 0:
        for group in groups: self.api.gsched_ip.write("> %s\n" % str(group))
    else:
        self.api.gsched_ip.write("None\n")
      
    groups = gsh.get_empty_groups()
    self.api.gsched_ip.write("\nEmtpy or unattached Groups [ name (sdf) ]:\n")
    if len(groups) > 0:
        for group in groups: self.api.gsched_ip.write("> %s\n" % str(group))
    else:
        self.api.gsched_ip.write("None\n")
        
    self.api.gsched_ip.write('\n')
ip.expose_magic("gsched_print_groups", gsched_print_groups)

@manage_session
@split_args
def gsched_cleanup(self, *args):
    """Destroyes all uninstalled Groups and empty (memberless) Groups.
    
    usage: cleanup_groups
    """
    gsh = gsproc.parse()
        

    self.api.gsched_ip.write("Removing groups:\n")
    for group in gsh.get_empty_groups():
        self.api.gsched_ip.write("%s\n" % str(group))
        self.api.gsched_ip.gsched_session.destroy_group(group.get_name())
    
    for member in gsh.get_all_members():
        if isinstance(member, GSGroup):
            if len(member.get_members()) == 0:
                group_name = member.get_name()
                self.api.gsched_ip.write("%s\n" % str(member))
                self.api.gsched_ip.remove_group(group_name)
ip.expose_magic("gsched_cleanup", gsched_cleanup)

@manage_session
@split_args
def gsched_remove_group(self, *args):
    """Recursively uninstall and destroy the Group and its members.
    
    usage: remove_group <group-name>
    
    """
    if len(args) == 0:
        self.api.gsched_ip.write( "Warning: You did not specify a group to remove\n")
        return

    if len(args) > 1:
        for grp in args: self.api.gsched_ip.remove_group(grp)
        return
    
    group_name = args[0]
    group = self.api.gsched_ip.find_group(group_name)
    if group is None:
        self.api.gsched_ip.write( "Warning: Cannot remove non-existent Group: %s\n" % group_name)
        return
            
    self.api.gsched_ip.remove_group_R(group)
ip.expose_magic("gsched_remove_group", gsched_remove_group)

@manage_session
@split_args
def gsched_uninstall_group(self, *args):
    """Uninstalls a Group from Group Scheduling.
    
    usage: uninstall_group <group-name>
    
    Note: Uninstalling a group one of the prerequisites before
    destroying a group.
    """
    if len(args) == 0:
        # User didnt specify a group to remove, tell them there
        # error and stop this method.
        self.api.gsched_ip.write( "Warning: You did not specify a group to uninstall\n")
        return
    if len(args) > 1:
        for grp in args: self.api.gsched_ip.uninstall_group(grp)
        return

    group = self.api.gsched_ip.find_group(group_name)
    if group is None:
        self.api.gsched_ip.write( "Warning: Cannot uninstall non-existent Group: %s\n" % group_name)
            
        
    self.api.gsched_ip.gsched_session.uninstall_group(group)
ip.expose_magic("gsched_uninstall_group", gsched_uninstall_group)
    

@manage_session
@split_args
def gsched_destroy_group(self, *args):
    """Destroys the Group Struct of the Group.
        
    usage: destroy_group <group-name>
    
    Uses the GSSession backend to destroy a Group <group-name>. To
    be destroyed the group must first be uninstalled from Group
    Scheduling and have no members. If both of the previous
    conditions are not met, then removing the Group will fail.
    """

    if len(args) == 0:
        # No group specified to destroy, print the warning, and
        # the help about destroy_group.
        self.api.gsched_ip.write( "Warning: You did not specify a group to destroy\n")
        return

    if len(args) > 1:
        # Assume that if there are multiple arguments, that they
        # are all groups to be destroyed, so call the destroy_group 
        # with each group individually.
        for grp in args: self.api.gsched_ip.destroy_group(grp)
        return
            
    # len(args) should only be 1 after the previous two if
    # statments are not entered, and that element is the name of
    # the group to destroy.
    group_name = args[0]
    group = self.api.gsched_ip.find_group(group_name)
    if group is None:
        # The group was not found in the main hierarchy, so check
        # the 'empty groups'.
        group = self.api.gsched_ip.find_empty_group(group_name)
        if group is None:
            # The group was not found in the empty_groups so it
            # doesnt exists, quit this action.
            self.api.gsched_ip.write("Error: Unable to destroy unknown Group `%s'\n" % group_name)
            return 

    # Attempt to destroy the group
    retval = self.api.gsched_ip.gsched_session.destroy_group(group)

    if retval == 0:
        self.api.gsched_ip.write("Destroyed %s successfully\n" % group)
    else:
        self.api.gsched_ip.write("Unable to destroy %s (Error Code %i)\n" % (group, retval))
ip.expose_magic("gsched_destroy_group", gsched_destroy_group)

@manage_session
@split_args
def gsched_load_configfile(self, *args):
    """Loads a Group Scheduling Configuration file into group scheduling.
    """
    if len(args) == 0:
        return
    if len(args) > 1:
        return
    
    inputfile = args[0]
    gsh_config_dict = config.parse_configfile(inputfile)
    gsh = GSHierarchy(gsh_config_dict)
    session.load_hierarchy(gsh, self.api.gsched_ip.gsched_session)
ip.expose_magic("gsched_load_configfile", gsched_load_configfile)    


@split_args
def gsched_print_system(self, *args):
    """Prints the whole system hierarchy (all installed Groups and
    thier members) in a tree format.
    """
    gsh = gsproc.parse()
    gsh.pprint()
ip.expose_magic("gsched_print_system", gsched_print_system)

    
    ########### END PUBLIC COMMAND METHODS ##########
        
