#!/usr/bin/env python
""" dtabbar.py

Author:    Dillon Hicks
Email:    hhicks[at]ittc[dot]ku[dot]edu
Updted: 21.05.2009
Summary: 
"""

import sys
import os
import types
import copy
from PyQt4.QtGui import *
from PyQt4 import QtCore
from PyQt4.Qt import *
from dtab import *

class DTabBar(QWidget):
    """A Tab bar made for DTabs."""
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setLayout(QHBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.tabLayout = QHBoxLayout()
        self.layout().addLayout(self.tabLayout)
        self.layout().insertStretch(1, 1)
        self.__tabs = []
        self.__currentTab = -1
         
    
    def setTabText(self, index, text):
        if index < len(self.__tabs) and index > -1:
            tab = self.__tabs[index]
            tab.setText(text)
        
    def addTab(self, text):
        """Adds a DTab to the end of the DTabBar."""
        newTab = DTab(text)
        self.tabLayout.addWidget(newTab)
        self.__tabs.append(newTab)
        self.__currentTab = len(self.__tabs) - 1
        self.connect(newTab, QtCore.SIGNAL('tabCloseRequested'), self.__processCloseRequest)
        self.connect(newTab, QtCore.SIGNAL('tabSelected'), self.__selectNewTab)
        self.__tabs[self.__currentTab].emitTabSelected()
                
        
    def insertTab(self, index, text):
        """Inserts a DTab before index in the DTabBar."""
        newTab = DTab(text)
        self.tabLayout.insertWidget(index, newTab)
        self.__tabs.insert(index, newTab)
        self.connect(newTab, QtCore.SIGNAL('tabCloseRequested'), self.__processCloseRequest)
        self.connect(newTab, QtCore.SIGNAL('tabSelected'), self.__selectNewTab)
        
        
    def removeTab(self, index):
        """Removes the tab at index."""
        tab = self.__tabs.pop(index)
        self.layout().removeWidget(tab)
        tab.setParent(None)
        
        nextIndex = index
        numberTabs = len(self.__tabs)
        if numberTabs is 0:
            return None
        while nextIndex >= numberTabs:
            nextIndex -= 1
        
        if not nextIndex == -1:
            self.__tabs[nextIndex].emitTabSelected()
    
    def setCurrentIndex(self, index):
        if index < len(self.__tabs):
            tab = self.__tabs[index]
            if isinstance(tab, DTab):
                self.__selectNewTab(tab, False)
    #### Private Methods ####
    
    def __processCloseRequest(self, tab):
        """Catches the tabCloseRequested signal from child tab and emits 
        new tabCloseRequested with index of the tab in the DTabBar."""
        tabIndex = self.__tabs.index(tab)
        self.emit(QtCore.SIGNAL('tabCloseRequested'), tabIndex)
    
    def __selectNewTab(self, tab, emitSignal=True):
        """Catches the tabSelected signal from child tab and emits 
        new tabSelected with index of the tab in the DTabBar.
        """        
        tabIndex = self.__tabs.index(tab)
        for x in range(0, len(self.__tabs)):
            selectedTab = self.__tabs[x]
            newFocus = True if x is tabIndex else False
            selectedTab.setFocus(newFocus)
        if emitSignal is True:
            self.emit(QtCore.SIGNAL('tabSelected'), tabIndex)