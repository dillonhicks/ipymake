"""
:mod:`gsstructures` -- Gsched Hierarchy Objects 
==========================================================
    :synopsis: Group and Task data structures that are the basis for
        Group Scheduling Hierarchy configurations. 

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>


Contents:

.. toctree::
    :maxdepth: 1
    
    gsstructures_gsdata
    gsstructures_gsmember
    gsstructures_gsthread
    gsstructures_gsgroup
    gsstructures_gshierarchy
    gsstructures_consts
    
    
"""

#not included in autodocs
"""


**Current Version: 2.2** 

Changes
---------------

*Version* : *Changes*
    
* 1.0 : First completed version -- heavily coupled with (old)GroupViewer  

* 2.0 : Complete rewrite.

* 2.1 : Adapting to fit PEP-008 Python coding and naming guidelines.
          This first iteration is to rename methods/functions to fit the
          def i_am_a_function() as opposed to the old ones which
          used cammel case (ie. def iAmAFuction()).

* 2.2 : Adapting to fit with PEP-287 reStructured Text Docstring format. (inprogress)

"""

import sys
import types
import pprint

# Allow access to the GSH parsing tag library, used 
# for decomposing the config dictionary.
#
from gsparsingtags import *

class DEBUG_LEVEL:
    NONE    = 0
    LOW     = 1
    NORMAL  = 2
    HIGH    = 3

# Checking if debug_level has been defined.
# If not, creates it and sets it to 0 so that
# all of the debug references in gsstructures.py
# will not fail.
#
try:
    global Params
    Params.debug_level
except NameError:
    class FallbackParams:
        debug_level = 0
    
    Params = FallbackParams()
finally:
    debug_level = Params.debug_level


"""
.. todo:: This should be variable to the width of the 
    terminal buffer. 80 is standard, but everyone always
    is doing some kind of resizing. 
"""
TERMINAL_WIDTH = 80    
    
    
def pdebug(msg, level=DEBUG_LEVEL.NORMAL):
    """
    Prints the debug message if the debug level is 
    high enough.
    
    :param msg: The message to print.
    :type msg: string
    :param level: The Debug Level at which to print the message.
    :type level: integer
    """
    if debug_level >= level:
        print msg

def pprint_debug(msg, level=DEBUG_LEVEL.NORMAL):
    """
    Pretty Prints the debug message packet if the debug level is 
    high enough.
    
    :param msg: The message to print.
    :type msg: A pretty printable object
    :param level: The Debug Level at which to pretty print the message.
    :type level: integer
    """
    if debug_level >= level:
        pprint.pprint(msg)
    
class DATA_ATTRIBUTES:
    """
    
    Data Attributes for Group Scheduling Per Member/Group Data.
    
    .. note:: We need to talk about these in more details
        I remember them being relevant but we had not hashed out
        a good use or set of them.
        
    * NONE: For describing GS internal member data
        that the user cannot modify, but is 
        displayed for completeness.
    
    * DYNAMIC: Changes value during runtime within
        Group Scheduling.
    
    * STATIC: Doesn't change values during runtime.
    
    * REQUIRED: An input value is required for this data for 
        proper functionality. 
    
    * HAS_DEFAULT: There is a default value associated with the 
        MemberData that may/will be used.
        
    * EXCLUSIVE: ????
    
    """
    # Group Scheduling Member Attributes Flags
    #
    NONE        = 0x0001
    DYNAMIC     = 0x0002
    STATIC      = 0x0004
    REQUIRED    = 0x0008
    HAS_DEFAULT = 0x000e
    EXCLUSIVE   = 0x0010
    ALL         = [ NONE, DYNAMIC, STATIC, 
                   REQUIRED, HAS_DEFAULT, EXCLUSIVE ]    
    
class C_TYPES:
    """ 
    Provides a way to have some equivalence between C data
    types and Python data types. This C_TYPES class includes
    evaluation of values against their desired type and gives
    default values for the C types to help typing within the 
    configuration files and Group Scheduling API.
    """
    
    # The Python->C type equivalents.
    #
    INT     = 'Integer'
    U_INT   = 'Unsigned Integer'
    LONG    = 'Long'
    U_LONG  = 'Unsigned Long'
    BOOL    = 'Boolean'
    STRING  = 'String'
    HANDLE  = "void*"
    ALL     = [ INT, U_INT, LONG, U_LONG, BOOL,
                STRING, HANDLE ]
    
    # Slightly arbitrary default values for the
    # given cTypes, so that the configuration files
    # will not have to parse empty strings and 
    # worry about inconsistent types.
    #
    INT_DEFAULT     = 0
    U_INT_DEFAULT   = 0
    LONG_DEFAULT    = 0
    U_LONG_DEFAULT  = 0
    BOOL            = False
    STRING          = ''
    HANDLE          = 'void*'
    
    @staticmethod
    def get_default(cType):
        """
        :return: The default value of the cType,
            if it exists. Otherwise return None.
        """
        if cType is C_TYPES.INT:
            return C_TYPES.INT_DEFAULT
        if cType is C_TYPES.U_INT:
            return C_TYPES.U_INT_DEFAULT
        if cType is C_TYPES.LONG: 
            return C_TYPES.LONG_DEFAULT
        if cType is C_TYPES.U_LONG:
            return C_TYPES.U_LONG_DEFAULT
        if cType is C_TYPES.BOOL:
            return C_TYPES.BOOL_DEFAULT
        if cType is C_TYPES.STRING:
            return C_TYPES.STRING_DEFAULT
        if cType is C_TYPES.HANDLE:
            return C_TYPES.HANDLE_DEFAULT

        return None
    
    @staticmethod
    def eval(value, cType):
        """
        Evaluates the value against the expected value range
        for the cType.
        
        :return: True if the value is an expected range, false
            if outside of the expected range (or not of 
            of matching value & type), and None if cType
            is not a type within C_TYPES.
        """
        if cType is C_TYPES.INT:
            if type(value) is int:
                return True
            return False

        if cType is C_TYPES.U_INT:
            if type(value) is int:
                if value >= 0:
                    return True
            return False
        
        if cType is C_TYPES.LONG:
            if type(value) is long:
                return True
            
        if cType is C_TYPES.U_LONG:
            if type(value) is long:
                if value >= 0:
                    return True
            return False
                    
        if cType is C_TYPES.BOOL:
            if type(value) is bool:
                return True
            return False
        
        if cType is C_TYPES.STRING:
            if type(value) is str:
                return True
            
        if cType is C_TYPES.HANDLE:
            return True
        
        return None

class GSData :
    """
    :class:`GSData`
    
    Holds all of the data relevant to a piece of data within
    an SDF. This could be a per member data element or a per
    group data element. All of this information is used for 
    creating a group scheduling configuration file, even if it is
    not being used to within actual Group Scheduling. This is to 
    help assist the user of the other Group Scheduling Python tools
    by providing more useful information than what would actually
    be needed. The best example of this is the docString attribute
    of the GSData class.
    
    :param name: The desired unique name used to identify the
        GSData.
    :param value: The value to give the GSData. This is not
        always used/needed. `See: DATA_ATTRIBUTES`
    :param cType: The type that would be given to 'value' if 
        programming in C. This is used for value evaluation 
        for the value. `See: C_TYPES`
    :param docString: The summary of the GSData giving why
        and how the data is used as per member/group data
        within a particular SDF. `See: GSSdf`
    :param index: The index to place the data within the C 
        vector of the member structure within Group Scheduling.
        `See: Group Scheduling API documentation.`
    :param attributes: A list of special attributes for the 
        GSData that tell how it is to be used, initialized, and
        nature. `See: DATA_ATTRIBUTES`    
    """
    def __init__(self, name, value, cType, 
                 docString='', index=0, attribs=[]):
        self.name = name
        self.value = None
        self.cType = None        
    
        if C_TYPES.eval(value, cType):
            self.value = value
            self.cType = cType
        elif cType in C_TYPES.ALL:
            self.value = C_TYPES.get_default(cType)            
                
        self.docString = docString
        self.attributes = []
    
        for attrib in attribs:
            addAttribute(attrib)
        
        self.index = index
        
    def add_attribtue(self, attrib):
        """
        Add a specific attribute to the `GSData`.
        """
        if attrib in DATA_ATTRIBUTES.ALL:
            self.attributes.append(attrib)
        else:
            pdebug('Attribute %s is not a proper data attribute!'\
                   ' Not adding to the GSData.' % attrib.__name__)

    def adapt(self):
        
        return { self.name : {
                   DATA_VALUE_TAG        : self.value,
                   DATA_TYPE_TAG         : self.cType,
                   DATA_INDEX_TAG        : self.index,
                   DATA_DOCSTRING_TAG    : self.docString,
                   DATA_ATTRIBUTES_TAG   : self.attributes
                   }
                }
        
        
class GSSdf:
    """
    Group Scheduling Scheduling Decision Function
    
    :param name: The function name of the SDF i.e. sdf_rr
    :type name: string
    :param longName: The human readable name of the
            SDF i.e. Round Robin
    :type longName: string
    :param docString: The summary of the SDF and its use.
    :type docString: string
    """
    def __init__(self, name, longName, docString=""):
        self.name = name
        self.longName = longName
        self.docString = docString
        self.PMD = {}
        self.PGD = {}
        
    def add_PMD(self, name, value, 
               cType, docString='',
               index=None, attribs=[]):
        """Adds a Per Member Data element to the SDF. Checks to
        make sure that there is not a name collision with the to be
        inserted element."""
        if index is None:
            index = len(self.PMD.values())
        newPMD = GSData(name, value, cType, docString, index, attribs)
        if self.PMD.has_key(name):
            return False
        self.PMD[name] = newPMD
        return True
        
    def add_PGD(self, name, value, 
               cType, docString='',
               index=None, attribs=[]):
        """Adds a Per Group Data element to the SDF. Checks to
        make sure that there is not a name collision with the to be
        inserted element."""        
        if index is None:
            index = len(self.PGD.values())
        newPGD = GSData(name, value, cType, docString, index, attribs)
        if self.PGD.has_key(name):
            return False
        self.PGD[name] = newPGDs
        return True


    def adapt(self):
        parsedPMD = {}
        for key in self.PMD.keys():
            parsedPMD[key] = self.PMD[key].adapt()
        
        parsedPGD = {}
        for key in self.PGD.keys():
            parsedPGD[key] = self.PMD[key].adapt()            
        
        return { self.name:  {
                              SDF_NAME_TAG : self.longName,
                              SDF_PMD_TAG : parsedPMD,
                              SDF_PGD_TAG : parsedPGD,
                              }
                }

class MemberAttributes:
    """
    
    """
    EXCLUSIVE = 'exclusive'
    
class GSMember():
    """
    Encapsulates all the pertinent 
    Group Scheduling member data common to groups and threads.

    :param name: The user defined name of the member. This name does 
        not have to be unique, and is for labeling purposes only. 
    :type name: String
    :param doc: A comment to summarize the purpose of the Member.
    :type doc: String        
    :type id: Integer
    :param parent: Reference to the parent object that
        contains the GSMember.
    :type parent: GSMember
    """ 
    def __init__(self, name, parent=None, doc=''):
        """
        .. method:: GSMember.__init__(name, parent=None, doc='')
        """
        self._memberData = {}
        self._attributes = set([])
        self.name = name
        self.parent = parent
        self.docString = doc
        self._id = None
    
    # Standard get/set routines that are my (Dillon)
    # preference for interacting with Class
    # Attributes. 
    #
    def get_name(self):
        """
        :returns: The name of the member.
        """
        return self.name
    def set_name(self, name): 
        """
        Sets the name of the member to `name`.
        """
        self.name = name
    def get_docstring(self): 
        """
        :returns: The docstring of the member.
        """
        return self.docString
    def set_docstring(self, doc): 
        """
        Sets the docstring of the member to `doc`.
        """
        self.docString = doc
    def get_ID(self): 
        """
        .. note:: 
            
            Not used
        
        :returns: the id of the member.
        """
        return self._id
    def set_ID(self, id):
        """
        .. note:: 
            Not used
        
        Sets the members's id to `id`.
        """
        self._id = id
    def get_parent(self): return self.parent
    def set_parent(self, parent): self.parent = parent
    
    def get_PMD(self):
        """
        :returns: Returns all per member data.
        :rtype: list of `GSData` objects
        """
        return self._memberData
    
    def update_PMD(self, data):
        """
        :param data: A list of GSData that defines the 
            dataset for this member.
        """
        self._memberData.update(data)
        
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
        Updates the members attributes with a list of new attributes.
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
        """
        return self._attributes.issuperset(set([attr]))


    def adapt(self):
        """
        Converts the member's data into a dictionary for parsing 
        to a configfile.
        """
        return { self.name : {
                    
                    THREAD_SPECIFICATION_PMD_TAG          : self._memberData,
                    THREAD_SPECIFICATION_ATTRIBUTES_TAG   : list(self._attributes), 
                    THREAD_SPECIFICATION_COMMENT_TAG      : self.docString } }
        
    def __str__(self):
        return  self.get_name()
    
    def fields(self):
        """
        Returns the members data as a tuple of fields.
        """
        return ( self.name, )

class GSThread(GSMember):
    """
    Group Scheduling Thread (or Task)
    """
    @staticmethod
    def wrap_member(mbr):
        """
        Wraps the GSMember to make it a GSThread.
        
        :param mbr: The member to wrap into a a GSThread. 
        :return: GSThread
        """
        # Check to see if the mbr is actually a GSMember
        # class. wrapMember is not designed and should
        # not handle other object types.
        #
        if not mbr.__class__ is GSMember:
            raise TypeError('GSThread Error(1): Cannot wrap member;'
                            ' mbr is not a GSMember', mbr)
        
        # Acquires the name, parent, and 
        # doc needed to copy the member and make it
        # a thread.
        #
        name = mbr.get_name()
        parent = mbr.get_parent()
        doc = mbr.get_docstring()
        return GSThread(name, parent, doc)
    
    def __init__(self,name, parent=None, doc='', pid=0):
        GSMember.__init__(self, name, parent, doc )
        
        self.pid = pid

    def set_pid(self, pid):
        self.pid = pid
        
    def get_pid(self):
        return self.pid

    def pprint(self, indentLevel=0):
        pName = ' ' * indentLevel 
        pName += '(T) - %s' % self.name
        print pName
    
    def fields(self):
        return ( self.get_name(), self.get_parent(), self.get_docstring())


    
class ROOT_FLAGS:
    """
    GSGroup Root Attribute Flags
    
    * NOT_ROOT: The group is a member only.
    * SUPER_ROOT: The group is the root of a GSHierarchy.
    * ACTIVE_ROOT: The group the currently has exclusive control.
    * LOCAL_ROOT: Specifies a group that is not the SUPER_ROOT 
        that has the permissions to become an active 
        root during mode changes.
    """
    NOT_ROOT    =   0x0000
    SUPER_ROOT  =   0x0001
    ACTIVE_ROOT =   0x0002
    LOCAL_ROOT  =   0x0004

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
    
    def __init__(self, name='<New Group>', sdf='sdf_seq',
                 parent=None, doc=''):          
        GSMember.__init__(self, name, parent, doc )

        self.rootFlags = ROOT_FLAGS.NOT_ROOT
        # The strip is here to prevent there from
        # being extra \n characters in the sdf name
        # this was causing errors in graphing.
        # Graphviz Dot does not line \n characters
        # In node labels.
        self.sdf = sdf.strip()
        self.members = []
        self.struct_name = name
    
    def add_member(self, member):
        """
        Adds a member of either type GSGroup or GSThread to the 
        group.
        """
        if member.__class__ is GSGroup:
            self.add_group(member)
        elif member.__class__ is GSThread:
            self.add_thread(member)
        else:
            raise TypeError('GSGroup Error(1):Cannot add the member; '
                            'not a GSGroup or GSThread object', member)
        pass
    
    def add_group(self, group):
        """
        Adds the group to the GSGroup's members.
        """
        if isinstance(group, GSGroup):
            pdebug('Adding GSGroup %s to GSGroup %s'
                   % (group.get_name(), self.get_name()) )
            group.set_parent(self)
            self.members.append(group)
        else:
            raise TypeError('GSGroup Error(2): Cannot add the group; '
                            'group is not a GSGroup ', member)
        pass
    
    def remove_group(self, group):
        """
        Remove the group from the GSGroup's members.
        """
        if group in self.members:
            pdebug('Removing GSGroup %s from GSGroup %s'
                   % (group.get_name(), self.get_name()) )
            group.set_parent(None)
            return self.members.pop(group)
        else:
            pdebug('Nothing to remove, GSGroup %s not found in GSGroup %s.'
                   % (group.get_name(), self.get_name()) )
            
        return None
    
    def add_thread(self, thread):
        """
        Adds the thread to the GSGroup.
        """
        if isinstance(thread,GSThread):
            pdebug('Adding GSThread %s to GSThread %s'
                   % (thread.get_name(), self.get_name()) )
            thread.set_parent(self)
            self.members.append(thread)
        else:
            pdebug('%s is not a GSThread object'
                   % (thread.get_name(), self.get_name()) )
            raise TypeError('GSGroup Error(3): Cannot add Thread, '
                            'not a GSThread object', thread)

    
    def remove_thread(self, thread):
        """
        Removes the thread from the GSThread.
        """
        if thread in self.members:
            pdebug('Removing GSThread %s from GSThread %s'
                   % (thread.get_name(), self.get_name()) )
            thread.set_parent(None)
            return self.members.pop(thread)
        else:
            pdebug('GSThread %s not found in GSThread %s'
                   % (thread.get_name(), self.get_name()) )
        return None
    
    def get_members(self):
        """Returns the members of the group. The members are 
        expected to be GSGroups and GSThreads.
        """
        pdebug('Retrieving GSGroup %s\'s members with GSGroup.getMembers()'
               % self.get_name(),
               DEBUG_LEVEL.HIGH )
        return self.members
    
    def get_SDF(self):
        """
        Returns the group sdf.
        
        :return: The string name of the sdf.
        """
        pdebug('Retrieving GSGroup %s\'s SDF name with GSGroup.getSDF()'
               % self.get_name(),
               DEBUG_LEVEL.HIGH )
        return self.sdf

    def set_struct_name(self, name):
        self.struct_name = name

    def get_struct_name(self):
        return self.struct_name

    def pprint(self, indentLevel=0):
        pName = ' ' * indentLevel 
        pName += '(G) - %s' % self.name
        print pName
        for mem in self.members:
            mem.pprint(indentLevel+4)

    
    def fields(self):
        return (self.get_name(), self.get_SDF(), self.get_parent(), 
                 self.get_docstring)
            
    def __str__(self):
        return self.get_name()+' ('+self.get_SDF()+')'
        
class GSHierarchy:
    """
    A wrapper to a Root GSGroup that provides a few Hierarchy wide 
    functions. 
    
    :param config: The configuration dictionary defining a 
            Group Scheduling Hierarchy or a root `GSGroup`.
    :type config: GSGroup or dictionary 
    """
    def __init__(self, config):
        self._superRoot = None
        self._activeRoot = None
        self._members = []
        self._attachmentPoint = None
        self.superRootName = None
        self.empty_groups = []

        if isinstance(config, GSGroup):
            self._superRoot = config
            self._activeRoot = config
            self.superRootName = config.get_name()               
            return
        
        elif not type(config) is types.DictType: 
            raise ValueError('GSHierarchy Error(10): ' 
                        'Parsing failed, The config parameter is ' 
                        'not a dictionary.', type(config))
   
   
                
        def load_setup_data(data):
            """ Get and store information here
            set superroot to be the root.
            """
            
            # Printing the debug setup information:
            # Raw Configuration Data, super root name of the hierarchy,
            # and attachment point of the application.
            #
            if debug_level >= 2:
                print 'Loading GSH Setup Data'
                print '    Raw Data:'
                pprint.pprint(data)
                
            # Obtaining the super root name and the attachment
            # point name from the configuration dict.
            #
            self.superRootName = data[LOCAL_ROOT_TAG]
            self._attachmentPoint = data[ATTACHMENT_POINT_TAG]
            
            if debug_level >= 2:
                print 'Super Root Name: %s' % self.superRootName
                print 'Attachment Point Name: %s' % self._attachmentPoint
                
                     
        def load_SDF(data):
            """ Load and register? sdf information
            
            """
            
            if debug_level >= 2:
                print 'Loading SDF Specifications'
                print '    Raw Data:'
                pprint.pprint(data)

            
            for sdfKey in data.keys():
                #
                # Debug to add: Check keys?
                #
                
                sdf = data[sdfKey]
                cName = sdfKey
                name = sdf[SDF_NAME_TAG]
                perGroupData = sdf[SDF_PGD_TAG]
                perMemberData = sdf[SDF_PMD_TAG]

                
                #
                # Debug info
                #
                pdebug( ('='*80))
                pdebug( 'SDF %s Raw Data:' % sdfKey)
                pprint_debug(sdf)
                pdebug( '\nLoaded Information:')
                pdebug( 'Name: %s' % name)
                pdebug( 'SDF C-Name: %s' % cName)
                pdebug( 'Per Group Data: %s' % perGroupData)
                pdebug( 'Per Member Data: %s' % perMemberData)
                
                
                gsSDF = GSSdf(cName, name)
                for key in perMemberData.keys():
                    rawPMD = perMemberData[key]
                    name = key
                    value = rawPMD[DATA_VALUE_TAG]
                    cType = rawPMD[DATA_TYPE_TAG]
                    docString = rawPMD[DATA_DOCSTRING_TAG]
                    index = rawPMD[DATA_INDEX_TAG]
                    attribs = rawPMD[DATA_ATTRIBUTES_TAG]
                    gsSDF.add_PMD(name, value, cType, 
                                 docString, index, attribs)
                
                for key in perGroupData.keys():
                    rawPMD = perMemberData[key]
                    name = key
                    value = rawPMD[DATA_VALUE_TAG]
                    cType = rawPMD[DATA_TYPE_TAG]
                    docString = rawPMD[DATA_DOCSTRING_TAG]
                    index = rawPMD[DATA_INDEX_TAG]
                    attribs = rawPMD[DATA_ATTRIBUTES_TAG]
                    gsSDF.add_PMD(name, value, cType, 
                                 docString, index, attribs)

                pdebug('\nGenerated SDF Structure:')
                pprint_debug(gsSDF.adapt())
                pdebug( ('='*80)+'\n' )
                
                
        def load_groups(data, threads, configMembers):
            """ Load raw group data into GSGroups.
            
            @param data: The groups subsection of the raw parsed
                configuration dictionary.
            @param threads: The threads 
            """
            gsGroups = {}
            GROUP, MEMBERS = range(2)
            if debug_level >= 2:
                print 'Loading Group Definitions:'
                print '    Raw Group Data:'
                pprint.pprint(data)
                print '\n'

        
            #stage one, get groups
            for grp in data.keys():
                rawGroup = data[grp]
                name = grp
                sdf = rawGroup[GROUP_SDF_TAG]
                attributes = rawGroup[GROUP_ATTRIBUTES_TAG]
                perGroupData = rawGroup[GROUP_PGD_TAG]
                members = rawGroup[GROUP_MEMBERS_TAG]
                                
                # Debug message showing the raw dictionary
                # for a particular group, and the loaded 
                # information by name.
                #
                if debug_level >= 2:
                    print ('='*80)
                    print 'Group %s Raw Data:' % grp
                    pprint.pprint(rawGroup)
                    print '\nLoaded Information:'
                    print 'Name: %s' % name
                    print 'Attributes: %s' % attributes
                    print 'Per Group Data: %s' % perGroupData
                                        
                # Create the group, add attributes and add the 
                # preliminary group data to the gsGroups data structure
                # for later build of the hierarchy.
                # 
                group = GSGroup(name, sdf, None)
                group.update_attributes(attributes)
                gsGroups[name] = (group, members)
                self._members.append(group)
                # Debug message showing the GSMember
                # parsed back into a dictionary that it 
                # would be used in the parser to write it 
                # back to the file. Used as a sanity check 
                # against the above information.
                #
                if debug_level >= 2:
                    print '\nGenerated GSGroup Structure:'
                    pprint.pprint(group.adapt())
                    print ('='*80)+'\n' 
                    
            #stage 2 build groups
            #stage 2.1 get root
            if debug_level >= 3:
                print ('Group raw data contains expected'
                       +' super root key \'%s\': %s\n'
                     % (self.superRootName, data.has_key(self.superRootName)))
            

            # Raise and error if the super root is specified and not defined
            # as a group structure within the the group data.
            #
            if not gsGroups.has_key(self.superRootName):
                raise KeyError('GSHierarchy Error(9): '
                               'Cannot continuing building GSHierarchy. Super'
                               ' Root not defined in configuration group'
                               ' data.', 
                               self.superRootName )    
            else:
                def build_group_R(grpName, grpData, threads, configMembers ):
                    """Builds the group by recursively building and adding 
                    all of the members of the group.
                    
                    @param grpName: Name of the group to be built.
                    @param grpData: The data dictionary
                    @note: The grpData dictionary is set up with a structure
                        as such:
                        grpData = { GROUP_NAME : ( GROUP, MEMBERS ), ...}
                        So that GROUP_NAME is the string name of the group 
                        as a key. The tuple value has the raw group data at
                        index 0 and members data at index 1, which are defined 
                        as global variables GROUP=0 and MEMBERS=1.
                    """
                    
                    if debug_level >= 2:
                        print 'Building group: %s' % grpName
                    group = grpData[grpName][GROUP]
                    members = grpData[grpName][MEMBERS]
                    # Iterate through the members of the 
                    # group to check if they are threads or groups.
                    #
                    for member in members:
                        # Is the member a thread? 
                        #
                        if member in threads.keys():
                            # Making sure that the thread is in the 
                            # group of Members that have been defined. 
                            #
                            tName = member
                            tSpecName = threads[member]
                            configMbr = configMembers[tSpecName]
                            mbrThread = GSThread.wrap_member(configMbr)
                            mbrThread.set_name(tName)
                            group.add_thread(mbrThread)
                            self._members.append(mbrThread)
                            
                        elif member in grpData.keys():
                            build_group_R(member, grpData, threads, configMembers)
                            mbrGroup = grpData[member][GROUP]
                            group.add_group(mbrGroup)
                        # If member is not in threads and in groups than it 
                        # shows that the hierarchy is 
                        else:
                            #FIXME.DILLON : raise not found error
                            pass
                    pass
                
                self._superRoot = gsGroups[self.superRootName][GROUP]
                build_group_R(self.superRootName, gsGroups, threads, configMembers)
            
            pass
        
        def load_thread_specifications(data):
            """ Create Thread_Specifications
            
            @param data: The thread specification subsection of the configuration 
                dictionary.
            """
            gsThread_Specifications = {}
            if debug_level >= 2:
                print 'Loading Thread_Specification Definitions:'
                print '    Thread_Specification Definitions Raw Data:'
                pprint.pprint(data)
            
            # Make all of the raw thread_specification data into 
            # GSMember objects.
            # 
            for mbr in data.keys():
                rawThread_Specification = data[mbr]
                name = mbr
                attributes = rawThread_Specification[THREAD_SPECIFICATION_ATTRIBUTES_TAG]
                perMemberData = rawThread_Specification[THREAD_SPECIFICATION_PMD_TAG]
                doc = rawThread_Specification[THREAD_SPECIFICATION_COMMENT_TAG]
                                 
                # Debug message showing the raw dictionary
                # for a particular thread_specification, and the loaded 
                # information by name.
                #
                if debug_level >= 2:
                    print ('='*80)
                    print 'Thread_Specification %s Raw Data:' % mbr
                    pprint.pprint(rawThread_Specification)
                    print '\nLoaded Information:'
                    print 'Name: %s' % name
                    print 'Attributes: %s' % attributes
                    print 'Per Thread_Specification Data: %s' % perMemberData
                    print 'Comment: %s' % doc

                # Creating the GSMember from the none iterable
                # GSMember data.
                #
                member = GSMember( name, None, doc )
                
                # Using the GSMember methods to add the 
                # attributes list, and per member data 
                # dictionary.
                #
                member.update_attributes(attributes)
                member.update_PMD(perMemberData)
                
                # Simply adding the created member to 
                # the loaded members list.
                #
                gsThread_Specifications[name] = member
                
                # Debug message showing the GSMember
                # parsed back into a dictionary that it 
                # would be used in the parser to write it 
                # back to the file. Used as a sanity check 
                # against the above information.
                #
                if debug_level >= 2:
                    print '\nGenerated GSMember Structure:'
                    pprint.pprint(member.adapt())
                    print ('='*80)+'\n' 

            return gsThread_Specifications
        
        
    
        
        def load(config):
            """ Start the segmentation of the load process.
            
            @param config: The raw configuration dicationary from the 
                parsing the .gsh configuration file with configutility.parseConfigFile().
            """

            if debug_level >= 2:
                # 1) Print Debug Messages and pretty printing the 
                # config dictionary. 
                #
                print 'Loading Configuration'
                print '    Raw Data:'
                pprint.pprint(config)

            # 2) Check the config dictionary against the expected tags
            # for parsing config into the GSHierarchy.
            #
            if config.keys() != TOP_LEVEL_TAGS:
                configTags = set(config.keys())
                expectedTags = set(TOP_LEVEL_TAGS)
                
                # Incorrect (unexpected) tags are defined by the
                # difference of the configuration tags and expected
                # tags.
                #
                incorrectTags = configTags - expectedTags
                # Undefined (expected) tags are defined by the
                # difference of the expected tags and configuration
                # tags.
                #              
                undefinedTags = expectedTags - configTags
                
                if debug_level >= 2:
                    # Print the Unexpected and Undefined tags
                    # for the configuration.
                    #
                    print 'Unexpected tags found in config:'
                    pprint.pprint(list(incorrectTags))
                    print 'Undefined tags found in config:'
                    pprint.pprint(list(undefinedTags))

                # Unexpected Tags, meaning incorrect configuration.
                # Raise ValueError, since it isn't desired to load 
                # incorrect information.
                #
                if len(incorrectTags) > 0:
                    raise ValueError('The configuration is not a proper GSH Dictionary.'/
                                         '\nThere was an unrecognized tag(s).',
                                         config, list(incorrectTags))
                # Expected and not found tags, meaning incorrect configuration.
                # Raise ValueError, since it isn't possible to load the 
                # expected information from the hierarchy.
                #
                if len(undefinedTags) > 0:
                    raise ValueError('The configuration is not a proper GSH Dictionary.'/
                                         '\nThere was/were a/an unrecognized tag(s).',
                                         config, list(undefinedTags))

                    
            # Loading the root and application attachement
            # point data.
            #
            load_setup_data( config[GSH_INSTALLATION_TAG] )

            # 
            #
            load_SDF( config[SDF_SPECIFICATION_TAG] )
            
            # Loading and creating a GSMember data structures 
            # from which to define groups and tasks, from the 
            # the thread_specifications section within the config dictionary.
            #
            config_thread_specifications = \
                load_thread_specifications( config[THREAD_SPECIFICATION_TAG] )
            
            # Loading the GSGroups defined in the groups section,
            # and filling the attaching it to the information
            # to the correct GSMember structure.
            #
            configThreads = config[THREADS_TAG]
            
            # Loading the GSGroups defined in the groups section.
            #
            load_groups( config[GROUPS_TAG], configThreads, config_thread_specifications)
            
        
        # Starting the loading/decomposition process
        # using the passed config dict.
        #
        if debug_level >= 2:
            pprint.pprint(config)
        load(config)


    def add_empty_group(self, group):
        """ 
        Add the Group to the Parent Group.
       
        :param group: The Group to add to parent.
        :type group: GSGroup
        :param parent: The parent group within the hierarchy to which to
            add group.
        :type parent: GSGroup   
        """
        # Simple check to make sure that the thread is actually a Group.
        #
        if not isinstance(group, GSGroup):
            raise TypeError('GSHierarchy Error(9): group is' 
                        'not a GSGroup.', thread)
        
        self.empty_groups.append(group)

    
    def get_empty_groups(self):
        return self.empty_groups

        
    def add_group(self, group, parent):
        """ 
        Add the Group to the Parent Group.
       
        :param group: The Group to add to parent.
        :type group: GSGroup
        :param parent: The parent group within the hierarchy to which to
            add group.
        :type parent: GSGroup   
        """
        # Simple check to make sure that the thread is actually a Group.
        #
        if not isinstance(group, GSGroup):
            raise TypeError('GSHierarchy Error(5): group is' 
                        'not a GSGroup.', thread)
        
        # Make sure that the parent is a GSGroup and it is in the 
        # Hierarchy's members.
        # Obviously adding a thread to a thread is not allowed,
        # and adding a thread to a non-existent group is also
        # prevented.
        #
        if parent is None:
            parent = self._superRoot
        elif not parent.__class__ is GSGroup:
            raise TypeError('GSHierarchy Error(6): Cannot add group'
                            ' parent is not a GSGroup.', parent)
                
        pdebug("Adding GSThread %s to the GSGroup %s." % (thread.getName(), parent.getName()),
                   DEBUG_LEVEL.HIGH )
        parent.add_thread(thread)
    
    def add_thread(self, thread, parent):
        """
         Add thread to the Parent Group.
       
        :param thread: The thread to add to the parent group.
        :type thread: GSThread
        :param parent: The parent group within the hierarchy to which to
            add group.
        :type parent: GSGroup    
        """
        # Simple check to make sure that the thread is actually a thread.
        #
        if not thread.__class__ is GSThread:
            raise TypeError('GSHierarchy Error(7): Thread is not a GSThread.', thread)
        
        # Make sure that the parent is a GSGroup and it is in the 
        # Hierarchy's members.
        # Obviously adding a thread to a thread is not allowed,
        # and adding a thread to a non-existent group is also
        # prevented.
        #
        if parent is None:
            parent = self._superRoot
        elif not parent.__class__ is GSGroup:
            raise TypeError('GSHierarchy Error(8): parent is not a GSGroup.', parent)
                        
        pdebug("Adding GSThread %s to the GSGroup %s." % (thread.getName(), parent.getName()),
                   DEBUG_LEVEL.HIGH )
        parent.add_thread(thread)

        pass
    
    def remove_group(self, group, parent):
        """
        Remove a group from the hierarchy, return the
        removed group (or None).
        
        :param group: The Group to remove.
        :type group: GSGroup
        :param parent: The parent Group from which to remove group. 
        :type parent: GSGroup
        :returns: The Group removed from parent, or None.
        :rtype: GSGroup or None
        """
        if not isinstance(group, GSGroup):
            raise TypeError("GSHierarchy Error(1): Cannot remove group, "
                            "it is not a GSGroup.", group)
        if not isinstance(parent, GSGroup):
            raise TypeError("GSHierarchy Error(2): Cannot remove group, "
                            "parent is not a GSGroup.", parent)
        parent_members = parent.get_members()
        if not group in parent_members:
            return None
        return parent_members.pop(group)
    
    def remove_thread(self, thread, parent):
        """
        Remove a Thread from the `GSHierarchy`, return the 
        removed thread (or None).
        
        :param thread: The Group to remove.
        :type thread: GSGroup
        :param parent: The parent Group from which to remove group. 
        :type parent: GSGroup
        :returns: The Group removed from parent, or None.
        :rtype: GSGroup or None
        """
        if not isinstance(thread, GSThread):
            raise TypeError("GSHierarchy Error(3): Cannot remove thread, "
                            "it is not a GSThread.", thread)
        if not isinstance(parent, GSGroup):
            raise TypeError("GSHierarchy Error(4): Cannot remove thread, "
                            "parent is not a GSGroup.", parent)

        parent_members = parent.get_members()
        if not thread in parent_members:
            return None
        return parent_members.pop(thread)
    

    def get_super_root(self):
        """
        Returns the reference to the GSGroup which is the root group of 
        the GSHierarchy.
      
        .. note:: It is not just a `root` in anticipation of having local roots for 
            mode changes.
            
        :returns: The *super* or *main* hierarchy root.
        :rtype: GSGroup
        """
        return self._superRoot

    def adapt(self):
        """
        Creates the dictionary from which the .gsh configuration file
        can be created.
        
        .. todo:: Implement this after talking to Doug about being
            able to reverse the parser to have dictionary->config_file
            writing.
        """
        pass

    def get_all_members(self):
        """
        :returns: All members from every group in the `GSHierarchy.
        :rtype: list of `GSGroup` and `GSThread` objects.
        """
        all_members = []
        def populate_members_R(root_group):
            for member in root_group.members:
                if isinstance(member, GSGroup):
                    populate_members_R(member)
                all_members.append(member)
        populate_members_R(self.get_super_root())
        return all_members

    def pprint(self):
        """
        Prints the :class:`GSHierarchy` by traversing the 
        tree recursively, starting at the root, and calling 
        each members `pprint()`
        """
        print ' GROUP SCHEDULING HIERARCHY'
        print '------------------------------'
        if self._superRoot:
            self._superRoot.pprint()
        else:
            print 'None'
        
        print
        print
        print ' UNATTACHED GROUPS'
        print '-------------------------------'
        if len(self.get_empty_groups()) > 0:
            for group in self.get_empty_groups():
                group.pprint()
        else:
            print 'None'
    
    
    
    
        
