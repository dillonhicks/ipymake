""" gshtoolbar.py
Author:    Dillon Hicks
Updted: 05.06.2009
Summary:  
"""
import os
from PyQt4.QtGui import *
from PyQt4 import QtCore
from PyQt4.Qt import *

ICONS_PATH = os.getcwd()+'/icons/'

class ActionFlags:
    """Determines which actions are added to the GSHToolBar."""
    NONE = 0x0
    MAKE_ROOT = 0x1
    ADD_GROUP = 0x2
    ADD_TASK = 0x4
    COPY = 0x8
    PASTE = 0x10
    REMOVE = 0x20
    CUT = 0x40
    SAVE_SELECTED = 0x80
    SAVE_ALL = 0x100
    SAVE_SELECTED_AS = 0x200
    OPEN_FILE = 0x400
    ADD_PGD = 0x800
    ADD_PMD = 0x1000
    ADD_LIST = ADD_GROUP 
    REMOVE_LIST = REMOVE
    ALL = 0x1fff
    GROUP_ACTIONS = ADD_GROUP | ADD_TASK | COPY | PASTE | REMOVE
    SDF_ACTIONS = 0
    MAIN_ACTIONS = (OPEN_FILE | SAVE_SELECTED | SAVE_ALL | MAKE_ROOT | 
                    ADD_GROUP | ADD_TASK | COPY | PASTE | REMOVE ) 
    LIST_ACTIONS = ADD_LIST | REMOVE_LIST
class GSHToolBar(QWidget):
    """Adaptable and reusable toolbar for manipulating different parts 
    of the GSHs."""
    def __init__(self, actions=ActionFlags.NONE, orient=Qt.Vertical, parent=None):
        QWidget.__init__(self, parent)
        #Widget wide Settings
        scheduleToolBar = QToolBar()
        scheduleToolBar.setOrientation(orient)
        if orient == Qt.Vertical:
            scheduleToolBar.setFixedWidth(32) #32 = Width of Icons
        else:
            scheduleToolBar.setFixedHeight(32)

        #The actions available 
        addTaskAction = QAction(QIcon(ICONS_PATH+'insert-object.png'),
                                       'Add Task', scheduleToolBar)
        addGroupAction = QAction(QIcon(ICONS_PATH+'insert-group.png'),
                                       'Add Group', scheduleToolBar)
        makeRootAction = QAction(QIcon(ICONS_PATH+'rating.png'),
                                       'Make Root', scheduleToolBar)
        copyNodeAction = QAction(QIcon(ICONS_PATH+'edit-copy.png'),
                                       'Copy', scheduleToolBar)
        pasteNodeAction = QAction(QIcon(ICONS_PATH+'edit-paste.png'),
                                       'Paste', scheduleToolBar)
        removeNodeAction = QAction(QIcon(ICONS_PATH+'draw-eraser.png'),
                                       'Remove', scheduleToolBar)
        cutNodeAction = QAction(QIcon(ICONS_PATH+'edit-cut.png'),
                                       'Cut', scheduleToolBar)
        openFileAction = QAction(QIcon(ICONS_PATH+'document-open.png'),
                                       'Open File', scheduleToolBar)
        saveAction = QAction(QIcon(ICONS_PATH+'filesave.png'),
                                       'Save Selected', scheduleToolBar)
        saveAllAction = QAction(QIcon(ICONS_PATH+'filesaveall.png'),
                                       'Save All', scheduleToolBar)
        saveAsAction = QAction(QIcon(ICONS_PATH+'filesaveas.png'),
                                       'Save As', scheduleToolBar)
        addPGDAction = QAction(QIcon(ICONS_PATH+'insert-object.png'),
                                       'Add PGD', scheduleToolBar)
        addPMPAction = QAction(QIcon(ICONS_PATH+'insert-object.png'),
                                       'Add PMD', scheduleToolBar)
    
        #Matching actions against members of ActionFlags. If there
        #is a match, the action is added to the toolbar. 
        if actions & ActionFlags.OPEN_FILE == ActionFlags.OPEN_FILE:
            scheduleToolBar.addAction(openFileAction)
        if actions & ActionFlags.SAVE_SELECTED == ActionFlags.SAVE_SELECTED:
            scheduleToolBar.addAction(saveAction)
        if actions & ActionFlags.SAVE_ALL == ActionFlags.SAVE_ALL:
            scheduleToolBar.addAction(saveAllAction)
        if actions & ActionFlags.SAVE_SELECTED_AS == ActionFlags.SAVE_SELECTED_AS:
            scheduleToolBar.addAction(saveAsAction)
        if actions & ActionFlags.ADD_PGD == ActionFlags.ADD_PGD:
            scheduleToolBar.addAction(addPGDAction)
        if actions & ActionFlags.ADD_PMD == ActionFlags.ADD_PMD:
            scheduleToolBar.addAction(addPMDAction)
        if actions & ActionFlags.MAKE_ROOT == ActionFlags.MAKE_ROOT:
            scheduleToolBar.addAction(makeRootAction)
        if actions & ActionFlags.ADD_GROUP == ActionFlags.ADD_GROUP:
            scheduleToolBar.addAction(addGroupAction)
        if actions & ActionFlags.ADD_TASK == ActionFlags.ADD_TASK:
            scheduleToolBar.addAction(addTaskAction)
        if actions & ActionFlags.COPY == ActionFlags.COPY:
            scheduleToolBar.addAction(copyNodeAction)
        if actions & ActionFlags.CUT == ActionFlags.CUT:
            scheduleToolBar.addAction(cutNodeAction)
        if actions & ActionFlags.PASTE == ActionFlags.PASTE:
            scheduleToolBar.addAction(pasteNodeAction)
        if actions & ActionFlags.REMOVE == ActionFlags.REMOVE:
            scheduleToolBar.addAction(removeNodeAction)
        
        #Creating custom name appropriate signals to encapsulate 
        #the actions.
        emitMakeRoot = lambda: self.emit(QtCore.SIGNAL('makeRoot'))
        emitAddGroup = lambda: self.emit(QtCore.SIGNAL('addGroup'))
        emitAddTask = lambda: self.emit(QtCore.SIGNAL('addTask'))
        emitCopy = lambda: self.emit(QtCore.SIGNAL('copy'))
        emitCut = lambda: self.emit(QtCore.SIGNAL('cut'))
        emitPaste = lambda: self.emit(QtCore.SIGNAL('paste'))
        emitRemove = lambda: self.emit(QtCore.SIGNAL('remove'))
        emitOpenFile = lambda: self.emit(QtCore.SIGNAL('openFile'))
        emitSave = lambda: self.emit(QtCore.SIGNAL('save'))
        emitSaveAll = lambda: self.emit(QtCore.SIGNAL('saveAll'))
        emitSaveAs = lambda: self.emit(QtCore.SIGNAL('saveAs'))
        emitAddPGD = lambda: self.emit(QtCore.SIGNAL('addPGD'))
        emitAddPMD = lambda: self.emit(QtCore.SIGNAL('addPMD'))
        #Signals
        self.connect(makeRootAction, QtCore.SIGNAL('activated()'), 
                     emitMakeRoot)
        self.connect(addGroupAction, QtCore.SIGNAL('activated()'),
                     emitAddGroup)
        self.connect(addTaskAction, QtCore.SIGNAL('activated()'),
                     emitAddTask)
        self.connect(copyNodeAction, QtCore.SIGNAL('activated()'),
                     emitCopy)
        self.connect(cutNodeAction, QtCore.SIGNAL('activated()'),
                     emitCut)
        self.connect(pasteNodeAction, QtCore.SIGNAL('activated()'),
                     emitPaste)
        self.connect(removeNodeAction, QtCore.SIGNAL('activated()'),
                     emitRemove)
        self.connect(saveAction, QtCore.SIGNAL('activated()'),
                     emitSave)
        self.connect(saveAllAction, QtCore.SIGNAL('activated()'),
                     emitSaveAll)
        self.connect(saveAsAction, QtCore.SIGNAL('activated()'),
                     emitSaveAs)
        self.connect(saveAction, QtCore.SIGNAL('activated()'),
                     emitAddPGD)
        self.connect(saveAction, QtCore.SIGNAL('activated()'),
                     emitAddPMD)    
        self.connect(openFileAction, QtCore.SIGNAL('activated()'),
                     emitOpenFile)    
        #Layout settings
        layout = QHBoxLayout()
        layout.addWidget(scheduleToolBar)
        self.setLayout(layout)