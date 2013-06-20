"""
:mod:`ccsmstructures` -- Computation Component Set Manager Objects 
====================================================================
    :synopsis: Python data structures which encapsulate the information for
        Computation Component Sets in the kernel.

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>

**Current Version: 1.0** 

:class:`CCSMSet` -- The CCSM Set Class
=======================================

The `CCSMSet` class holds four important pieces of information that
reflect the information that is stored by the Linux CCSM Kernel Module.

* **Name** : The *unique* name of the `CCSMSet`.
* Flags: The attribute flags for the `CCSMSet`.
* Members: The list `CCSMSet` members for the current `CCSMSet`.
* Parent: The parent `CCSMSet` of the current `CCSMSet`.

With this information stored in a Python data structure it then becomes easier
to use this information to create powerful tools that allow us to analyze and
manipulate CCSM Sets in the Python, rather than C, domain. Currently, 
`CCSMSet` objects are used to recreate CCSM sets in the kernel.
This is done using `ccsmprocutils` to parse the ``/proc/ccsm`` file 
into a list of `CCSMSets`.  


:class:`CCSMFlags` -- Set Attribute Flags 
=============================================

.. note:: These are not rigidly defined or used at the moment,
    but will be used in the future. They are listed below for reference.

.. todo:: Dillon -- Figure out what these are.

* TASK
* PIPE
* FIFO
* SHARED_MEM
* FILE
* MUTEX
* FUTEX
* SOCKET
  

Module Changes
================

*Version* *(YYYY-MM-DD)*: *Changes*
    
* 1.0 (2009-10-11): First completed version

"""

class CCSMFlags:
    """
    The `CCSMFlags` represent all of the flags that can be used
    in the kernel for the kernel CCSM Set attributes.
       
    * TASK
    * PIPE  
    * FIFO 
    * SHARED_MEM
    * FILE
    * MUTEX
    * FUTEX
    * SOCKET
    """
    TASK = 'task'
    PIPE = 'pipe'
    FIFO = 'fifo'
    SHARED_MEM = 'shared_mem'
    SOCKET = 'socket'
    FILE = 'file'
    MUTEX = 'mutex'
    FUTEX = 'futex'

    ALL_FLAGS = [TASK, PIPE, FIFO, SHARED_MEM, 
            SOCKET, FILE, MUTEX, FUTEX]

class CCSMSet:
    """
    A data structure to encapsulate CCSM Set data in the Python.

    :param name: The name of the `CCSMSet`. The name must be unique.
    :type name: string
    :param flags: The attribute flags for the `CCSMSet`. 
    :type flags: string or list of strings
    :param parent: The CCSMSet parent, if it is a member (child) set.
    :type parent: `CCSMSet` or None
    """
    def __init__(self, name, flags=[], parent=None):
        """

        """
        self.name = name
        self.flags = flags
        self.parent = parent
        self.members = []
        
    def get_name(self): 
        """
        :returns: The name of the `CCSMSet`.
        :rtype: string
        """
        return self.name
    
    def set_name(self, name):
        """
        Sets the name of the `CCSMSet` to name.
        
        .. todo:: Dillon, you need to check for uniqueness of the name
            within the set.
        
        :param name: The desired name of the `CCSMSet`. If name is not a string
            then there will be a type coercion to string (i.e. *str(name)*).
        :type name: string
        """
        if not type(name) is str:
            name = str(name) 
        self.name = name
    
    def get_flags(self, flags): 
        """
        :returns: The attribute flags of the `CCSMSet`.
        :rtype: list of strings
        """
        return self.flags
    
    def set_flags(self, flags):
        """
        Sets the flags of the `CCSMSet` to flags.
         
        .. todo:: Add checking to make sure the flags are
            valid.
        """
        self.flags = flags    
    
    def get_parent(self):
        """
        :returns: The parent of this `CCSMSet`.
        :rtype: CCSMSet or None
        """
        return self.parent
    
    def set_parent(self, parent):
        """
        Sets the parent of the `CCSMSet` to parent, if parent is a `CCSMSet`
        or None.
        
        :param parent: The new parent for the `CCSMSet`.
        :type parent: CCSMSet or None
        """
        if isinstance(parent, CCSMSet) or parent is None:
            self.parent = parent
        else:
            raise TypeError("Error setting parent: CCSMSet must" 
                            " have a parent that is a CCSMSet", 
                            parent.__class__)

    
    def get_set_members(self):
        """
        :returns: The members for this `CCSMSet`. See `get_all_members()`
            for getting every member for the set as a whole.
        :rtype: list of `CCSMSet` objects
        """
        return self.members
    
    def add_member(self, member):
        """
        Adds a member to the `CCSMSet`. 
        
        When the member is added to another `CCSMSet` its parent is
        set to the `CCSMSet` to which it was added. If member is not a `CCSMSet`
        then a TypeError is raised.
        
        :raises TypeError: If `member` is not a `CCSMSet`.
        :param member: The member to add to this 
        """
        if isinstance(member, CCSMSet):
            member.set_parent(self)
            self.members.append(member)
        else:
            raise TypeError("Error adding member: CCSMSet must" 
                            " members must be ", member.__class__)
    
    def is_root_set(self):
        """
        :returns: If the `CCSMSet` is a root set (a set with no parent).
        :rtype: boolean
        """
        return self.parent is None
        
    def pprint(self, indent_level=0, step=4):
        """
        Pretty prints this `CCSMSet` and its member subsets
        with increasing indentation for each lower level of the
        subset tree::
            
            pipeline_group
                signal_gen_group
                    thread-1
                    thread-2
                    thread-3
                signal_rcvd_group
                    thread-4
                    thread-5
                    thread-6
    
        :param indent_level: The current indentation level (number of spaces)
            to use for printing the information for this `CCSMSet`.
        :type indent_level: integer
        :param step: The extra indentation to have at every lower level.
        :type step: integer
        """
        print ' '*indent_level + self.get_name()
        for mem in self.members:
            mem.pprint(indent_level+step,step)
    
    def get_all_members(self):
        """
        Recursively get all members in this CCSMSet and its subsets.
        
        :returns: All members within this set and it's subsets.
        :rtype: list of `CCSMSet` objects
        """
        # Need a list to hold the members
        all_members = []
        # Internal recursive function 
        # that recursively travels down the 
        # tree created by the sets and subsets
        # to get all member.
        def populate_members(root_set):
            # Add the current set to the members
            all_members.append(root_set)
            for mem in root_set.get_set_members():
                # For each of the current sets members
                # call this function again with them
                # as the root_set to add the member set
                # and its subset members.
                populate_members(mem)
        # Start the search for members
        # at this CCSMSet.
        populate_members(self)
        return all_members
        
    def get_root_set(self):
        """
        :returns: The root (parentless) `CCSMSet` from the set which this 
            `CCSMSet` is either a member or the root.
        :rtype: CCSMSet 
        """
        if self.is_root_set():
            # Check for a lack of parent passes.
            # This must be the root, return this CCSMSet.
            return self
        # This isnt a parentless CCSMSet so
        # get its parent.
        parent = self.get_parent()
        # Do this check again on the parent CCSMSet.
        return parent.get_root_set()
     
