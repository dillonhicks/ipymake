#!/usr/bin/env python
""" dtab.py

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

ICONS_PATH = os.getcwd()+'/icons/'
"""Pads for left justification of text in buttons."""
PAD_TEXT = lambda text : text+(' '*3)

class DTab(QWidget):
    """A closable base tab.
    
    DTab is two stacked push buttons which allow for a custom tab
    that emits a 'tabSelected' signal for the main body of the tab being selected
    and a 'tabCloseRequested' signal for the close button on the right side of the tab.
    
    NOTE: This is to provide forward compatibility with Qt4.5 QTabWidget when it 
    becomes available for PyQt.
    """
    def __init__(self, text='', icon=None, parent=None):
        #Widget Wide Properties/Settings
        QWidget.__init__(self, parent)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        mainLayout = QGridLayout()
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)
        
        #Widget Components#
        ##Main Tab Button
        self.text = PAD_TEXT(text)
        self.tabButton = QPushButton(self.text)
        self.tabButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        ###Ghost Button provides the grayed out appearance.
        self.__ghostButton = QPushButton(self.tabButton.text())
        self.__ghostButton.setEnabled(False)
        ##Tab Close Button With X Icon
        closePixmap = QPixmap(ICONS_PATH+'close.png').scaled(20,16)
        self.tabCloseButton = QPushButton(QIcon(closePixmap),'')
        self.tabCloseButton.setFixedSize(closePixmap.size())
        self.tabCloseButton.setFlat(True)
        
        #Layout Settings
        mainLayout.addWidget(self.__ghostButton, 0, 0, 1, 3)
        mainLayout.addWidget(self.tabButton, 0, 0, 1, 3)
        mainLayout.addWidget(self.tabCloseButton, 0, 2, 1, 1)
        

        
        #SIGNALS#
        self.emitCloseSignal = lambda: self.emit(QtCore.SIGNAL('tabCloseRequested'), self)
        self.emitTabSelected = lambda: self.emit(QtCore.SIGNAL('tabSelected'), self)
        self.connect(self.tabCloseButton, QtCore.SIGNAL('clicked()'), self.emitCloseSignal)
        self.connect(self.tabButton, QtCore.SIGNAL('clicked()'), self.emitTabSelected)
        
        #Layout Application#
        self.setLayout(mainLayout)

    def setText(self, text): 
        self.text = PAD_TEXT(text)
        self.tabButton.setText(self.text)
        self.__ghostButton.setText(self.text)
    
    def setFocus(self, focus):
        """If not focus, applies a grayed appearance, else restores to normal appearance."""
        if focus:
            self.tabButton.setFlat(False)
            self.tabButton.setText(self.text)
            self.tabCloseButton.show()
        else:
            self.tabButton.setText('')
            self.tabButton.setFlat(True)
            self.tabCloseButton.hide()