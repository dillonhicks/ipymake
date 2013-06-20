#!/usr/bin/env python
""" groupviewer.py
    
(Eventual) Graphical front end to pygroupmaker.

Author:    Dillon Hicks    
Updated: 23.06.2009
Summary: groupviewer is to be used to read and write configuration files
        for the command line tool groupmaker. It does this by allowing the 
        user to construct group-scheduling configuration trees in hierarchical
        view that simplifies creation and editing by allowing the user to 
        manage complexity in a tree form. 
        
TASK LIST:
    - Read/Write Configs
    - Spice up gui (drag and drop, multiple configs, etc)

"""
import sys
import os
import types
import copy
from PyQt4.QtGui import *
from PyQt4 import QtCore
from PyQt4.Qt import *
from PyQt4.QtWebKit import *
from DGui import *
from schedulingstructures import *
try:
    from pykusp import configfile
except Exception, err:
    print err

__version__ = '1.0.0'
ICONS_PATH = os.getcwd()+'/icons/'
NAME, TYPE, VALUE = range(3)
GSH_OBJECT, MEMBERS = range(2)
TREE_INDENTATION = 10

class GroupViewer(QSplitter):
    DEFAULT_SIZE = [250,600]
    openConfigurations = []
    workspace = []
    MAX_INVALID_ATTEMPTS = 3
    def __init__(self, parent = None):
        QSplitter.__init__(self, parent)
        #Widget Wide Settings
        self.setChildrenCollapsible(False)
        self.clipboard = DClipBoard()
        self.__invalidAddCount = 0
        self.__workGroupIsClicked = False

        #Schedule Widget Treeviews (TreeView + ToolBar).
        scheduleWidget = QWidget()
        dualTreeLayout = QVBoxLayout()
        dualTreeLayout.setSpacing(2)
        scheduleLayout = QHBoxLayout()
        scheduleLayout.setSpacing(0)
        scheduleWidget.setLayout(scheduleLayout)
        
        ##Work Group Schedule Tree. 
        self.scheduleTree = QTreeWidget()
        scheduleTree = self.scheduleTree
        scheduleTree.setIndentation(TREE_INDENTATION)
        scheduleTree.setHeaderLabels(['Open Config Files'])
        dualTreeLayout.addWidget(scheduleTree)
        
        ##Unattached Group Schedule Tree
        self.unattachedTree = QTreeWidget()
        self.unattachedTree.setIndentation(TREE_INDENTATION)
        self.unattachedTree.setHeaderLabels(['Workspace'])

        dualTreeLayout.addWidget(self.unattachedTree)
        scheduleLayout.addLayout(dualTreeLayout)
        
        ##Tree Operation tool bar for tree view.
        scheduleToolBar = GSHToolBar(ActionFlags.MAIN_ACTIONS)
        scheduleLayout.insertWidget(0, scheduleToolBar)
        
        #Editor Widget (Internet Browser Inspired)
        groupEditWidget = QWidget()
        groupEditLayout = QVBoxLayout()
        groupEditWidget.setLayout(groupEditLayout)
        
        ##Browser TabWidget
        browserTabBar = DTabWidget()
        startHTMLView = QWebView()
        startHTMLView.setUrl(QUrl('https://wiki.ittc.ku.edu/kusp2_wiki/index.php/GroupViewer'))
        browserTabBar.addTab(startHTMLView,'Start')
        groupEditLayout.addWidget(browserTabBar)
        self.browserTabWidget = browserTabBar
        
        #Signals
        self.connect(scheduleToolBar,
                     QtCore.SIGNAL('addGroup'), self.addGroup)
        self.connect(scheduleToolBar,
                     QtCore.SIGNAL('addTask'), self.addThread)
        self.connect(scheduleToolBar,
                     QtCore.SIGNAL('copy'), self.copyNode)
        self.connect(scheduleToolBar,
                     QtCore.SIGNAL('cut'), self.cutNode)
        self.connect(scheduleToolBar,
                     QtCore.SIGNAL('makeRoot'), self.makeNodeRoot)
        self.connect(scheduleToolBar,
                     QtCore.SIGNAL('paste'), self.pasteNode)
        self.connect(scheduleToolBar,
                     QtCore.SIGNAL('remove'), self.removeNode)
        self.connect(scheduleToolBar,
                     QtCore.SIGNAL('save'), self.openSaveDialog)
        self.connect(self.scheduleTree, 
                     QtCore.SIGNAL('itemDoubleClicked(QTreeWidgetItem*,int)'),
                      self.openGroupTab)
        self.connect(scheduleToolBar,
                     QtCore.SIGNAL('openFile'),
                     self.showFileDialog)
        self.connect(self.unattachedTree, 
                     QtCore.SIGNAL('itemDoubleClicked(QTreeWidgetItem*,int)'),
                      self.openGroupTab)      
        self.connect(self.scheduleTree, 
                     QtCore.SIGNAL('itemClicked(QTreeWidgetItem*,int)'),
                      self.__setClickedToWorkGroup)
        self.connect(self.unattachedTree, 
                     QtCore.SIGNAL('itemClicked(QTreeWidgetItem*,int)'),
                      self.__setClickedToUnattachedGroup)              

        
        #Adding tree view to main window.
        self.addWidget(scheduleWidget) #Index 0
        self.addWidget(groupEditWidget) 
        self.setSizes(self.DEFAULT_SIZE)

    def __setClickedToWorkGroup(self):
        """Sets the config-view tree to the last clicked TreeView.
        
        This keeps track of which Tree (config-view/workspace) 
        is clicked to know which tree to add a new member (group/task).
        """
        self.__workGroupIsClicked = True
        self.unattachedTree.setCurrentItem(None)
    
    def __setClickedToUnattachedGroup(self):
        self.__workGroupIsClicked = False
        self.scheduleTree.setCurrentItem(None)
    
    def getSelectedItem(self, useTopLevel=False):
        currentItem = None
        if self.__workGroupIsClicked:
            currentItem = self.scheduleTree.currentItem()
        else:
            currentItem = self.unattachedTree.currentItem()

        if currentItem is None and useTopLevel:
            if self.__workGroupIsClicked:
                currentItem = self.scheduleTree.topLevelItem(0)
            else:
                currentItem = self.unattachedTree.topLevelItem(0)
        
        return currentItem
    
    def addGroup(self):
        """Inserts a new empty group to the Group Scheduling Hierarchy."""
        #add new object to data structure
        currentItem = None
        newGroup = None
        newCount =  0
        
        if self.__workGroupIsClicked:
            currentItem = self.scheduleTree.currentItem()
            newCount = len(self.openConfigurations)
        else:
            currentItem = self.unattachedTree.currentItem()
            newCount = len(self.workspace)
            
        if currentItem is None:
            groupName =  '<New Group>-%i'%newCount
        else:
            coord = currentItem.getCoordString()
            newCount = currentItem.childCount()
            groupName = '<New Group>-%s-%i'%(coord, newCount)
            
        newGroup = GSHGroup(groupName)
        self.connect(newGroup,
                     QtCore.SIGNAL('nameChanged'),
                     self.__updateTabName)
        
        try:
            if not currentItem is None:
                currentItem.getGSHParent().addMember(newGroup)
            else:
                if self.__workGroupIsClicked:
                    self.scheduleTree.addTopLevelItem(newGroup.asLongItem())
                    self.openConfigurations.append(newGroup)
                else:
                    self.unattachedTree.addTopLevelItem(newGroup.asLongItem())
                    self.workspace.append(newGroup)
                    
        except TypeError, e:
            self.__invalidAddCount += 1
            print e
        finally:
            if self.__invalidAddCount >= self.MAX_INVALID_ATTEMPTS:
                self.__invalidAddCount = 0
                messageBox = QMessageBox()
                messageBox.setStandardButtons(QMessageBox.Ok )
                messageBox.setText('Sorry, cannot add a group to a task.')
                messageBox.setDetailedText('It would be highly illogical.')
                messageBox.exec_()

  
  
    def addThread(self):
        """Inserts a new empty group to the Group Scheduling Hierarchy."""
        #add new object to data structure
          #add new object to data structure
        currentItem = None
        if self.__workGroupIsClicked:
            currentItem = self.scheduleTree.currentItem()
        else:
            currentItem = self.unattachedTree.currentItem()
        newGroup = None
        if currentItem is None:
            currentItem = self.unattachedTree.topLevelItem(0)
        #copyNumber = currentItem.childCount(
        taskName = '%s'%('<New Thread>')
        newTask = GSHThread(taskName)

        if not currentItem is None:
            currentItem.getGSHParent().addMember(newTask)
        else:
            if self.__workGroupIsClicked:
                self.scheduleTree.addTopLevelItem(newTask.asShortItem())
                self.openConfigurations.append(newTask)
            else:
                self.unattachedTree.addTopLevelItem(newTask.asShortItem())
                self.workspace.append(newTask)

    
    def copyNode(self):
        """Recursively copies the node and all of its children to the clipboard. 
        
        Deepcopy.
        """
        currentItem = None
        if self.__workGroupIsClicked:
            currentItem = self.scheduleTree.currentItem()
        else:
            currentItem = self.unattachedTree.currentItem()
        self.clipboard.makeCopy(currentItem)
        pass
    
    def cutNode(self):
        pass
    
    def makeNodeRoot(self):
        pass
    
    def pasteNode(self):
        pasteItem = self.clipboard.getCopy()
        if pasteItem is None:
            return
        currentItem = None
        if self.__workGroupIsClicked:
            currentItem = self.scheduleTree.currentItem()
        else:
            currentItem = self.unattachedTree.currentItem()
        pasteName = pasteItem.getName()
        currentItem[pasteName] = pasteItem
    
    def removeNode(self):
        currentItem = self.getSelectedItem()
        print currentItem
        if currentItem is None:
            return None
        member = currentItem.getGSHParent()
        if member in self.openConfigurations:
            index = self.openConfigurations.index(member)
            parent = currentItem.parent()
            parent = None
            del self.openConfigurations[index]
            
        elif member in self.workspace:
            index = self.workspace.index(member)
            currentItem.GSHParent = None
            del self.workspace[index]

    def showFileDialog(self):
        fileDialog = QFileDialog(self)
        fileDialog.setDirectory(os.getcwd())
        fileDialog.setWindowTitle('Open Group Scheduling Configuration File')
        self.connect(fileDialog, QtCore.SIGNAL('filesSelected(QStringList)'),
                     self.loadConfigFiles)
        fileDialog.exec_()
        
    def loadConfigFiles(self, filepaths):
        for filepath in filepaths:
            self.loadConfigurationFile(filepath)     
    
    def openGroupTab(self, item, column):
        if not isinstance(item.getGSHParent(), GSHThread):
            group = item.getGSHParent()
            groupPage = group.getEditorWidget()
            
            #groupPage.loadData(group)
            self.browserTabWidget.addTab(groupPage, group.getName())
        else:
            thread = item.getGSHParent()
            threadPage = ThreadPageWidget(thread)

            #skPage.loadData(task)
            self.browserTabWidget.addTab(threadPage, thread.getName())
            
    def loadConfigurationFile(self, filepath):
        tags = ParsingTags
        config = {}
        rootName = ''
        loadedThreads = {}
        loadedGroups = {}
        configMembers = []
        
        try:
            config = configfile.parse_config(str(filepath), None)
        except Exception, err:
            messageBox = QMessageBox()
            messageBox.setStandardButtons(QMessageBox.Ok )
            messageBox.setText('Cannot open file for parsing.')
            messageBox.setDetailedText(str(err))
            messageBox.exec_()
        
        
        if config.has_key(tags.MEMBERS):
            configMembers = config[ tags.MEMBERS ]
        
        if config.has_key(tags.THREADS):
            configThreads = config[ tags.THREADS ]
            print configThreads
            for threadName in configThreads.keys():
                newThread = None
                print configMembers
                for mbr in configMembers.values():
                    if mbr[ tags.CCSM_NAME ] == threadName:
                        loadedThreads[threadName] = mbr
                        break
                if newThread is None:
                    print 'Could not find Thread with CCSM Name: <%s>'%threadName
                    
        if config.has_key( tags.GROUPS ):
            configGroups = config[ tags.GROUPS ]
            for gName in configGroups:
                groupData = configGroups[gName]
                gSDF = groupData[ tags.SDF ] if groupData.has_key( tags.SDF ) else None
                if not gSDF is None:
                    gSDF = SCHEDULING_FUNCTIONS_BY_KERNEL_NAME[gSDF]
                gDoc = groupData[ tags.COMMENT ] if groupData.has_key( tags.COMMENT ) else ''
                gMembers = groupData[ tags.MEMBERS ] if groupData.has_key( tags.MEMBERS ) else []
                group = GSHGroup(gName, gSDF)
                group.setDocString(gDoc)
                loadedGroups[gName] = (group, gMembers)
        
        #Determining Root
        if config.has_key( tags.GSH_INSTALLATION ):
            gshData = config[ tags.GSH_INSTALLATION ]
            if gshData.has_key( tags.ROOT ):
                rootName = gshData[ tags.ROOT ]
            #Not worrying about attachment point, yet
        
        if not rootName is None:
            rootNode = loadedGroups[rootName] \
                    if loadedGroups.has_key(rootName) else None
            if rootNode is None:
                print 'Could Not Find Root In Defined Groups'
                return None
            else:
                root = self.__createHierarchyR(rootNode, loadedGroups, loadedThreads)
                root.setRoot(True)
                self.openConfigurations.append(root)
                self.scheduleTree.addTopLevelItem(root.asLongItem())

    def __createHierarchyR(self, node, groups, tasks):
        root = node[GSH_OBJECT]
        members = node[MEMBERS]
        for member in members:
            if member in groups.keys():
                memberNode = groups[member]
                group = self.__createHierarchyR(memberNode, groups, tasks)
                root.addMember(group)
            elif member in tasks.keys():
                memberNode = tasks[member]
                task = GSHThread(member)
                root.addMember(task)
            else:
                print 'Member Not Found'
        return root
    
    def openSaveDialog(self):
        currentItem = None
        if self.__workGroupIsClicked:
            currentItem = self.scheduleTree.currentItem()
        else:
            currentItem = self.unattachedTree.currentItem()
        if currentItem is None:
            return None
        fileDialog = QFileDialog(self)
        fileDialog.setDirectory(os.getcwd())
        self.connect(fileDialog, QtCore.SIGNAL('filesSelected(QStringList)'),
                     self.saveConfiguration)
        fileDialog.exec_()
        
    def saveConfiguration(self, filepaths):
        savePath = ''
        currentItem = None
        
        if len(filepaths) > 0:
            savePath = filepaths[0]
        else:
            return None

        if self.__workGroupIsClicked:
            currentItem = self.scheduleTree.currentItem()
        else:
            currentItem = self.unattachedTree.currentItem()
        if currentItem is None:
            return None
        gshObject = currentItem.getGSHParent()
        try:
            saveFile = open(savePath, 'w')
            configDict = gshObject.toConfigString(True)
            configString = configfile.to_string(configDict)
            saveFile.write(configString)
            saveFile.close()
        except Exception, err:
            messageBox = QMessageBox()
            messageBox.setStandardButtons(QMessageBox.Ok )
            messageBox.setText('Cannot save file.')
            messageBox.setDetailedText(str(err))
            messageBox.exec_()
        
    def __updateTabName(self, group):
        newName = '%s %s'%(group.prefix, group.getName())
        groupWidget = group.getEditorWidget()
        tabIndex = self.browserTabWidget.indexOf(groupWidget)
        self.browserTabWidget.setTabText(tabIndex, newName)
        
class GroupViewerWindow(QMainWindow):
    """Graphical interface to ease creation of Group Scheduling config files."""
    def __init__(self):
        QMainWindow.__init__(self)
        #Window Wide Settings
        self.setWindowTitle('Group Viewer')
        self.resize(850,620)
        self.setMinimumSize(640,480)
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowIcon(QIcon(ICONS_PATH+'groupviewer.png'))
        self.setCentralWidget(QStackedWidget())
        mainWidget = self.centralWidget()
        mainWidget.setContentsMargins(0, 0, 0, 0)
        
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
        
        #Tool Bar below the main menu.
        #Allows for navigation and manipulation
        #of the group schedules
        searchBar = self.addToolBar('Search Tool Bar')
        searchBar.hide()
        
        prevSiblingAction = QAction(QIcon(ICONS_PATH+'go-previous-view.png'),
                                       'Previous Sibling Node', searchBar)
        nextSiblingAction = QAction(QIcon(ICONS_PATH+'go-next-view.png'),
                                       'Next Sibling Node', searchBar)
        downToChildAction = QAction(QIcon(ICONS_PATH+'go-down.png'),
                                       'Go To Child Node', searchBar)
        upToParentAction = QAction(QIcon(ICONS_PATH+'go-up.png'),
                                       'Go To Parent Node', searchBar)
        searchBar.addAction(prevSiblingAction)
        searchBar.addAction(downToChildAction)
        searchBar.addAction(upToParentAction)
        searchBar.addAction(nextSiblingAction)
        searchBar.addSeparator()
        searchEdit = QLineEdit()
        searchBar.addWidget(searchEdit)
        searchBar.addAction('Find')
        filterComboBox = QComboBox()
        filterComboBox.addItem('Filter By')
        searchBar.addWidget(filterComboBox)
        
        #Status Bar for user info, aesthetics
        self.setStatusBar(QStatusBar())
        mainStatusBar = self.statusBar()       
        mainStatusBar.hide()

        self.groupViewer = GroupViewer()        
        #Signals
        self.connect(fileOpen,
                     QtCore.SIGNAL('activated()'),
                     self.groupViewer.showFileDialog)
        self.connect(fileExit,
                     QtCore.SIGNAL('activated()'),
                     self.showPromptCloseDialog)
        
        #Adding a default blank start Group View

        mainWidget.addWidget(self.groupViewer)
        
    
        
    def showPromptCloseDialog(self):
        closeMessageBox = QMessageBox(self)
        closeMessageBox.setWindowTitle('Exit Groupviewer?')
        closeMessageBox.setText('Are you sure you want to exit?')
        closeMessageBox.show()


if __name__ == "__main__": 

    app = QApplication(sys.argv)
    form = GroupViewerWindow()
    form.show()
    sys.exit(app.exec_())      
             
