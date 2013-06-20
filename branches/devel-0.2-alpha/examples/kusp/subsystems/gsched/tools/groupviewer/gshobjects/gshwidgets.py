#!/usr/bin/env python
""" GSHWidgets.py

Author:    Dillon Hicks
Email:    hhicks[at]ittc.ku.edu
Updted: 29.06.2009
Summary: 
"""
import sys
import os
import types
import copy
from PyQt4.QtGui import *
from PyQt4 import QtCore
from PyQt4.Qt import *
from DGui import *
import gshobjects
from gshsdf import *
from gshtoolbar import *
from builtinsdfs import *

#Path to the icons, There is a better way to do this.
ICONS_PATH = os.getcwd()+'/icons/'

#Headers for the Per Member Data Tree in the Per Member Data Tab 
#within the GroupPageWidget
PER_MEMBER_HEADERS = ('Member/Attribute Name', 'Type', 'Value', 
                        'Required', 'Default')

#Headers for the Per Group Data Tree in the Per Group Data Tab
#within the GroupPageWidget
PER_GROUP_HEADERS = ('Attribute Name', 'Type', 'Value', 'Required', 'Default')

#Headers for SDF Tree in the SDF Properties Tab
#within the GroupPageWidget
SDF_EDITOR_HEADERS = ('Name', 'Type', 'Value', 'Required', 'Default')

#Headers for the Member Tree in the Member Tree Tab
#within the GroupPageWidget
GROUP_MEMBER_HEADERS = ('Name', 'Type', 'SDF' , '# Members')

ATTRIBUTE_HEADERS = ('Name', 'Value', 'Description')

#To Be Defined
ATTRIBUTES_BY_NAME = ('Attribute0','Attribute1','Attribute2',
                          'Attribute5','Attribute4','Attribute3')

#Index of the value desired within the PER_MEMBER_HEADERS
MEMBER_NAME = 0
MEMBER_TYPE = 1
MEMBER_VALUE = 2
MEMBER_REQUIRED = 3
MEMBER_DEFAULT = 4

#Tab indexes of the GroupPageWidget 
PROPERTIES_TAB_INDEX = 0
MEMBER_TAB_INDEX = 1
PGD_TAB_INDEX = 2
PMD_TAB_INDEX = 3
SDF_TAB_INDEX = 4

COLUMN_WIDTH = 65

class MemberDataEditor(QWidget):
    INPUT_MINIMUM_WIDTH = 100
    INPUT_MAXIMUM_WIDTH = 100
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        #Widget Wide Settings
        mainLayout = QVBoxLayout()
        
        self.memberTree = QTreeWidget()
        

        self.saveButton = QPushButton('Save')
        self.clearEditButton = QPushButton('Cancel')
        self.nameLabel = QLabel('Name: ')
        self.nameEdit = QLineEdit()
        self.nameEdit.setMinimumWidth(self.INPUT_MINIMUM_WIDTH)
        self.nameEdit.setReadOnly(True)
        
        self.typeLabel = QLabel('Type: ')
        self.typeComboBox = QComboBox()
        self.typeComboBox.addItems(SDF_DATA_TYPES_BY_NAME)
        self.typeComboBox.setMaximumWidth(self.INPUT_MAXIMUM_WIDTH)
        
        self.valueLabel = QLabel('Value: ')
        self.valueEdit = QLineEdit()
        
        #self.valueEdit.setMinimumWidth(self.INPUT_MINIMUM_WIDTH)
        self.requiredCheckBox = QCheckBox('Is required?')
        
        self.defaultLabel = QLabel('Default Value')
        self.defaultEdit = QLineEdit()
        self.defaultEdit.setReadOnly(True)
        
        treeButtonLayout = QHBoxLayout()
        treeButtonLayout.addStretch()
        
        editLayout = QGridLayout()
        editLayout.addWidget(self.nameLabel, 2, 0)
        editLayout.addWidget(self.nameEdit, 2, 1)
        editLayout.addWidget(self.typeLabel, 2, 2)
        editLayout.addWidget(self.typeComboBox, 2, 3)
        editLayout.addWidget(self.valueLabel, 3, 0)
        editLayout.addWidget(self.valueEdit, 3, 1)
        #editLayout.addWidget(self.requiredCheckBox, 3, 4)
        editLayout.addWidget(self.defaultLabel, 3, 2)
        editLayout.addWidget(self.defaultEdit, 3, 3)
        editLayout.addItem(QSpacerItem(0,20), 4, 0)
        editLayout.addWidget(self.saveButton, 5, 3)
        editLayout.addWidget(self.clearEditButton, 5, 4)
        
        mainLayout.addWidget(self.memberTree)
        mainLayout.addLayout(treeButtonLayout)
        mainLayout.addSpacing(20)
        mainLayout.addLayout(editLayout)
        
        self.setLayout(mainLayout)
        
        
class GroupPageWidget(QWidget):
    """The Group Page Widget provides a way to edit group data."""
    MAXIMUM_WIDTH = 200
    def __init__(self, group=None, parent=None):
        QWidget.__init__(self, parent)
        #Widget Wide Settings
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.currentGroup = group

            
        # Child/PGD/PMD Tree Widgets
        treeLayout = QVBoxLayout()
        treeLayout.setSpacing(0)
        treeTabs = QTabWidget()
        self.treeTabs = treeTabs
        #Group Properties (name, ccsm name, sdf attributes)
        propertyFrame = QFrame()
        propertyLayout = QGridLayout()
        propertyFrame.setLayout(propertyLayout)
        nameLabel = QLabel('Name: ')
        self.nameEdit = QLineEdit()
        nameLabel.setBuddy(self.nameEdit)
        ccsmNameLabel = QLabel('CCSM Member\n\tName: ')
        self.ccsmNameEdit = QLineEdit()
        
        self.sdfComboBox = QComboBox()
        self.sdfComboBox.addItems(SCHEDULING_FUNCTIONS_BY_NAME)
        self.sdfComboBox.setMaximumWidth(self.MAXIMUM_WIDTH)
        indexOfLast = self.sdfComboBox.count()
        self.sdfComboBox.insertSeparator(indexOfLast)
        self.sdfComboBox.setEditable(True)
        
        attributeLayout = QVBoxLayout()
        attributeWidget = QWidget()
        attributeWidget.setLayout(attributeLayout)
        self.attributeComboBox = QComboBox()
        self.attributeComboBox.addItems(ATTRIBUTES_BY_NAME)
        addAttributeLabel = QLabel('Attribute:')
        attributeToolBar = GSHToolBar(ActionFlags.LIST_ACTIONS,
                                      Qt.Horizontal)
        attributeLabel = QLabel('Member Attributes')
        attributeLabel.setAlignment(Qt.AlignCenter)
        self.attributeTree = QTreeWidget()
        self.attributeTree.setHeaderLabels(ATTRIBUTE_HEADERS)
        attrSecondaryLayout = QHBoxLayout()
        attrSecondaryLayout.addWidget(addAttributeLabel)
        attrSecondaryLayout.addWidget(self.attributeComboBox)
        attrSecondaryLayout.addWidget(attributeToolBar)
        attrSecondaryLayout.addStretch()
        attributeLayout.addWidget(attributeLabel)
        attributeLayout.addWidget(self.attributeTree)
        attributeLayout.addLayout(attrSecondaryLayout)
        
        SDFWidget = QWidget()
        SDFLayout = QVBoxLayout()
        SDFWidget.setLayout(SDFLayout)
        SDFSecondaryLayout = QHBoxLayout()
        self.SDFPropertiesLabel = QLabel('SDF Properties')
        self.SDFPropertiesLabel.setAlignment(Qt.AlignCenter)
        self.SDFLabel = QLabel('SDF:')
        SDFSecondaryLayout.addWidget(self.SDFLabel)
        SDFSecondaryLayout.addWidget(self.sdfComboBox)
        SDFSecondaryLayout.addStretch()
        #SDFSecondaryLayout.addWidget(self.sdfComboBox)
        #SDFSecondaryLayout.addWidget(self.SDFLabel)
        self.SDFTree = QTreeWidget()
        self.SDFTree.setHeaderLabels(SDF_EDITOR_HEADERS)
        SDFLayout.addWidget(self.SDFPropertiesLabel)
        SDFLayout.addWidget(self.SDFTree)
        SDFLayout.addLayout(SDFSecondaryLayout)
        ## Structuring layout
        ### Row 0
        propertyLayout.addWidget(nameLabel, 0, 0)
        propertyLayout.addWidget(self.nameEdit, 0, 1)
        propertyLayout.addWidget(ccsmNameLabel, 0, 2)
        propertyLayout.addWidget(self.ccsmNameEdit, 0, 3)
        ### Row 1
        #propertyLayout.addWidget(sdfLabel, 1, 2)
        #propertyLayout.addWidget(self.sdfComboBox, 1, 3)
        #propertyLayout.setColumnStretch(4, 20)
        ### Row 2        
        propertyLayout.addWidget(attributeWidget, 2, 0, 1, 5)
        ### Row 3
        propertyLayout.addWidget(SDFWidget, 3, 0, 1, 5)
        
        treeTabs.addTab(propertyFrame,'Group Properties')
        
        
        ## Child (members) View
        memberAttributeWidget = QWidget()
        memberAttributeLayout = QVBoxLayout()
        memberLabel = QLabel('Members')
        memberLabel.setAlignment(Qt.AlignHCenter)
        attributeLabel = QLabel('Attributes')
        attributeLabel.setAlignment(Qt.AlignHCenter)
        self.childTree = QTreeWidget()
        self.childTree.setHeaderLabels(GROUP_MEMBER_HEADERS)
        self.memberToolBar = GSHToolBar(ActionFlags.GROUP_ACTIONS,
                                        Qt.Horizontal)
        memberAttributeLayout.addWidget(memberLabel)
        memberAttributeLayout.addWidget(self.childTree)
        memberAttributeLayout.addWidget(self.memberToolBar)
        memberAttributeWidget.setLayout(memberAttributeLayout)
        treeTabs.addTab(memberAttributeWidget, 'Members')
                
        ##Per Group Data TreeWidget
        self.groupEditor = MemberDataEditor()
        self.groupTree = self.groupEditor.memberTree
        self.groupTree.setHeaderLabels(PER_GROUP_HEADERS)
        treeTabs.addTab(self.groupEditor, 'Per Group Data')
        
        ##Per Member Data Widget TreeWidget
        self.memberEditor = MemberDataEditor() 
        self.memberTree = self.memberEditor.memberTree
        self.memberTree.setHeaderLabels(PER_MEMBER_HEADERS)
        treeTabs.addTab(self.memberEditor, 'Per Member Data')
    
        treeLayout.addWidget(treeTabs)

        #Signals
        #selectRow = lambda row, column: self.memberTable.setRangeSelected(QTableWidgetSelectionRange(row, 0, row, 2), True)
        self.connect(self.memberTree,
                     QtCore.SIGNAL('itemClicked(QTreeWidgetItem*,int)'),
                      self.editMemberData)
        #self.connect(addButton, QtCore.SIGNAL('clicked()'), self.createNewMember)
        self.connect(self.sdfComboBox,
                     QtCore.SIGNAL('currentIndexChanged(QString)'),
                     self.__reloadSDF)
        self.connect(self.nameEdit,
                     QtCore.SIGNAL('textEdited(QString)'),
                     self.updateGroupName)
        if not self.currentGroup is None:
            self.connect(self.currentGroup,
                         QtCore.SIGNAL('memberAdded'),
                         self.__reloadData)
            self.connect(self.memberToolBar,
                                QtCore.SIGNAL('addGroup'),
                                self.addMemberGroup)
            self.connect(self.memberToolBar,
                                QtCore.SIGNAL('addTask'),
                                self.addMemberThread)
        
        self.connect(attributeToolBar, 
                     QtCore.SIGNAL('addGroup'),
                     self.addMemberAttribute)
        
        #Layout Settings
        #mainLayout.addWidget(propertyFrame)
        mainLayout.addLayout(treeLayout)
        self.__reloadData()
        self.setLayout(mainLayout)
    
    def __reloadSDF(self, SDFName):
        groupSDF= SCHEDULING_FUNCTIONS[str(SDFName)]
        self.currentGroup.resetSDF(groupSDF)
        self.loadData(self.currentGroup)
    
    def __loadSDF(self, SDF):
        SDF = SDF.getName()
        self.SDFPropertiesLabel.setText('%s SDF Properties'%SDF)
    	groupSDF = SCHEDULING_FUNCTIONS[SDF]
        SDFIndex = self.sdfComboBox.findText(SDF)
    	self.sdfComboBox.setCurrentIndex(SDFIndex)
        self.SDFTree.clear()
    	self.SDFTree.setSortingEnabled(False)
    	self.SDFTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        PGDItem = QTreeWidgetItem(['Per Group Data'])
        PMDItem = QTreeWidgetItem(['Per Member Data'])
        allPGD = groupSDF.getAllPGD()
        
        if len(allPGD) > 0:
            self.treeTabs.setTabEnabled(PGD_TAB_INDEX, True)
            for PGD in groupSDF.getAllPGD():
                fields = PGD.asFields()
                PGDItem.addChild(QTreeWidgetItem(fields))        
        else:
            self.treeTabs.setTabEnabled(PGD_TAB_INDEX, False)
            PGDItem.font(0).setItalic(True)
            PGDItem.setDisabled(True)
        
        allPMD = groupSDF.getAllPMD()
        if len(allPMD) > 0:
            self.treeTabs.setTabEnabled(PMD_TAB_INDEX, True)
            for PMD in allPMD:
                fields = PMD.asFields()
                PMDItem.addChild(QTreeWidgetItem(fields))
        else:
            self.treeTabs.setTabEnabled(PMD_TAB_INDEX, False)
            PMDItem.font(0).setItalic(True)
            PMDItem.setDisabled(True)
        
    	self.SDFTree.addTopLevelItems([PGDItem, PMDItem])
        self.SDFTree.expandAll()

    def __reloadData(self):
        self.loadData(self.currentGroup)
        
    def loadData(self, group):
        """Loads the infomation contained within group into the 
        GroupPageWidget Editor tabs."""
        self.currentGroup = group
        name = self.currentGroup.getName()
        ccsmName = self.currentGroup.getCCSMName()
        self.nameEdit.setText(name)
        self.ccsmNameEdit.setText(ccsmName)
        
        #Clearing all the group trees to prepare for (re)initalization
        self.childTree.clear()
        self.childTree.setSortingEnabled(False)
        self.childTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.groupTree.clear()
        self.groupTree.setSortingEnabled(False)
        self.groupTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.memberTree.clear()
        self.memberTree.setSortingEnabled(False)
        self.memberTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        #Adding each member to 
        for member in self.currentGroup.getMembers():
            self.childTree.addTopLevelItem(member.asShortItem())   
        #Adding the Per Group Datum 
        self.groupTree.addTopLevelItems(self.currentGroup.getPGDRecords())
        self.memberTree.addTopLevelItems(self.currentGroup.getPMDRecords())
        self.memberTree.expandAll()
    

        self.childTree.resizeColumnToContents(0)
        self.SDFTree.resizeColumnToContents(0)
        self.memberTree.resizeColumnToContents(0)
        self.groupTree.resizeColumnToContents(0)
        
        self.childTree.setColumnWidth(1,COLUMN_WIDTH)
        self.SDFTree.setColumnWidth(1,COLUMN_WIDTH)
        self.memberTree.setColumnWidth(1,COLUMN_WIDTH)
        self.groupTree.setColumnWidth(1,COLUMN_WIDTH)        

        self.childTree.setColumnWidth(2,COLUMN_WIDTH)
        self.SDFTree.setColumnWidth(2,COLUMN_WIDTH)
        self.memberTree.setColumnWidth(2,COLUMN_WIDTH)
        self.groupTree.setColumnWidth(2,COLUMN_WIDTH)

        self.childTree.setColumnWidth(3,COLUMN_WIDTH)
        self.SDFTree.setColumnWidth(3,COLUMN_WIDTH)
        self.memberTree.setColumnWidth(3,COLUMN_WIDTH)
        self.groupTree.setColumnWidth(3,COLUMN_WIDTH)
        
        self.SDFTree.resizeColumnToContents(4)
        self.memberTree.resizeColumnToContents(4)
        self.groupTree.resizeColumnToContents(4)
        
        self.__loadSDF(self.currentGroup.getSDF())
        
    def addMember(self, name, type, value, parent=None):
        """Adds a row to the table."""
        newItem = QTreeWidgetItem([str(name), str(type), str(value)])
        if parent is None:
            self.memberTree.addTopLevelItem(newItem)
        else:
            parent.addChild(newItem)
        return newItem
    
        
    def createNewMember(self):
        """Creates a new temporary row that can be edited."""
        #newRow = self.memberTree.rowCount()
        newName = 'New Member'
        newType = str.__name__
        newValue = '<Enter Data>'
        self.addMember(newName, newType, newValue) 
        
    
    
    def editMemberData(self, item, column):
        """ Loads the item info into the editable widgets on the bottom part of
        the tabbed widget.
        
        Activated when a PMD Tree Item is clicked. Allows the user to edit
        the value of the PMD Item. Only saved when the 'save' button is 
        clicked."""
        mName = item.text(MEMBER_NAME)
        mType = item.text(MEMBER_TYPE)
        mValue = item.text(MEMBER_VALUE)
        mRequired = bool(item.text(MEMBER_REQUIRED))
        mDefault = item.text(MEMBER_DEFAULT)
        #if not memberType in SDF_DATA_TYPES_BY_NAME:
        #    return
        if mType in SDF_DATA_TYPES_BY_NAME:
            self.memberEditor.nameEdit.setText(mName)
            typeIndex = list(SDF_DATA_TYPES_BY_NAME).index(mType)
            self.memberEditor.typeComboBox.setCurrentIndex(typeIndex)
            self.memberEditor.valueEdit.setText(mValue)
            self.memberEditor.requiredCheckBox.setChecked(mRequired)
        
    
    def addMemberGroup(self):
        newGroup = gshobjects.GSHGroup()
        self.currentGroup.addMember(newGroup)

    def addMemberThread(self):
        newThread = gshobjects.GSHThread()
        self.currentGroup.addMember(newThread)
    
    def updateGroupName(self, nextText):
        """Updates the GSHGroups name to the Text Edit Text."""
        newName = self.nameEdit.text()
        if len(newName) == 0:
            newName = '<Unamed Group>'
            self.nameEdit.setText(newName)
            self.nameEdit.selectAll()
            
        self.currentGroup.setName(newName)
        #For use to change the tab heading when the
        #groups name changes.
        self.emit(QtCore.SIGNAL('groupNameChanged'))
    
    def addMemberAttribute(self):
        attribute = self.attributeComboBox.currentText()
        attributeItem = QTreeWidgetItem([attribute])
        self.attributeTree.addTopLevelItem(attributeItem)
class ThreadPageWidget(QWidget):
    """The Group Page Widget provides a way to edit group data."""
    MAXIMUM_WIDTH = 200
    def __init__(self, thread=None, parent=None):
        QWidget.__init__(self, parent)
        #Widget Wide Settings
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.currentThread = thread

            
        # Child/PGD/PMD Tree Widgets
        treeLayout = QVBoxLayout()
        treeLayout.setSpacing(0)
        treeTabs = QTabWidget()
        self.treeTabs = treeTabs
        #Group Properties (name, ccsm name, sdf attributes)
        propertyFrame = QFrame()
        propertyLayout = QGridLayout()
        propertyFrame.setLayout(propertyLayout)
        nameLabel = QLabel('Name: ')
        self.nameEdit = QLineEdit()
        nameLabel.setBuddy(self.nameEdit)
        ccsmNameLabel = QLabel('CCSM Member\nName: ')
        self.ccsmNameEdit = QLineEdit()
        
        self.sdfComboBox = QComboBox()
        self.sdfComboBox.addItems(SCHEDULING_FUNCTIONS_BY_NAME)
        self.sdfComboBox.setMaximumWidth(self.MAXIMUM_WIDTH)
        indexOfLast = self.sdfComboBox.count()
        self.sdfComboBox.insertSeparator(indexOfLast)
        self.sdfComboBox.setEditable(True)
        
        attributeLayout = QVBoxLayout()
        attributeWidget = QWidget()
        attributeWidget.setLayout(attributeLayout)
        attributeToolBar = GSHToolBar(ActionFlags.LIST_ACTIONS,
                                      Qt.Horizontal)
        attributeLabel = QLabel('Member Attributes')
        attributeLabel.setAlignment(Qt.AlignCenter)
        attributeTree = QTreeWidget()
        attributeTree.setHeaderLabels(ATTRIBUTE_HEADERS)
        attributeLayout.addWidget(attributeLabel)
        attributeLayout.addWidget(attributeTree)
        attributeLayout.addWidget(attributeToolBar)
        
        SDFWidget = QWidget()
        SDFLayout = QVBoxLayout()
        SDFWidget.setLayout(SDFLayout)
        SDFSecondaryLayout = QHBoxLayout()
        self.SDFLabel = QLabel('SDF Properties')
        self.SDFLabel.setAlignment(Qt.AlignCenter)
        SDFSecondaryLayout.addWidget(self.sdfComboBox)
        SDFSecondaryLayout.addWidget(self.SDFLabel)
        self.SDFTree = QTreeWidget()
        self.SDFTree.setHeaderLabels(SDF_EDITOR_HEADERS)
        SDFLayout.addLayout(SDFSecondaryLayout)
        SDFLayout.addWidget(self.SDFTree)

        ## Structuring layout
        ### Row 0
        propertyLayout.addWidget(nameLabel, 0, 0)
        propertyLayout.addWidget(self.nameEdit, 0, 1)
        propertyLayout.addWidget(ccsmNameLabel, 0, 2)
        propertyLayout.addWidget(self.ccsmNameEdit, 0, 3)
        ### Row 1
        #propertyLayout.addWidget(sdfLabel, 1, 2)
        #propertyLayout.addWidget(self.sdfComboBox, 1, 3)
        #propertyLayout.setColumnStretch(4, 20)
        ### Row 2        
        propertyLayout.addWidget(attributeWidget, 2, 0, 1, 5)
        ### Row 3
        #propertyLayout.addWidget(SDFWidget, 3, 0, 1, 5)
        
        self.loadData(self.currentThread)
        self.setLayout(propertyLayout)
 
    def loadData(self, thread):
        name = self.currentThread.getName()
        ccsmName = self.currentThread.getCCSMName()
        self.nameEdit.setText(name)
        self.ccsmNameEdit.setText(ccsmName)