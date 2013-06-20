# $Id$
#
# AUTHOR(s):  Andrew Boie
#
# Copyright 2005(C), The University of Kansas
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import gs
import string
import copy
from group_lib import *
from group_api import *

from lib.doubledict import NSDict

# these 4 classes represent items that are INSTALLED in the kernel
class GroupSchedulingItem:
    """Base class for entities installed in the kernel"""
    def __init__(self, name, comment):
        self.comment = comment
        self.name = name
        pass

    def get_comment(self):
        """return a comment string for this item"""
        return self.comment

    def get_name(self):
        """return the name of this item"""
        return self.name

    def __repr__(self):
        return "{"+`self.get_name()`+":"+`self.get_comment()`+"}"

    pass

class GroupSchedulingMember(GroupSchedulingItem):
    def __init__(self, name, comment):
        GroupSchedulingItem.__init__(self, name, comment)
        self.references = []
        self.params = {}
        pass

    def __destroy(self):
        raise Exception, "Abstract method."

    def get_id(self):
        raise Exception, "Abstract method."

    def get_composite_id(self):
        raise Exception, "Abstract method."
    
    pass

class GroupSchedulingComputation(GroupSchedulingMember):

    def __init__(self, name, comment, joiner_type, cid):
        GroupSchedulingMember.__init__(self, name, comment)
        self.joiner_type = joiner_type
        self.cid = cid
        pass

    def set_param(self, paramname, value):
        j, i = self.get_composite_id()
        set_computation_parameters(j, i, paramname, value)
        pass

    def get_param(self, paramname):
        j,i = self.get_composite_id()
        return get_computation_parameters(j, i, paramname)

    def get_id(self):
        return self.cid

    def get_composite_id(self):
        return (self.cid, self.joiner_type)

    def __repr__(self):
        return "(id="+`self.cid`+",type="+`self.joiner_type`+")"
    
    # use the delete_group() method in GroupScheduling, not this!!!!
    def __destroy(self):
        for group in self.references:
            del group[self.get_name()]
            pass
        pass
    pass

class GroupSchedulingSDF(GroupSchedulingItem):
    def __init__(self, name, comment, algorithm, member_spec, group_spec):
        GroupSchedulingItem.__init__(self, name, comment)
        self.algorithm = algorithm
        self.mspec = member_spec
        self.gspec = group_spec
        pass
    
    def get_algorithm(self):
        """return the path to the algorithm file"""
        return self.algorithm

    def get_group_spec(self):
        """return a copy of the group_level parameter specs"""
        return copy.copy(self.gspec)
    
    def get_member_spec(self):
        """return a copy of the member-level parameter specs"""
        return copy.copy(self.mspec)
    pass

# DO NOT instantiate this yourself! use the GroupScheduling.create_group() method!
class GroupSchedulingGroup(GroupSchedulingMember):
    def __init__(self, name, comment, sdf, params):
        GroupSchedulingMember.__init__(self, name, comment)

        # a GroupSchedulingSDF object
        self.sdf = sdf
                
        # uses a doubledict, so we can reference by name or id
        # each member stored as a tuple: (member, member_id)
        self.members = NSDict()

        # install the group into GS
        self.gid = create_group(self.name, self.sdf.get_name())
        
        if params:
            self.set_parameters(params)
            pass
        
        pass

    # accessors

    def __repr__(self):
        return "Group("+`self.get_name()`+","+`self.get_id()`+"):"+`self.members.keys()`
    
    def get_sdf(self):
        """return the GroupSchedulingSDF for this group"""
        return self.sdf

    def get_member_parameters(self, key):
        """returns a copy of a member's parameter dict"""
        return get_member_parameters(self.get_id(), self.members[key][1],
                                     self.get_sdf().get_member_spec())
    
                                     
    def get_parameters(self):
        """get a copy of the group-level parameters for this group"""
        return get_group_parameters(self.get_id(),
                                    self.get_sdf().get_group_spec())
    
    def get_id(self):
        return self.gid
    
    def get_composite_id(self):
        return (self.get_id(), "group")
    
    
    # mutators
    def set_parameters(self, paramdict):
        """verify and install group-level parameters"""
        
        set_group_parameters(self.get_id(),
                             paramdict,
                             self.get_sdf().get_group_spec())
        pass
    
    
    def set_member_parameters(self, member, paramdict):
        """verifies and installs member-level parameters"""
        if member not in self.members:
            error_local("Member "+`members`+ " not in this group.")
            pass
        
        set_member_parameters(self.get_id(),
                              self.members[member][1],
                              paramdict,
                              self.get_sdf().get_member_spec())
        
        pass

    # use the delete_group() method in GroupScheduling, not this!!!!
    def __destroy(self):
        if self.keys():
            error_local("Cannot delete group; it has members inside it.")
            return

        destroy_group(self.get_id())
        
        # have all groups that reference this group, delete
        # this group from their members list.
        reflist = [i for i in self.references]
        for group in reflist:
            del group[self.get_name()]
            pass
        
        return
    
    # list-like methods

    def append(self, item, params=None):
        """add a GroupSchedulingMember to the member list.
        returns an integer member ID"""

        if not issubclass(item.__class__, GroupSchedulingMember):
            local_error("Append: Item must be a GroupSchedulingMember")
            return

        iname = item.get_name()        
        jid, jtype = item.get_composite_id()

        # convert string type to integer. comp_types defined in group_lib.py
        jtype_int = comp_types[jtype]
        
        # add it to this group
        mid = join_group(self.get_id(), iname, jtype_int, jid)
        
        # initially place the member in our member list with no
        # parameters, and then set them
        self.members[(iname, mid)] = (item, mid)

        if params:
            self.set_member_parameters(mid, params)
            pass
        
        # let the item know that we have a reference to it, in case
        # we want to destroy it later
        item.references.append(self)
        return mid

    def keys(self):
        return self.members.keys()

    def __getitem__(self, key):
        """retrieve a group (member, mid), either by member id or name"""
        return self.members[key]

    def __delitem__(self, key):
        """remove an item from this group. keyed by name or member id."""
        member, mid = self.members[key]
        leave_group(self.id, mid)
        del self.members[key]
        member.references.remove(self)
        pass

    def __iter__(self):
        """iterate over all the current group members"""
        return self.members.__iter__()     
    pass




