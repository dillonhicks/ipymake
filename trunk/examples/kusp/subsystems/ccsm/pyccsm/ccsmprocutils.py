#!/bin/env python
"""
===========================================================================
:mod:`ccsmprocutils` -- Computation Component Set Manager Procfs Utilities
===========================================================================
    :synopsis: Contains functions for reading and parsing the 
        CCSM proc interface '/proc/ccsm.'

.. moduleauthor:  Dillon Hicks <hhicks@ittc.ku.edu>

**Current Version 1.0**

Reading
======================

Parsing
======================

Module Changes
===============

*Version* *(YYYY-MM-DD)*: *Changes*

* 1.0 (2009-10-10): First completed and tested version.

"""

from ccsmstructures import *

def read():
    """
    :return: CCSM **/proc/ccsm** file read as a string.
    """
    procCCSM = open( "/proc/ccsm", 'r' )
    retval = procCCSM.read()
    procCCSM.close()
    return retval
    
def readlines():
    """
    :return: CCSM **/proc/ccsm** file read as a list of strings. 
    """
    procCCSM = open( "/proc/ccsm", 'r' )
    retval = procCCSM.readlines()
    procCCSM.close()
    return retval
        

def parse(raw_proc=None):
    """
    Parses the CCSM **/proc/ccsm** file into a list of 
    `CCSMSet` objects, each `CCSMSet` in the list representing
    a root (parentless) set.
    
    The formats of the /proc/ccsm lines are:
    
    **Sets**::
    
        set | <name> | <list-of-flags> | <set-type>
        
    **Members**::
    
        member | <name> | <parent-name> 
    
    :param raw_proc: This can be used to parse a saved /proc/ccsm read
        if so desired. If `raw_proc` is None, then it reads the current
        /proc/ccsm.
    :type raw_proc: string, list of strings, or None
    :returns: The root `CCSMSet` that describe the Sets that CCSM is managing.
    :rtype: List of `CCSMSet` objects
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
        raise TypeError( "ERROR ccsmprocutils.parse: Cannot parse argument "
                        "rawProc, it is not of type string or list.", type( raw_proc ) )
    
    # Name based dictionary to hold the 
    # CCSMSet object parsed from proc.
    sets = {}
    root_sets = []
    # Memberships are (member-name, parent-name) pairs,
    # see Members in the docstring.
    memberships = []
    NAME, PARENT_NAME = range(2)
    
    for text_line in raw_proc:
        # for each line of the proc file
        if text_line.startswith('set'):
            # It is a line with the set's information
            # so make a CCSMSet out of the information 
            # on this line.
            set, name, flags, set_type = text_line.split('|')
            flags = flags.strip()
            flags = flags.split(' ')
            name = name.strip()
            sets[name] = CCSMSet(name, flags)
            if set_type.strip() == '0':
                # A type of 0 denotes a root CCSMSet, so
                # make a CCSMHierarchy out of it and append
                # it to the list of known hierarchies.
                root_sets.append(sets[name])
        elif text_line.startswith('member'):
            # The current line describes a parent->child
            # membership between sets.
            # Preserve this as a (child-name, parent-name)
            # tuple.
            member, name, parent = text_line.split('|')
            name = name.strip()
            parent = parent.strip()
            memberships.append((name, parent))
            
    for pair in memberships:
        # for each membership pair
        # grab the  child and the parent from
        # the list of sets. Then add that child 
        # to the parents member sets.
        child = sets[pair[NAME]]
        parent = sets[pair[PARENT_NAME]]
        parent.add_member(child)    
           
    
    return root_sets

if __name__=='__main__':
    for set in parse():
        set.pprint()
