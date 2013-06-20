#!/usr/bin/env python
"""
:mod:`gssdf` -- Gsched Scheduling Decision Functions
=====================================================
    :synopsis: SDFTemplate/SDF PMD/PGD attribute data structures.

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>

.. note:: This is a module that is currently under development and 
    not in use. This documentation will change frequently, more so than
    our other documentation. 
    
    **The Future Plan:** In the long run, this module will have the 
    classes and other information for user specified-dynamically loaded sdfs.


"""
import copy
import types
from sip import voidptr

#Supported Types for PMD and PGD
SDF_DATA_TYPES = {'Integer' : types.IntType,
        'Unsigned Integer' : types.IntType,
        'Long' : types.LongType,
        'Unsigned Long' : types.LongType,
         'Boolean' : types.BooleanType,
         'String'  : types.StringType,
         'Handle'  : voidptr }

#
SDF_DEFAULT_VALUES = {'Integer' : 0,
                       'Unsigned Integer' : 0,
                       'Long': 0L,
                       'Unsigned Long' : 0L,
                       'Boolean' : False,
                       'String' : '',
                       'Handle' : 'Void*'}

#Values of the types as a tuple
SDF_DATA_TYPES_BY_VALUE = tuple(SDF_DATA_TYPES.values())

#Names of the types as a tuple
SDF_DATA_TYPES_BY_NAME = tuple(SDF_DATA_TYPES.keys())


class SDFData():
    """Data structure for generic SDF PMD/PGD."""
    def __init__(self, name,  cType='Integer', value=None,  required=True, doc='', handle=None, member=None):
        """Initalizes all attributes of the SDFData Class.
        
        @param name: Name of the SDFData (ie 'Priority' or 'Quantum').
        @param value: The value of the associated PMD or PGD.
        @param docString: A string describing what the PMD/PGD is or for what 
            it is used.
        @param required: Indicates whether or not the PMD/PGD value is required
            to be entered during SDF Design time so as not to cause an
            kernel SDF operation/load error.
        @param handle: Included for possible future use (refer to conversation with
            doug as outlined in the wiki).
        @param member: The pointer to the member to which the SDF Data is associated.
        """
        
        self.__name = name
        self.__docString = doc
        self.__isRequired = required
        self.__cType = cType
        self.__handle = handle    
        self.__value = value
        self.__member = member
        if self.__value is None:
            self.__value = SDF_DEFAULT_VALUES[cType]
        
    def getName(self):
        """Returns the Name attribute of the SDFData."""
        return self.__name
    
    def setName(self, name):
        """Sets SDFData.name to name."""
        self.__name = name
        
    def getType(self):
        """Returns the type attribute of the SDFData."""
        return self.__cType
    
    def setType(self, cType):
        self.__cType = cType
        
        
    def isRequired(self):
        """Returns true if the SDFData is a required 
        entry to be a valid SDF."""        
        return self.__isRequired
    
    def setRequired(self, required):
        """Sets the SDFData.idRequired to required."""
        self.__isRequired = required
    
    def getDocString(self):
        return self.__docString
    
    def setDocString(self, doc):
        self.__docString = str(doc)
    
    def getHandle(self): 
        """Returns the handle attribute of the SDFData."""
        return self.__handle
    
    def setHandle(self, handle):
        """Sets the SDFData.handle to handle."""
        self.__handle = handle
        
    def setValue(self, value):
        """Sets the value of the SDFData to value."""
        assert type(value) in SDF_DATA_TYPES_BY_VALUE
        self.__value = value
        
    def getValue(self):
        """Returns the value of the SDFData."""
        return self.__value
    
    def getMember(self):
        """Returns the member to which the SDFData is associated."""
        return self.__member
    
    def asFields(self):
        name = str(self.__name)
        dataType = str(self.getType())
        value = str(self.__value)
        required = str(self.__isRequired)
        docString = str(self.__docString)
        fields = [name, dataType, value, required, docString]
        print fields
        return fields
    
    def __deepcopy__(self, memo={}):
    
        name = self.getName()
        dataType = self.getType()
        required = self.isRequired()
        handle = self.getHandle()
        value = self.getValue()
        member = self.getMember()
        dataType = self.getType()
        docString = self.getDocString()
        cName = copy.deepcopy(name)
        cType = copy.deepcopy(dataType)
        cRequired = copy.deepcopy(required)
        cHandle = copy.deepcopy(handle)
        cValue = copy.deepcopy(value)
        cMember = copy.deepcopy(member)
        cDataType = copy.deepcopy(dataType)
        cDocString = copy.deepcopy(docString)
        
        return SDFData(cName, cDataType, cValue, cRequired,
                            cDocString, cHandle, cMember)

class SDFTemplate():
    """Specifies PGD and PMD for the SDF."""
    def __init__(self, name, codeName):
        """
        
        @param name: A human readable name for the SDF (ie 'Round Robin').
        @param codeName: The name of the SDF function as a string (ie 'sdf_rr').
        """
        self.__perGroupDataByName = {}
        self.__perGroupData = []
        self.__perMemberDataByName = {}
        self.__perMemberData = []
        self.name = name
        self.codeName = codeName
    
    def getName(self):
        return self.name
    
    def getCFunctionName(self):
        return self.codeName
    
    def __str__(self):
        return self.codeName
    
    def getAllPMD(self):
        return self.__perMemberData
    
    def getAllPGD(self):
        return self.__perGroupData
        
    def addPGD(self, name, dataType, required=True, doc='',  handle=None):
              
        PGD = SDFData(name,  dataType, None, required, doc,  handle)
        self.__perGroupData.append(PGD)
        self.__perGroupDataByName[name] = PGD
       
    def addPMD(self, name, dataType, required=True, doc='', handle=None):
        """Add a Per Member Data requirement to the SDF Template.""" 
        PMD = SDFData(name,  dataType, None, required, doc,  handle)
        self.__perMemberData.append(PMD)
        self.__perMemberDataByName[name] = PMD
        
    def copyAllPMD(self):
        """Returns a deepcopy of all of the PMD (Per Member Data)."""
        PMDCopy = []
        for PMD in self.__perMemberData:
            PMDCopy.append(copy.deepcopy(PMD))
        return PMDCopy
    
    def copyAllPGD(self):        
        PGDCopy = []
        for PGD in self.__perGroupData:
            PGDCopy.append(copy.deepcopy(PGD))
        return PGDCopy
    def copyPMD(self, name):
        PMD = self.__perMemberDataByName[name]
        return copy.deepcopy(PMD)
    
    def copyPGD(self, name):
        PGD = self.__perGroupDataByName[name]
        return copy.deepcopy(PGD)
    
    def removePMD(self, name):
        """Removes Per Member Data with SDFData.name == name.""" 
        pass
    
    def removePGD(self, name):
        """Removes Per Group Data with SDFData.name == name.""" 
        pass