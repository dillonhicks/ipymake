#!/usr/bin/env python
"""gschedarchitect

@author:    Dillon Hicks    
@organization: KUSP
@contact: hhicks[at]ittc[dot]ku[dot]edu
@summary:
        

"""

import sys
import os
import types
import copy
import pykusp.configutility as config
from pygsched.gsstructures import *
from PyQt4.QtGui import *
from PyQt4 import QtCore
from PyQt4.Qt import *
from PyQt4.QtWebKit import *

global dataManager
FILEPATH, HIERARCHY = range(2)

class QModularWindow(QWidget):
    def __init__(self, title='New Modular Window', parent=None):
        QWidget.__init__(self, parent)
        
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(2,2,2,2)
        mainLayout.setSpacing(0)
        self.__centralWidget = QWidget()
        self.__centralFrame = QFrame()
        self.__centralFrame.setFrameStyle(QFrame.StyledPanel)
        self.__centralLayout = QStackedLayout()
        self.__centralLayout.addWidget(self.__centralWidget)
        self.__centralFrame.setLayout(self.__centralLayout)
        self.__centralFrame.setSizePolicy(QSizePolicy.MinimumExpanding , QSizePolicy.MinimumExpanding)

        titleLayout = QHBoxLayout()
        titleLayout.setContentsMargins(1,2,1,2)
        self.__titleLabel = QLabel(title)
        titleFrame = QFrame()
        titleFrame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        closeButton = QPushButton('X')
        closeButton.setFixedSize(20,20)
        titleLayout.addWidget(self.__titleLabel)
        titleLayout.addStretch()
        titleLayout.addWidget(closeButton)
        titleFrame.setLayout(titleLayout)
        titleFrame.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        mainLayout.addWidget(titleFrame)
        mainLayout.addWidget(self.__centralFrame)
        self.setLayout(mainLayout)
        
    def setTitle(self, title):
        self.__titleLabel.setText(title)
        pass
    
    def title(self):
        return self.__titleLabel.text()
    
    def centralWidget(self):
        return self.__centralWidget
    
    def setCentralWidget(self, widget):
        self.__centralLayout.removeWidget(self.__centralWidget)
        self.__centralLayout.addWidget(widget)
        self.__centralWidget = widget
        


class GSArchitectDataManager(QObject):
    def __init__(self, parent=None):
        
        self.openConfigurations = []
        self.workspaceConfigs = []
        self.loadedSdfs = []
        
        # TODO: At start load predefined sdf configurations
        
        
        
    def loadConfig(self, filepath):
        configDict = config.parseConfigFile(filepath)
        try:
            gsh = GSHierarchy(configDict)
            self.openConfigurations.append([filepath, gsh])
        except KeyError, err:
            #Message Box Here?
            pass
        #emit uptdate signal
        pass
    
    def closeConfig(self, gsh):
        pass
    
    def creatNewConfig(self, configName):
        
        pass
    
    def loadSdf(self, filename):
        pass
    
    def saveConfig(self):
        pass

class GSTreeWidget(QTreeView):
    pass    



class GSSdfSummaryWidget(QWidget):
    """The SDF Summary Widget provides a widget that 
    displays readonly information about a Scheduling 
    Decision Function. This is used primarily as the 
    fourth tab in the GSMemberDataWidget.
    """
    def __init__(self, parent=None):
        # Widget wide settings
        QWidget.__init__(self, parent)
        
        # Layout
        mainLayout = QGridLayout()
        
        # Name of the SDF
        nameLabel = QLabel('Name:')
        nameEdit = QLineEdit('Sequential')
        nameEdit.setReadOnly(True)
        mainLayout.addWidget(nameLabel, 0, 0)
        mainLayout.addWidget(nameEdit, 0, 1)
        
        # The function name of the SDF
        functionLabel = QLabel('Scheduling Function: ')
        functionEdit = QLineEdit('sdf_seq')
        functionEdit.setReadOnly(True)
        functionLabel.setToolTip('The name of the Scheduling Function'
                                 ' within the kernel.')
        functionEdit.setToolTip('The name of the Scheduling Function'
                                 ' within the kernel.')
        
        mainLayout.addWidget(functionLabel, 0, 2)
        mainLayout.addWidget(functionEdit, 0, 3)
        
        # Shows the documentation over the SDF
        sdfDocBrowser = QTextBrowser()
        mainLayout.addWidget(sdfDocBrowser, 1, 0, 1, 4)
        
        # The frame contains the Per Member Data
        # and the Per Group Data.
        dataFrame = QFrame()
        dataFrame.setFrameStyle(QFrame.Box | QFrame.Sunken)
        frameLayout = QVBoxLayout()
        
        ## Per Member Data Table
        pmdLabel = QLabel('Per Member Data')
        pmdLabel.setAlignment(Qt.AlignHCenter)
        pmdTable = QTableWidget()
        frameLayout.addWidget(pmdLabel)
        frameLayout.addWidget(pmdTable)
        
        ## Per Group Data Table
        pgdLabel = QLabel('Per Group Data')
        pgdLabel.setAlignment(Qt.AlignHCenter)
        pgdTable = QTableWidget()
        frameLayout.addWidget(pgdLabel)
        frameLayout.addWidget(pgdTable)
            
        ## Setting the layout of the frame
        ## to the layout that contains
        ## PMD/PGD. 
        dataFrame.setLayout(frameLayout)
        
        # Adding the PMD/PGD frame to the main
        # layout.
        mainLayout.addWidget(dataFrame, 2, 0, 1, 4)
        
        # Set the layout of the SdfSummary widget to the
        # layout that contains the created widgets.
        self.setLayout(mainLayout)
                
class GSMemberDataToolBar(QWidget):
    """ Save, revert, and close buttons in a horizontal 
    layout toolbar. 
    """
    def __init__(self, parent=None):
        # Widget wide settings
        QWidget.__init__(self, parent)
        
        # Creating the layout for widget.
        mainLayout = QHBoxLayout()
        
        # Creates a 'save', 'revert', and 
        # 'close' buttons.
        saveButton = QPushButton('Save')
        revertButton = QPushButton('Revert')
        closeButton = QPushButton('Close')
        
        # Adding the buttons from above to the 
        # layout.
        mainLayout.addWidget(saveButton)
        mainLayout.addWidget(revertButton)
        mainLayout.addWidget(closeButton)
        
        # In this particular layout, this will
        # gives all of the buttons a left 
        # justification.
        mainLayout.addStretch()
        
        # Setting the layout of this widget
        # to the layout that conaints the buttons.
        self.setLayout(mainLayout)

class GSMemberDataWidget(QWidget):
    """This widget provides a way to display and 
    edit Per Member Data and Per Group Data.
    """
    def __init__(self, parent=None):
        # Widget wide settings
        QWidget.__init__(self, parent)
        
        # The layout of the widget
        mainLayout = QVBoxLayout()
        
        # The table that shows the members.
        membersTable = QTableWidget()
        memberDataEditLabel = QLabel('%s Per Member Data')
        mainLayout.addWidget(membersTable)
        mainLayout.addWidget(memberDataEditLabel)
        
        # The Per member/group Data edit table
        # and toolbar widgets.
        memberDataEditTable = QTableWidget()
        memberDataToolBar = GSMemberDataToolBar()
        mainLayout.addWidget(memberDataEditTable)
        mainLayout.addWidget(memberDataToolBar)
        
        # Set the layout of this widget to the layout
        # that contains the properly grouped widgets.
        self.setLayout(mainLayout)
        
class GSGroupInfoEditForm(QWidget):
    """Displays and provides edit widgets for the 
    name, ccsm name, sdf, doc string, and the Group's 
    parent.
    """
    def __init__(self, parent=None):
        # Widget wide settings
        QWidget.__init__(self, parent)
        
        # Creating the layout for the widget.
        mainLayout = QGridLayout()
        
        # Making the name widget for the
        # Group.
        nameLabel = QLabel('Name:')
        nameEdit = QLineEdit()
        # The coordinates for adding widgets are 
        # .addWidget( Y-coord, X-coord, Widget)
        mainLayout.addWidget(nameLabel, 0, 0)
        mainLayout.addWidget(nameEdit, 0, 1)
        
        # The CCSM Name widgets 
        ccsmNameLabel = QLabel('CCSM Name:')
        ccsmNameEdit = QLineEdit()
        mainLayout.addWidget(ccsmNameLabel, 0, 2)
        mainLayout.addWidget(ccsmNameEdit, 0, 3)
                
        # The SDF Choser widgets
        sdfLabel = QLabel('SDF: ')
        sdfComboBox = QComboBox() 
        mainLayout.addWidget(sdfLabel, 1, 0)
        mainLayout.addWidget(sdfComboBox, 1, 1)       
        
        # Get list of loaded sdfs to put 
        # into the sdf combo box.
        sdfDocEdit = QLineEdit('SDF Documentation String')
        sdfDocEdit.setReadOnly(True)
        mainLayout.addWidget(sdfDocEdit, 1, 2, 1, 2)
        
        # The parent info display widget
        parentLabel = QLabel('Parent:')
        parentEdit = QLineEdit('Parent')
        mainLayout.addWidget(parentLabel, 2, 0)
        mainLayout.addWidget(parentEdit, 2, 1)
        
        # The documentation string of the group 
        docStringEdit = QLineEdit('Doc String Here')
        mainLayout.addWidget(docStringEdit, 2, 2, 1, 2)
        
        self.setLayout(mainLayout)

class GSMemberToolBar(QWidget):
    """ Add, edit, and remove buttons in a horizontal 
    layout toolbar. 
    """
    def __init__(self, parent=None):
        # Widget wide settings
        QWidget.__init__(self, parent)
        
        # Creating the main Horizontal Box Layout
        # for the toolbar.
        mainLayout = QHBoxLayout()
        
        # Creating 'Add', 'Edit', and
        # 'Remove Buttons'
        addButton = QPushButton('Add')
        editButton = QPushButton('Edit')
        removeButton = QPushButton('Remove')
        
        # Adding the buttons in the order
        # Add, edit, remove with a left
        # justification.
        mainLayout.addWidget(addButton)
        mainLayout.addWidget(editButton)
        mainLayout.addWidget(removeButton)
        mainLayout.addStretch()
        
        # Setting the layout of this widget
        # layout that contains the properly 
        # formatted buttons.
        self.setLayout(mainLayout)
        

class GSGroupMembersWidget(QWidget):
    """
    """
    def __init__(self, parent=None):
        # Widget wide settings
        QWidget.__init__(self, parent)
        
        # Creating the main layout
        mainLayout = QVBoxLayout()
        
        # The Members that are Groups table
        groupsLabel = QLabel('Member Groups')
        groupsLabel.setAlignment(Qt.AlignHCenter)
        groupsTable = QTableWidget()
        groupsTable.setRowCount(1)
        groupsTable.setHorizontalHeaderLabels(['Name', 'CCSM Name',
                                          'SDF', 'Doc String'])
        groupsToolBar = GSMemberToolBar()
        mainLayout.addWidget(groupsLabel)
        mainLayout.addWidget(groupsTable)
        mainLayout.addWidget(groupsToolBar)
                
        # The members that are Threads table
        threadsLabel = QLabel('Member Threads')
        threadsLabel.setAlignment(Qt.AlignHCenter)
        threadsTable = QTableWidget()
        threadsTable.setRowCount(1)
        threadsTable.setHorizontalHeaderLabels(['Name', 'CCSM Name',
                                          'SDF', 'Doc String'])
        threadsToolBar = GSMemberToolBar()
        mainLayout.addWidget(threadsLabel)
        mainLayout.addWidget(threadsTable)
        mainLayout.addWidget(threadsToolBar)
        
        # Setting the layout of the widget to the layout
        # that contains the formatted tables.
        self.setLayout(mainLayout)
        
        
        
class GSGroupSummaryWidget(QWidget):
    """
    """
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        summaryLayout = QVBoxLayout()
        
        # For editing the name/sdf/ccsm name
        # of the group.
        editForm = GSGroupInfoEditForm()
        
        # 
        membersWidget = GSGroupMembersWidget()
        
        #
        summaryLayout.addWidget(editForm)
        summaryLayout.addWidget(membersWidget)
        
        # 
        self.setLayout(summaryLayout)
        

class GSGroupEditor(QTabWidget):
    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        summaryPage = GSGroupSummaryWidget()
        pmdPage = GSMemberDataWidget()
        pgdPage = GSMemberDataWidget()
        sdfPage = GSSdfSummaryWidget()
        
        self.addTab(summaryPage, 'Summary')
        self.addTab(pmdPage, 'Per Member Data')
        self.addTab(pgdPage, 'Per Group Data')
        self.addTab(sdfPage, 'SDF Information' )
        
class GSWorkspaceWidget(QSplitter):
    """The Workspace widget is the left-hand side of the 
    screen. This shows the open .gsh configuration and the 
    workspace tree views and related widgets.
    """
    DEFAULT_SPLITTER_HEIGHTS = [468, 300]
    
    def __init__(self, parent=None):
        QSplitter.__init__(self, parent)
        self.setOrientation(Qt.Vertical)
        #self.setContentsMargins(4, 4, 4, 4)
        
        #  Hiearchy Tabs just hold one page that 
        #  contains a 
        hierarchyTabs = QTabWidget()
        hierarchyPage = QWidget()
        hierarchyPageLayout = QVBoxLayout()
        
        # Combobox to select an open .gsh configuration
        # that is open to edit, open a saved .gsh config,
        # or create a new .gsh configuration.
        #
        hierarchyComboBox = QComboBox()
        hierarchyComboBox.addItem('No Open Configurations')
        hierarchyComboBox.insertSeparator(1)
        hierarchyComboBox.addItem('Open')
        hierarchyComboBox.addItem('Create New Configuration')
        
        # The tree view for the .gsh configuration.
        #
        hierarchyTreeView = QTreeView()
        hierarchyTreeView.setHeaderHidden(True)
        
        # Adding combobox and tree view to the 
        # widget in order to create the desired effect
        # of the combobox stacked on top of the treeview.
        #
        hierarchyPageLayout.addWidget(hierarchyComboBox)
        hierarchyPageLayout.addWidget(hierarchyTreeView)
        #hierarchyPageLayout.setContentsMargins(4, 4, 4, 4)
        # Adding the layout to the hierarchy widget.
        #
        hierarchyPage.setLayout(hierarchyPageLayout)
        # Adding the created hierachy page to the
        # tabwidget. The tab widget is only used now for the look.
        #
        hierarchyTabs.addTab(hierarchyPage, 'Open Configurations')
        
        # Workspace tabs for cutting/pasting different parts
        # of different configurations.
        #
        workspaceTreeWidget = QTreeWidget() 
        workspaceTreeWidget.setHeaderHidden(True)
        workspaceTabs = QTabWidget()
        workspaceTabs.addTab(workspaceTreeWidget, 'Workspace')
        
        # Adding both widgets to the splitter.
        # 
        self.addWidget(hierarchyTabs)
        self.addWidget(workspaceTabs)
        
        # Setting the sizes so that the openconfigurations tab
        # has noticably more pixles of height than the workspace.
        #
        self.setSizes(self.DEFAULT_SPLITTER_HEIGHTS)
        
class GSArchitectWidget(QSplitter):
    """The GSArchitectWidget sets up the main body of the
    GSArchitectWindow.
    """
    DEFAULT_SPLITTER_WIDTHS = [224,800]
    
    def __init__(self, parent = None):
        QSplitter.__init__(self, parent)

        
        workspaceWidget = GSWorkspaceWidget()
        self.addWidget(workspaceWidget)
        
        # Adds group and thread edit
        # tabs to the right-hand side of the 
        # main body of the ArchitectWidget.
        #
        editTabs = QTabWidget()
        editTabs.setTabsClosable(True)
        # Creates and show a start page. The 
        # start page is pulled from the KUSP 
        # Gsched Architect web page.
        #
        startTab = QWebView()
        startTab.setUrl(QUrl('http://www.ittc.ku.edu/kusp'))
        editTabs.addTab(startTab, 'Architect Start Page') 
        editTabs.addTab(GSGroupEditor(), 'Test Page')
        self.addWidget(editTabs)
       
        #
        #
        self.setSizes(self.DEFAULT_SPLITTER_WIDTHS)

   

class GSArchitectWindow(QMainWindow):
    """Graphical interface to ease creation of 
    Group Scheduling config files."""
    def __init__(self):
        """
        """
        QMainWindow.__init__(self)
        #Window Wide Settings
        self.setWindowTitle('Group Scheduling Architect')
        self.resize(1024,768)
        self.setMinimumSize(640,480)
        self.setCentralWidget(GSArchitectWidget())
        mainWidget = self.centralWidget()
        #mainWidget.setContentsMargins(2, 2, 2, 2)
        
        #Main Menu 
        mainMenu = self.menuBar()
        ##File Menu
        fileMenu = mainMenu.addMenu('&File')
        fileNew = fileMenu.addAction('&New Group Hierarchy')
        fileOpen = fileMenu.addAction('&Open')
        fileMenu.addSeparator()
        fileClose = fileMenu.addAction('Close')
        fileCloseAll = fileMenu.addAction('Close All')
        fileMenu.addSeparator()
        fileSave = fileMenu.addAction('&Save')
        fileSaveAs = fileMenu.addAction('S&ave As')
        fileMenu.addSeparator()
        filePrint = fileMenu.addAction('&Print')
        fileMenu.addSeparator()
        fileExit = fileMenu.addAction('&Exit')
        ##EditMenu
        editMenu = mainMenu.addMenu('&Edit')
        ##Tools Menu
        toolsMenu = mainMenu.addMenu('T&ools')
        toolsSDFLibaray = toolsMenu.addAction('SDF Library')
        toolsDiff = toolsMenu.addAction('Diff Menu')
        ##WindowMenu
        windowMenu = mainMenu.addMenu('Window')
        ##Help Menu
        helpMenu = mainMenu.addMenu('&Help')
        helpCHTML = helpMenu.addAction('Help')
        helpOnline = helpMenu.addAction('Online Help')
        helpInfo = helpMenu.addAction('Information')
        
        #Status Bar for user info, aesthetics
        self.setStatusBar(QStatusBar())
        mainStatusBar = self.statusBar()       
        
   
        #Signals
        self.connect(fileOpen,
                     QtCore.SIGNAL('activated()'),
                     self.showFileDialog)
        self.connect(fileExit,
                     QtCore.SIGNAL('activated()'),
                     self.showCloseDialog)

        
    
    def showFileDialog(self):
        """Opens the load file dialog that allows
        the user to browse for a .gsh file to open.
        """
        fileDialog = QFileDialog(self)
        fileDialog.setDirectory(os.getcwd())
        fileDialog.setWindowTitle('Open Group Scheduling Configuration File')
        
        self.connect(fileDialog, QtCore.SIGNAL('filesSelected(QStringList)'),
                     self.loadConfigFile)
        
        fileDialog.exec_()
        
    def showCloseDialog(self):
        """Opens a dialog asking the user if they 
        actually wish to quit, giving them a second to
        think about it before potentially quitting and losing work.
        """
        closeMessageBox = QMessageBox(self)
        closeMessageBox.setWindowTitle('Exit Groupviewer?')
        closeMessageBox.setText('Are you sure you want to exit?')
        closeMessageBox.show()

    def openSaveDialog(self):
        """Opens a save dialog for an open configuration to be
        saved as a .gsh file.
        """

        fileDialog = QFileDialog(self)
        fileDialog.setDirectory(os.getcwd())
        #
        #self.connect(fileDialog, QtCore.SIGNAL('filesSelected(QStringList)'),
        #             self.saveConfiguration)
        #
        fileDialog.exec_()

    def loadConfigFile(self, fileList):
        filepath = fileList[0]
        # Converting it from a QString into
        # a Python string
        filepath = str(filepath)
        dataManager.loadConfig(filepath)


if __name__ == "__main__": 

    app = QApplication(sys.argv)
    dataManager = GSArchitectDataManager()
    form = GSArchitectWindow()
    form.show()
    sys.exit(app.exec_())      
             
