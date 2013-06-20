""" 
===============================================
:mod:`gssession` -- Group Scheduling Sessions
===============================================
    :synopsis: Python module providing a high level interface with 
        the Group Scheduling API. It allows for subclassing the interface
        module Controller class as used in gschedctrl.

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>

"""

# not included in autodocs
"""
**Current Version 1.3.1**


Module Changes
==================

*Version* *(YYYY-MM-DD)* : *Changes*

* 1.0 : Original stable code.
* 1.1 : Start to change code to conform to PEP-008 by changing
          function names to def i_am_a_function() from 
          def iAmAFunction()
* 1.2 (2009-10-15) : Fixed a small bug with setting the exclusivity of 
    thread/task member(it was not being set). Also starting conversion 
    of intra-module documentation to conform with PEP-287, this is 
    the new reStructured Text format for docstrings.
* 1.2.1 (2009-11-22) : Adding groups to groups was mistakenly being 
    done with grp_name_join_group() instead of grp_join_group(). 
    So the change was made and now groups are successfully being 
    added to other groups.
* 1.3: (2009-11-25): Rewrote the whole module to be cleaner using 
     the enforcetypes module which helps readability by taking the 
     argument type checking out of the main body of the method. Also
     implemented a new _manage_session decorator that opens and closes
     the gsched file descriptor on a per-action basis. This was done
     with the intent to produce more safe code, since the end user would
     never have to 'close' the session.
* 1.3.1: (2009-11-27): Minor changes to reflect the changes made in swtiching
     from pygsched.gsstructures to the new gshierarchy module.-- A few function
     call name changes.

"""
import sys
import os
import pykusp.configutility as config
from pykusp.devutils.enforcetypes import *
import pygsched.gschedapi as gsched
from pygsched.gshierarchy import GSGroup, GSThread, GSHierarchy, MemberAttributes


def load_hierarchy(gsh_config):
    """
    Loads the Group Scheduling Hierarchy gsh into Group Scheduling
    in the kernel. 
    
    :param gsh: The Group Scheduling Hierarchy to load.
    :type gsh: :class:`gsstructures.GSHierarchy`
    :returns: The created session.
    :rtype: :class:`GSSession`
    """
    # Create session, therefore obtaining/opening the 
    # Group Scheduling file descriptor.
    
    session = GSSession()
    gsh_dict = config.parse_configfile(gsh_config)
    gsh = GSHierarchy(gsh_dict)

    # Loading the tree using a recursive function.
    # This is only used internally, so there was not
    # a reason to have then as an external function.
    # 
    def load_R(member, parent=None):
        """This function recursively loads a name based Group 
        Scheduling Hierarchy with the root 'member' into the 
        kernel through the pygsched.gschedapi. It does not 
        'install' loaded hierarchy, which is needed to 
        use the hierarchy.
        """
        if isinstance(member, GSGroup):
            # If the current member is a group:
            # Get the name of the GSGroup and the SDF
            # used by the GSGroup and create the 
            # group through the API with the obtained 
            # parameters.
            #
            group = member.get_name()
            sdf = member.get_sdf()
            session.create_group(group, sdf)

            session.set_group_options(member)

            for child in member.get_members():
                # After the group has been created on the kernel side
                # Recursively load all children by iterating
                # through all the members of the GSGroup.
                load_R(child, member )
            
            if not parent is None:
                # If the parent is None, it is the top level root 
                # of the Group Scheduling Hierarchy which will
                # be installed directly to the 
                # group_sched_top_seq group. Otherwise it is a
                # child group and should be added to the parent
                # above it in the recursion.
                #
                parent_name = parent.get_name()
                session.add_group_to_group(parent_name, group)
        elif isinstance(member, GSThread):
            # IF the member is a GSThread, get the name of the
            # thread.
            #
            thread_name = member.get_name()
            is_exclusive = int(member.has_attribute(MemberAttributes.EXCLUSIVE))
            if not parent is None:
                # Sanity check, the parent should never be 
                # None if the current member is a thread. 
                # A thread can never be installed directly
                # to group scheduling and it must have a parent
                # group.
                #
                parent_name = parent.get_name()
                session.add_thread_to_group(parent_name, thread_name, is_exclusive)
            else:
                
                raise TypeError("Cannot load the Group Scheduling Hierarchy: Attempted"
                                " to add Thread to None.", parent)
        else:
            # It the member is not a GSGroup or GSThread it is a type
            # that is not expected, and not a valid GS data structure
            # so raise an error.
            #
            raise TypeError("Cannot load the Group Scheduling Hierarchy: The "
                            "member is not a GSGroup or GSThread.", parent)
                
        pass
    
    # Getting the top level root of the Group 
    # Scheduling Hiearachy that the user wishes
    # to load. The recursive build obviously has
    # to start with the top level of the tree.
    #
    gshRoot = gsh.get_root_group()
    # Calling the recursive loading internal function
    # with the top level root of the hierarchy.
    #
    load_R(gshRoot)
    # After the Group Scheduling Hierarchy has been loaded,
    # the API needs the top level root of the hierarchy 
    # to install the Hierachy into the kernel.
    #
    session.install_group(gshRoot)
    return gsh


class GSSession:
    """
    GSSession manages one open Group Scheduling session. It 
    Keeps track of the current file descriptor. GSSession uses the Group
    Scheduling API to use the Group Scheduling kernel module to build
    and interact with Group Scheduling hierarchies in a higher
    level python environment. 
    
    .. seealso::
      
            * CCSM - Computation Component Set Manager
            * Group Scheduling Internals Manual
    """
    def __init__(self): self.gsched_session_fd = None     

    def _open(self):
        """
        Opens up ``/dev/group_sched`` for reading and writing, 
        and retrieves the appropriate file descriptor.
        """
        if self.gsched_session_fd is None:
            retval = gsched.grp_open()
            if retval < 0:
                print 'Group Scheduling API Error: %s' % os.strerror(-retval)
            else:
                self.gsched_session_fd = retval
        else:
            raise ValueError('Group Sched Cannot Be Opened: '
                             'Session Already Opened')
        return retval
            
    def _close(self):
        """
        Closes the file descriptor retrieved by :func:`_open`.
        """
        retval = 0
        if not self.gsched_session_fd is None:
            retval = gsched.grp_close(self.gsched_session_fd)
            self.gsched_session_fd = None
        else:
            raise ValueError('GSession Cannot Be Closed: '
                                 'Session is already closed')
           
        if retval < 0:
            print 'Group Scheduling Error: %s' % os.strerror(-retval)
        return retval
        
    def _args_to_string(method):
        def args_as_string_method(self, *args):
            string_args = []
            for arg in args:
                if not type(arg) is str:
                    if isinstance(arg, GSGroup) or \
                            isinstance(arg, GSThread):
                        arg = arg.get_name()
                    else:
                        arg = str(arg)
                string_args.append(arg)
            return method(self, *string_args)
        args_as_string_method.func_globals.update(method.func_globals)
        args_as_string_method.__name__ = method.__name__
        args_as_string_method.__doc__ = method.__doc__
        return args_as_string_method
    
    def _manage_session(method):
        """
        Special decorator function to open and close the group
        scheduling file descriptor after each operation.
        """
        def managed_method(self, *args):
            retval = 0
            if self._open() >= 0:
                try:
                    # No error condition with a positive return value, continue.
                    retval = method(self, *args)
                finally:
                    self._close()
                    return retval
            else:
                raise ValueError("Unable to open Group Scheduling file descriptor.")

        managed_method.func_globals.update(method.func_globals)
        managed_method.__name__ = method.__name__
        managed_method.__doc__ = method.__doc__
        return managed_method 
       
    @enforcetypes([str, GSGroup], str)
    @_args_to_string
    @_manage_session
    def create_group(self, name, schedule):
        """
        Tells Group Scheduling to create a Group named `name` with 
        SDF `schedule`. 
        
        
        :param name: Name of the group to be created.
        :type name: :class:`string`
        :param schedule: The name of the Scheduling Decision Function
        with which to create the group.
        :type schedule: :class:`string` 
        """
            
        if self.gsched_session_fd:
            retval = gsched.grp_create_group(self.gsched_session_fd, name, schedule)
            if retval < 0:
                print 'Group Scheduling Error: %s' % os.strerror(-retval)
        else:
            raise ValueError('Cannot create group, file descriptor is None.', 
                                 self.gsched_session_fd)
        return retval

    @enforcetypes([str, GSGroup], [str,GSGroup])            
    @_args_to_string
    @_manage_session
    def add_group_to_group(self, parent, group, member):
        """
        If the Group does not exist already as a 
        CCSM Set, then the appropriate callbacks are registered.
        
        :param parent: The parent group from which to remove a group.
        :type parent: :class:`string` or :class:`gsstructures.GSGroup`
        :param group: The group to remove from the parent.
        :param group: :class:`string` or :class:`gsstructures.GSGroup`
        """
        if self.gsched_session_fd:
            retval = gsched.grp_group_join_group(self.gsched_session_fd, parent, group, group )
            if retval < 0:
                print 'Group Scheduling Error: %s' % os.strerror(-retval)
        else:
            raise ValueError('Cannot add group, file descriptor is None.', 
                                 self.gsched_session_fd)
        return retval

    @_manage_session
    def set_group_options(self, group, options = None):
        """
        Set the options for a group.
        
        :param group: The group to set the options on.
        :param options: A set of options. The group's options will be used if none are provided.
        """

        if not options:
            options = group.get_attributes()

        group_opts = 0
        
        for k,v in GSGroup.options.iteritems():
            if k in options:
                group_opts |= v

        if self.gsched_session_fd:
            retval = gsched.grp_set_group_opts(self.gsched_session_fd, group.get_name(), int(group_opts) )
            if retval < 0:
                print 'Group Scheduling Error: %s' % os.strerror(-retval)
        else:
            raise ValueError('Cannot set group options, file descriptor is None.', 
                                 self.gsched_session_fd)
        return retval
    
    @enforcetypes([str, GSThread], [str,GSThread])
    @_args_to_string
    @_manage_session
    def add_thread_to_group(self, parent, thread, exclusive=1):
        """
        Adds a thread to Group Scheduling using a CCSM Name.
        
        :param parent: The parent group name to which to add the Thread.
        :param thread: The thread name to add to the parent group.
        :param exclusive: The exclusivity of the thread to be run only by group scheduling.
        """
        exclusive = int(exclusive)
        if self.gsched_session_fd:
            retval = gsched.grp_name_join_group(self.gsched_session_fd, parent, thread, exclusive)
            if retval < 0:
                print 'Group Scheduling Error: %s' % os.strerror(-retval)
        else:
            raise ValueError('Cannot add group, file descriptor is None.', 
                                 self.gsched_session_fd)
        
        return retval

 #   @enforcetypes([str, GSThread], int, str)
 #   @_args_to_string
    @_manage_session
    def add_pid_to_group(self, parent, pid, member_name):
        """
        Adds a thread to Group Scheduling using a CCSM Name.
        
        :param parent: The parent group name to which to add the Thread.
        :param thread: The thread name to add to the parent group.
        :param exclusive: The exclusivity of the thread to be run only by group scheduling.
        """
        pid = int(pid)
        if self.gsched_session_fd:
            retval = gsched.grp_pid_join_group(self.gsched_session_fd, parent, pid, member_name)
            if retval < 0:
                print 'Group Scheduling Error: %s' % os.strerror(-retval)
        else:
            raise ValueError('Cannot add group, file descriptor is None.', 
                                 self.gsched_session_fd)
        
        return retval

    
   
    @enforcetypes([str, GSGroup], [str, GSGroup]) 
    @_args_to_string
    @_manage_session
    def remove_group_from_group(self, parent, group):
        """Remove the group from the parent group using the
        group's and parent's unique CCSM name.
        
        :param parent: CCSM String name of the parent group.
        :param group: CCSM String name of the group to remove.
        """
        retval = gsched.grp_leave_group(self.gsched_session_fd, parent, group)
        if retval < 0:
            print 'Group Scheduling Error: %s' % os.strerror(-retval)
        return retval    

    @enforcetypes([str, GSGroup], [str, GSThread])
    @_args_to_string
    @_manage_session
    def remove_thread_from_group(self, parent, thread):
        """Remove the group from the parent group using the
        group's and parent's unique CCSM name.
        
        :param parent: CCSM String name of the parent group.
        :param group: CCSM String name of the group to remove.
        """
        retval = gsched.grp_leave_group(self.gsched_session_fd, parent, thread)
        if retval < 0:
            print 'Group Scheduling Error: %s' % os.strerror(-retval)
        return retval    
       
    @enforcetypes([GSGroup, str])
    @_args_to_string
    @_manage_session
    def install_group(self, group):
        """
        Installs the hierarchy with root as the CCSM 
        name of the root group of the hierarchy to install.
        
        :param root: CCSM Name of the root group of the
        hierarchy to install.
        
        .. note:: groupname and member_name are the same for now...
        """        
        retval = gsched.gsched_install_group(self.gsched_session_fd, group, group)
        if retval < 0:
            print 'Group Scheduling Error: %s' % os.strerror(-retval)
        return retval

    @enforcetypes([str, GSGroup])    
    @_args_to_string
    @_manage_session
    def uninstall_group(self, group):
        """
        Uninstalls the hierarchy with root as the CCSM 
        name of the root group of the hierarchy to uninstall.
        
        :param root: CCSM Name of the root group of the
        hierarchy to uninstall.
        
        .. note:: groupname and member_name are the same for now...
        
        """
        retval = gsched.gsched_uninstall_group(self.gsched_session_fd, root)
        if retval < 0:
            print 'Group Scheduling Error: %s' % os.strerror(-retval)
        return retval
    
    @enforcetypes(GSGroup)
    @_args_to_string
    @_manage_session
    def destroy_group(self, group):
        """ 
        Destroys the Group `group` given that 
        `group` is a :class:`string` or 
        :class:`gsstructures.GSHierarchy`.
        
        :param group: The group to destroy.
        :type group: string or :class:`gsstructures.GSHierarchy`
        """
        retval = gsched.grp_destroy_group(self.gsched_session_fd, group)
        if retval < 0:
            print 'Group Scheduling Error: %s' % os.strerror(-retval)
        return retval

    @enforcetypes([GSThread, str, int])
    @_manage_session
    def thread_set_exclusive(self, thread):
        if isinstance(thread, GSThread):
            pid = int(thread.get_pid())
        elif type(thread) is str:
            pid = int(thread)
        elif type(thread) is int:
            pid = thread
            
        retval = gsched.gsched_set_exclusive_control(self.gsched_session_fd, pid)
        if retval < 0:
            print 'Group Scheduling Error: %s' % os.strerror(-retval)
            
        return retval
            
    @enforcetypes([GSThread, str, int])
    @_manage_session
    def thread_clear_exclusive(self, thread):
        if isinstance(thread, GSThread):
            pid = int(thread.get_pid())
        elif type(thread) is str:
            pid = int(thread)
        elif type(thread) is int:
            pid = thread
                
        retval = gsched.gsched_clear_exclusive_control(self.gsched_session_fd, pid)
        if retval < 0:
            print 'Group Scheduling Error: %s' % os.strerror(-retval)
        return retval
