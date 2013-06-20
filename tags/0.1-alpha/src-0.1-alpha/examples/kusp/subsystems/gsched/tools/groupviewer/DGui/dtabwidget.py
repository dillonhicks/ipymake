#!/usr/bin/env python
""" dtabwidget.py

Author:    Dillon Hicks
Updted: 21.05.2009
Summary: A stand-in custom TabWidget until pyqt 4.5. Allows for 
        tab closing in a forward compatible way.
"""
import sys
import os
from PyQt4.QtGui import *
from PyQt4 import QtCore
from PyQt4.Qt import *               
from dtabbar import *

        
class DTabWidget(QWidget):
    """Custom, Functionally equivalent Version of QTabWidget."""
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(0)
        self.__pageWidget = QStackedWidget()
        tabScrollArea = QScrollArea()
        tabScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tabScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        tabScrollArea.setFrameShape(QFrame.Panel)
        tabScrollArea.setMaximumHeight(40)
        tabScrollArea.setWidgetResizable(True)
        tabScrollArea.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        tabScrollArea.addScrollBarWidget(QScrollBar(), Qt.AlignBottom)
        tabScrollArea.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        
        self.__tabBar = DTabBar()
        tabFrame = QFrame()
        tabLayout = QHBoxLayout()
        tabLayout.addWidget(self.__pageWidget)
        tabFrame.setFrameShape(QFrame.Panel)
        tabFrame.setLayout(tabLayout)
        tabScrollArea.setWidget(self.__tabBar)

        mainLayout.addWidget(tabScrollArea)
        mainLayout.addWidget(tabFrame)
        mainLayout.setContentsMargins( 0, 0, 0, 0)
        self.setLayout(mainLayout)
        self.connect(self.__tabBar, QtCore.SIGNAL('tabSelected'), self.__selectTab)
        self.connect(self.__tabBar, QtCore.SIGNAL('tabCloseRequested'), self.__closeTab)
    
    
    def addTab(self, page, text):
        tabIndex = self.indexOf(page)
        if tabIndex == -1: #Not Found
            self.__pageWidget.addWidget(page)
            self.__tabBar.addTab(text)
        else:
            self.__selectTab(tabIndex)
    
    def setTabText(self, index, text):
        self.__tabBar.setTabText(index, text)
    
    def __selectTab(self, index):
        self.__pageWidget.setCurrentIndex(index)
        self.__tabBar.setCurrentIndex(index)
    
    def __closeTab(self, index):
        page = self.__pageWidget.widget(index)
        self.__pageWidget.removeWidget(page)
        self.__tabBar.removeTab(index)
    
    def indexOf(self, widget):
        return self.__pageWidget.indexOf(widget)