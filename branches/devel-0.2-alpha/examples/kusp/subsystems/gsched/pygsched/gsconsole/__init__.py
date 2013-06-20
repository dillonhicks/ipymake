"""
:mod:`gsconsole` -- Group Scheduling Commandline Console
==========================================================

"""
import sys
import os
import signal 
import string
import pygsched.gssession as session
from pygsched.gshierarchy import GSGroup, GSThread, GSHierarchy
import pygsched.gsprocutils as gsproc
import pykusp.configutility as config
from pykusp.devutils.kuspconsole import *

class GSConsole(KUSPConsole):
    """
    A class to provide an interactive/interperator shell for thoe
    Group Scheduling API and utilities.
    """
    def __init__(self):
        KUSPConsole.__init__(self, 'pygsched.gsconsole.gsmethods')
        self.gsched_session = session.GSSession()
        self.prompt = 'gsched> '
        self.banner = \
"""
================================================
KUSP Group Scheduling API Shell

Type `help' for commands or `help <command>' 
for extended help about particular commands.
================================================
"""
            

    ##############################################
    # Private Methods -- Background helper routines for the public
    # callable routines (see gsmethods), Should not be callable by the
    # user.
    ##############################################


    def find_group(self, group_name):
        """Finds a group in the hierarchy that is not an
        empyt/unattached group.
        """
        gsh = gsproc.parse()
        matching_groups = filter( lambda member: isinstance(member, GSGroup) and \
                                      member.get_name() == group_name,
                                  gsh.get_members())
        if len(matching_groups) == 0:
            self.write("No Groups with name matching: %s\n" % group_name, LogLevels.DEBUG)
            return None
        if len(matching_groups) > 1:
            self.write( "More than one group matched with that group name,"
                        " returning first group matched.\n")
        return matching_groups[0]

    def find_empty_group(self, group_name):
        gsh = gsproc.parse()
        matching_groups = filter( lambda member: isinstance(member, GSGroup) and \
                                      member.get_name() == group_name,
                                  gsh.get_unattached_members())
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

        # It is unlikely that we will re-attach these hanging groups
        # to other hierarchies, so recursively destroy all member
        # groups as well. This will make sure that they are removed
        # and destroyed before attempting to destroy the current
        # group.
        for mem_group in mem_groups:
            self.remove_group_R(mem_group)
        
        parent = group.get_parent()
        if not parent is None:
            self.write('Removing group: %s\n' % str(group))
            self.gsched_session.remove_group_from_group(parent, group)
    
        # Now that all of the members have been removed, it is
        # possible to destroy the group.
        self.write('Destroying group: %s\n' % str(group))
        self.gsched_session.destroy_group(group)


    ######## END PRIVATE METHODS #############
