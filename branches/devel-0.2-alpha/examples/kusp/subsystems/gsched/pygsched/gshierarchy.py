"""
:mod:`gshiearchy` -- Gsched Hierarchy Object Classes 
==========================================================
    :synopsis: Group and Task data structures that are the basis for
        Group Scheduling Hierarchy configurations. 

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>


Contents:

.. toctree::
    :maxdepth: 1
    
    gshierarchy_gsmember
    gshierarchy_gsthread
    gshierarchy_gsgroup
    gshierarchy_gshierarchy
  
"""

# Not included in autodocs just for reference
"""


**Current Version: 3.0** 

Changes
---------------

*Version* *(YYYY-MM-DD)* : *Changes*
    
* 1.0 : First completed version -- heavily coupled with (old)GroupViewer  

* 2.0 : Complete rewrite.

* 2.1 : Adapting to fit PEP-008 Python coding and naming guidelines.
          This first iteration is to rename methods/functions to fit the
          def i_am_a_function() as opposed to the old ones which
          used cammel case (ie. def iAmAFuction()).

* 2.2 : Adapting to fit with PEP-287 reStructured Text Docstring format.

* 3.0 (2009-11-25) : Another rewirte, although this time there will be a heavy
          reuse of most of the code. The major thing to note is that this
          module will now be named gshierarchy instead of gsstructures.
          This also focuses on cleaning up the configuration dictionary 
          transformation code to parse the hierarchy in the GSHierarchy class.

"""

import sys
import types
from pykusp.devutils.enforcetypes import enforcetypes
import pykusp.configutility as config_parser
from gsparsingtags import *

class MemberAttributes:
    """
    * EXCLUSIVE: Whether or not to allow CFS to schedule a thread
      controlled by group scheduling. If exclusive is set, the thread
      will only be runnable by Group Scheduling.
    """
    EXCLUSIVE = 'exclusive'
    
class GSMember:
    """

    Encapsulates all the pertinent Group Scheduling member data common
    to groups and threads. The data included within the Member class
    is a name, docstring, and the members parent, as well as the
    appropriate get/set methods for each of the GSMember datum.

    :param name: The unique name of the member.
    :type name: String
    :param parent: Reference to the parent object that
        contains the GSMember.
    :type parent: GSMember
    :param doc: A comment to summarize the purpose of the Member.
    :type doc: String        
    :param member_data: General purpose data dictionary to give 
        arbitrary extra data to the member, if needed.
    :type member_data: dict
    :param attributes: Attributes for the member as defined in 
        :mod:`gshierarchy.MemberAttributes`. The list is converted 
        to a set for use internally.
    :type attributes: List of strings
    """ 
    def __init__(self, name, parent=None, doc='', member_data={}, attributes=[]):
        self._member_data = member_data
        self._attributes = set(attributes)
        self._name = name
        self._parent = parent
        self._docstring = doc
    
    # Standard get/set routines that are my (Dillon's)
    # preference for interacting with Class
    # Attributes. 
    #
    def get_name(self):
        """
        :returns: The name of the member.
        """
        return self._name
    
    @enforcetypes(str)
    def set_name(self, name): 
        """
        Sets the name of the member to `name`.
        :param name: The new name of the member.
        :type name: String
        """
        self._name = name
    
    def get_docstring(self): 
        """
        :returns: The docstring of the member.
        """
        return self._docstring

    @enforcetypes(str)
    def set_docstring(self, doc): 
        """
        Sets the docstring of the member to `doc`.
        :param doc: The new docstring for the member.
        :type doc: String
        """
        self._docstring = doc

    def get_parent(self): return self._parent
    
    def set_parent(self, parent): 
        """
        :type parent: GSMember
        """
        self._parent = parent
    
    def get_member_data(self):
        """
        :returns: Returns all per member data.
        :rtype: list of `GSData` objects
        """
        return self._member_data
    
    def update_member_data(self, data):
        """
        :param data: A list of GSData that defines the 
            dataset for this member.
        """
        self._member_data.update(data)
        

    def add_attribute(self, attr):
        """
        Adds an attribute to the attribute set.
        """
        self._attributes.add(attr)
        
    
    def remove_attribute(self, attr):
        """
        Removes an attribute for the attribute set.
        """
        self._attributes -= set([attr])
        
    def update_attributes(self, attrs):
        """
        Updates the members attribute set with a list of new
        attributes.
        """
        self._attributes.update(attrs)
        
    def get_attributes(self):
        """
        :returns: The list of attributes for the member.
        """
        return list(self._attributes)
    
    def has_attribute(self, attr):
        """
        Test to see if the member has the attribute.
        
        :param attr: The attribute for which to test.
        :type attr: String
        :returns: True if *attr* is in the set of attributes.

        .. seealso:: :mod:`gshierachy.MemberAttributes`
        """
        return self._attributes.issuperset(set([attr]))


    def adapt(self):
        """
        Converts the instance into a dictionary, keyed by the
        attribute name::
         
            print member.adapt()
            { 'name' : <member-name>,
              'parent' : <parent-reference>,
              'doc' : <docstring>,
              'member_data' : <member-data-dict>,
              'attributes' : <attributes-list>
            }

        """
        return  { 'name' : self.get_name(), 
                   'parent' : self.get_parent(),
                   'doc' : self.get_docstring(),
                   'member_data' : self.get_member_data(),
                   'attributes' : self.get_attributes()
                   }
        
    def __str__(self):
        return  self.get_name()
        

class GSThread(GSMember):
    """
    The GSThread is the class that represents the physical task struct
    for a task that is a member of some group within Group
    Scheduling. Akin to the Group Scheduling internal funcationality,
    GSThreads may only be members of GSGroups and may not have any
    members of their own.  Since they are allowed not members
    themselves, GSThreads will always be leaf nodes in any graphic
    visualization of a Group Scheduling Hierarchy.
    """
    def __init__(self, name, parent=None, pid=0, member_data={}, 
                 attributes=[], doc=''):
        GSMember.__init__(self, name, parent, doc,
                          member_data, attributes)
        
        self._pid = pid
    
    @enforcetypes(int)
    def set_pid(self, pid):
        self._pid = pid
        
    def get_pid(self):
        return self._pid
    
    def adapt(self):
        """
        Converts the instance into a dictionary, keyed by the
        attribute name::
         
            print thread.adapt()
            { 'name' : <thread-name>,
              'parent' : <parent-reference>,
              'pid'    : <pid-or-0>,
              'doc' : <docstring>,
              'member_data' : <member-data-dict>,
              'attributes' : <attributes-list>
            }

        """
        return  { 'name' : self.get_name(), 
                   'parent' : self.get_parent(),
                   'doc' : self.get_docstring(),
                   'pid' : self.get_pid(),
                   'member_data' : self.get_member_data(),
                   'attributes' : self.get_attributes()
                   }

    def to_pretty_string(self, indent=0):
        pstring = indent * ' '
        pstring += '(T) - %s ' % self.get_name()  
        if self.get_pid() > 0:
            pstring += '<%s>' % self.get_pid()
        pstring += '\n'
        return pstring

class GSGroup(GSMember):
    """
    Data structure to encapsulate data within a  
    Group Scheduling Hierarchy Group.
    
    :param name: The user given name of the Group.
    :type name: string
    :param sdf: The name of the Scheduling 
            Decision Function that the group uses.
    :type sdf: string
    :param parent: The GSGroup parent of this GSGroup.
    :type parent: GSGroup Reference
    :param doc: The documentation string describing the GSGroup's
        particular purpose.
    :type doc: String

    """

    options = { 'managed':0x01 }

    def __init__(self, group_name='new_group', 
                 member_name='new_group_mem',  
                 sdf='sdf_seq', parent=None, 
                 per_group_data={}, attributes=[], doc=''):          
        GSMember.__init__(self, member_name, parent, per_group_data, attributes,  doc )

        self._sdf = sdf.strip()
        self._group_members = []
        self._group_name = group_name
        self._attributes = set(attributes)
    
    def get_name(self):
        return self._group_name

    def set_name(self, name):
        self._group_name = str(name)

    @enforcetypes(GSMember)
    def add_member(self, member):
        """
        Adds a member of either type GSGroup or GSThread to the 
        group.
        """
        member.set_parent(self)
        self._group_members.append(member)
    
    @enforcetypes(GSMember)
    def remove_member(self, member):
        """
        Removes a member from the group and return it if it exsists.
        Otherwise return None.
        """
        if member in self._group_members:
            member.set_parent(None)
            return self._group_members.pop(member)
        return None

    def get_members(self, recursive_search=False):
        """Returns the members of the group. The members are 
        expected to be GSGroups and GSThreads.
        """
        if recursive_search:
            all_members = []
            all_members.extend(self._group_members)
            for member in filter(lambda m: isinstance(m, GSGroup),
                                 self._group_members):
                all_members.extend(member.get_members(recursive_search))
            return all_members
        return self._group_members


    def set_sdf(self, sdf):
        self._sdf = str(sdf)


    def get_sdf(self):
        """
        Returns the group sdf.
        
        :return: The string name of the sdf.
        """
        return self._sdf

    def set_member_name(self, name):
        GSMember.set_name(self, name)

    def get_member_name(self):
        return GSMember.get_name(self)

    @enforcetypes(int)
    def to_pretty_string(self, indent=0):
        pstring = ' ' * indent 
        pstring += '(G) - %s | %s | %s\n' % (self.get_name(), self.get_sdf(), self.get_member_name())
        for mem in self.get_members():
            pstring += mem.to_pretty_string(indent+4)
        return pstring
                
    def __str__(self):
        return self.get_name()+' ('+self.get_sdf()+')'
        
    def adapt(self):
        """
        Converts the instance into a dictionary, keyed by the
        attribute name::
         
            print thread.adapt()
            { 'name' : <group-name>,
              'sdf'    : <sdf-name>,  
              'parent' : <parent-reference>,
              'member_name' : <member-name>,
              'doc' : <docstring>,
              'per_group_data' : <per-group-data-dict>,
              'attributes' : <attributes-list>
            }

        """
        return  { 'name' : self.get_name(), 
                  'sdf' : self.get_sdf(),
                  'member_name' : self.get_member_name(),
                   'parent' : self.get_parent(),
                   'doc' : self.get_docstring(),
                   'per_group_data' : self.get_member_data(),
                   'attributes' : self.get_attributes()
                   }

    def get_attributes(self):
        """
        :returns: The list of attributes for the member.
        """
        return list(self._attributes)

    def has_attribute(self, attr):
        """
        Test to see if the member has the attribute.
        
        :param attr: The attribute for which to test.
        :type attr: String
        :returns: True if *attr* is in the set of attributes.

        .. seealso:: :mod:`gshierachy.MemberAttributes`
        """
        return self._attributes.issuperset(set([attr]))

class GSHierarchy:
    """
    The GSHierarchy class wraps a root GSGroup to provide hierarchy
    wide data and functions. 
    """
    def __init__(self, config):
        self._root_group = None
        self._attachment_point = None
        self._unattached_members = []
        
        if type(config) is str:
            config = config_parser.parse_configfile(config)

        if type(config) is dict:
           self.build_from_dict(config)

        elif isinstance(config, GSGroup):
            self._root_group = config
    
    @enforcetypes(GSMember)
    def add_unattached_member(self, member):
        """
        Add a GSGroup or GSThread to the Hierarchy's unattached
        members list. When a string representation of the Hierarchy is
        generated, each unattached member is printed under the
        "Unattached Members" heading. 
        """
        self._unattached_members.append(member)

    @enforcetypes(GSMember)
    def remove_unattached_member(self, member):
        """
        Removes a member from the unattached members list, and returns
        that member. If the member is not in the list, then it returns
        None.
        """
        if member in self._unattached_members:
            return self._unattached_members.pop(member)
        return None

    def get_unattached_members(self):
        """
        :returns: The list of unattached members.
        """
        return self._unattached_members

    def get_attachment_point(self):
        """
        :return: The attachment point (executable image name) of the
            hierarchy.
        """
        return self._attachment_point

    def set_attachment_point(self, attachment_point):
        self._attacment_point = attachment_point

    @enforcetypes(GSGroup)
    def set_root_group(self, root_group):
        self._root_group = root_group
    
    def get_root_group(self):
        return self._root_group

    
    def get_members(self):
        """
        :returns: List of member generated from the recursive search
            of the root group.
        """
        if self._root_group is None:
            return []
        return self._root_group.get_members(recursive_search=True)


    def __str__(self):
        """
        Prints the :class:`GSHierarchy` by traversing the 
        tree recursively, starting at the root, and calling 
        each members `pprint()`
        """
        root_group = self.get_root_group()
        root_info = str(root_group)
        rstring =  ' GSCHED HIERARCHY : Root=%s\n' % root_info
        rstring += '--------------------------'
        rstring += '-' * len(root_info) + '\n'
        if not root_group is None:
            rstring += root_group.to_pretty_string()
        else:
            rstring +=  '<None>\n'
        
            
        rstring += '\n'
        rstring += ' UNATTACHED MEMBERS\n'
        rstring += '--------------------\n'
        if len(self.get_unattached_members()) > 0:
            for group in self.get_unattached_members():
                rstring += group.to_pretty_string()
        else:
            rstring+=  '<None>\n'

        return rstring

    
    @enforcetypes(dict)
    def build_from_dict(self, config_data_dict):
        #################################
        # TOP LEVEL PASS THROUGH
        #################################
        
        # <gsh-installation>
        install_dict = config_data_dict[GSH_INSTALLATION_TAG]
        # <groups>
        groups_dict = config_data_dict[GROUPS_TAG]
        # <threads>
        threads_dict = config_data_dict[THREADS_TAG]
        # <thread-specification>
        thread_spec_dict = config_data_dict[THREAD_SPEC_TAG]
         
        ################################
        # Hierarchy Installation Info
        ################################
        root_name = install_dict[LOCAL_ROOT_TAG]
        attach_point = install_dict[ATTACHMENT_POINT_TAG]
        self.set_attachment_point(attach_point)

        #################################
        # Building Thread Specifications
        #################################
        thread_specs = {}
        for spec_name, spec_data in thread_spec_dict.items():
            attributes = spec_data[THREAD_SPEC_ATTRIBUTES_TAG]
            member_data = spec_data[THREAD_SPEC_PMD_TAG]
            docstring = spec_data[THREAD_SPEC_COMMENT_TAG]
            thread = GSMember(name=spec_name, parent=None, member_data=member_data, 
                              attributes=attributes, doc=docstring)
            thread_specs[spec_name] = thread

        ################################
        # Create threads
        ################################
        threads = {}
        for name, spec in threads_dict.items():
            # Get the thread specification corresponding
            # to the thread.
            thread_spec = thread_specs[spec]
            # Change the thread to have the desired name.
            # (Otherwise it would match the name of the
            # thread-spec).
            spec_dict  = thread_spec.adapt()
            spec_dict['name']= name
            threads[name] = GSThread(**spec_dict)
        #################################
        # Create Groups
        #################################
        groups = {}
        for group_name, group_data in groups_dict.items():
            sdf = group_data[GROUP_SDF_TAG]
            attributes = group_data[GROUP_ATTRIBUTES_TAG]
            per_group_data = group_data[GROUP_PGD_TAG]
            members = group_data[GROUP_MEMBERS_TAG]
            member_name = group_data[GROUP_MEMBER_NAME_TAG]
            docstring = group_data[GROUP_COMMENT_TAG]
            group = GSGroup(group_name, member_name, sdf, 
                            None, per_group_data, attributes,
                            docstring)
            groups[group_name] = { 'object' : group,
                                   'members' : members}
        
        def build_groups_R(group, group_members, build_threads, build_groups):
            for mem_name in group_members:
                member = None
                if mem_name in build_threads.keys():
                    
                    member = build_threads[mem_name]
                elif mem_name in build_groups.keys():
                    
                    mem_group = build_groups[mem_name]['object']
                    mem_group_members = build_groups[mem_name]['members']
                    build_groups_R(mem_group, mem_group_members, build_threads, build_groups)
                    member = mem_group
                else:
                    raise KeyError("Unable to find unknown member `%s'. The configuration data"
                                   " for the GSHierarchy is invalid, parsing failed." % mem_name)
                group.add_member(member)
        
        # Build Group Memberships
        root_group = None
        gsh_members = []
        if root_name in groups.keys():
            root_group = groups[root_name]['object']
            root_group_mems = groups[root_name]['members']
            build_groups_R(root_group, root_group_mems, threads, groups)
            self.set_root_group(root_group)
            gsh_members = root_group.get_members(recursive_search=True)
            
        
        ################################
        # Cleanup and Validation
        ################################
        # Find unattached groups
        u_groups = {}
        for u_group in filter(lambda g: not g['object'] in gsh_members and\
                                  not g['object'] is self.get_root_group(), 
                              groups.values()):
            group_name = u_group['object'].get_name()
            u_groups[group_name] = u_group
        
        # Find unattached thread
        u_threads = {}
        for u_thread in filter(lambda t: t not in gsh_members, 
                                threads.values()):
            u_threads[u_thread.get_name()] = u_thread
        
        
                
        # Try to attach unattached members.  If there is a problem,
        # this should help figure out where the link is broken.
        for grp in u_groups.values():
            group = grp['object']
            group_mems = grp['members']
            if group.get_parent() == None:
                build_groups_R(group, group_mems, u_threads, u_groups)
        
        u_groups = map(lambda g: g['object'], u_groups.values()) 
        # This should only add the partially reconstructed 
        # groups and lost threads to the unattached members.
        for u_mem in filter(lambda m: m.get_parent() is None, 
                              (u_groups+u_threads.values())):
            self.add_unattched_member(u_mem)
    
    
        
    
