#!/bin/env python

"""    
:mod:`gsprocutils` -- Gsched Proc Utilities
============================================= 
:synopsis: Contains functions for reading and parsing the 
        Group Scheduling proc interface */proc/group_sched.*

.. moduleauthor:  Dillon Hicks <hhicks@ittc.ku.edu>


Parsing the */proc/group_sched* interface is our primary way of
obtaining the Group Scheduling Hierarchy in the kernel. The proc
interface is not easily human readable, but the :mod:`gsprocutils`
provides a way to read and parse */proc/group_sched* to not only make
it human readable, but also build the hierarchy as a
:class:`gsstructures.GSHierarchy`.

.. contents::

**Reading the Group Scheduling proc file:**

There are two ways to read the Group Scheduling proc file with
:mod:`gsprocutils`. Either with :func:`gsprocutils.read` or
:func:`gsprocutils.readlines`, which wrap the python standard
:func:`file.read` and :func:`file.readlines` specifically for the
Group Scheduling proc file.


**The Format of** ``/proc/group_sched``:
    
    **Groups**::
    
    
        group | <name> | <sdf>
    
    **Group Member Data**::
    
        member | <member-struct-name> | <parent-name> | group | <group-name>
        
    
    **Member Tasks/Thread**::
    
        member | <member-name> | <parent-name> | task | <pid>


:func:`gsprocutils.parse`
-------------------------------

.. autofunction:: gsprocutils.parse

How to use :func:`parse` to create a :class:`gsstructures.GSHierarchy`
and show the contents of that hierarchy.

.. doctest:: 

   >>> import pygsched.gsproutils as gsproc
   >>> gsh = gsproc.parse()
   >>> print gsh
    GROUP SCHEDULING HIERARCHY : Root=gsched_top_seq_group
   ---------------------------------------------------------
   (G) - gsched_top_seq_group
       (G) - socket_pipeline
              (T) - thread-0
              (T) - thread-1
       (T) - thread-2
       (T) - thread-3
   

.. seealso::
   
   Class :class:`gshierarchy.GSHierarchy`

   Program :command:`gschedpprint`

:func:`gsprocutils.read`
----------------------------

.. autofunction:: gsprocutils.read

.. doctest::
   
   >>> import pygsched.gsprocutils as gsproc
   >>> print gsproc.read()
   group|gsched_top_seq_group|sdf_seq


:func:`gsprocutils.readlines`
-------------------------------

.. autofunction:: gsprocutils.readlines

.. doctest::

   >>> import pygsched.gsprocutils as gsproc
   >>> print gsproc.readlines()
   ['group|socket_pipeline|sdf_seq', 'member|thread-3|socket_pipeline|task|5210', 
   'group|gsched_top_seq_group|sdf_seq', 'member|socket_pipeline|gsched_top_seq_group|group|socket_pipeline']



"""

# Not included in the autodocs
"""
**Current Version 1.1**

Module Changes
===============

*Version* *(YYYY-MM-DD)* : *Changes*

* 1.0  (2009-10-04) : First completed and tested version.
* 1.1  (2009-10-11) : Fixed some small cosmetic errors, and switched
    doctring documentation to comply PEP-287.

TODO
----------------

* Comment the `parse()` function algorithm a bit better.

"""

from gshierarchy import GSThread, GSGroup, GSHierarchy

SYSTEM_ROOT_GROUP_NAME = 'gsched_top_seq_group'
NUMBER_FIELDS_GROUP = 3
NUMBER_FIELDS_MEMBER = 5

def read():
    """
    :return: Group Scheduling proc ouput string.
    """
    procGsched = open( "/proc/group_sched", 'r' )
    retval = procGsched.read()
    procGsched.close()
    return retval
    
def readlines():
    """
    :return: Reads the Group Scheduling proc file and 
        returns the lines as a list of strings.
    """
    procGsched = open( "/proc/group_sched", 'r' )
    retval = procGsched.readlines()
    procGsched.close()
    return retval
        

def parse(raw_proc=None):
    """
    Parses the Group Scheduling ``/proc/group_sched`` file into a 
    GSHierarchy data structure.
       
    """
    
    if raw_proc is None:
        # rawProc has not been specified,
        # so read /proc/gsched_proc to obtain something
        # to parse.
        # 
        raw_proc = readlines()
        
    elif type( raw_proc ) is str:
        # Split the string into a list of string of 
        # each line.
        #
        raw_proc = raw_proc.split( '\n' )
    elif type( raw_proc ) is list:
        # We want a list, so do nothing.
        #
        pass
    else:
        # The user has specified rawProc, it needs to be 
        # a string or a list of strings. If it isn't raise a TypeError.
        # 
        raise TypeError( "ERROR GschedProc.parse: Cannot parse argument "
                        "rawProc, it is not of type string or list.", type( raw_proc ) )
    
    unattached_members = {}
    unattached_groups = {}
    
    for line in raw_proc:
        fields = line.split( '|' )
        
        if len(fields) == NUMBER_FIELDS_GROUP:
            name, sdf = fields[1:]
            group = GSGroup(name, member_name=name, sdf=sdf.strip())
            unattached_groups[name] = group
            
        if len(fields) == NUMBER_FIELDS_MEMBER:
            name, parent_name, gs_type, type_data = fields[1:]
            type_data=type_data.strip() # getting rid of a bloody '\n' that is problematic
            
            if gs_type == 'task':
                member = GSThread(name, parent_name, pid=0, 
                                  member_data=int(type_data), 
                                  doc=type_data) 
                unattached_members[name] = member
                
            elif gs_type == 'group':
                if name[-4:] == '_mem':
                    # To get rid of the '_mem' at the end of the group's
                    # member structure name.
                    name = name[0:-4]
                if unattached_groups.has_key(name):
                    group = unattached_groups[name]
                    group.set_parent(parent_name)
                    group.set_docstring(type_data)
                else:
                    raise KeyError("The Group Scheduling /proc/group_sched " 
                                   "information does contain the expected "
                                   "member structure information for the "
                                   "group %s.\nParsing Failed" % 
                                   name)
    
            else:
                raise ValueError('Found unexpected Group Scheduling' 
                                 ' structure type %s in the Group'
                                 ' Scheduling /proc/group_sched'
                                 ' information. Parsing Failed.' % gs_type)
                
    
    
    root_group = None
    if unattached_groups.has_key(SYSTEM_ROOT_GROUP_NAME):
        root_group = unattached_groups.pop(SYSTEM_ROOT_GROUP_NAME)
    else:
        raise KeyError("The Group Scheduling /proc/group_sched " 
                       "information does contain the expected "
                       "System Root Group %s.\nParsing Failed" % 
                       SYSTEM_ROOT_GROUP_NAME)
    
    
    
    def build_gsh_R(root_group):
        root_name = root_group.get_name()
        for member_group in unattached_groups.values():
            if member_group.get_parent() == root_name:
                build_gsh_R(member_group)
                root_group.add_member(member_group)
                
        for thread in unattached_members.values():
            if thread.get_parent() == root_name:
                root_group.add_member(thread)
        
        
        pass
    
    build_gsh_R(root_group)
    gsh = GSHierarchy(root_group)

    empty_groups = {}
    for group in unattached_groups.values():
        if not group in gsh.get_members():
            group_name = group.get_name()
            empty_groups[group_name] = group
        

    def build_empty_gsh_R(root_group):
        root_name = root_group.get_name()
        for member_group in empty_groups.values():
            if member_group.get_parent() == root_name:
                build_empty_gsh_R(member_group)
                root_group.add_group(member_group)

    for group in empty_groups.values():
        build_empty_gsh_R(group)
    
    for group in empty_groups.values():
        if group.get_parent() is None:
           gsh.add_unattached_member(group)
             
    return gsh
