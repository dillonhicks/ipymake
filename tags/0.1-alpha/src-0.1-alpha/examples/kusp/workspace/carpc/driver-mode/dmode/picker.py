from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qc
from sound import Button

class File(qt.QTreeWidgetItem):
    """
    A file item. It cannot be expanded.
    """
    def __init__(self, parent, info):
        qt.QTreeWidgetItem.__init__(self, parent, [info.baseName()])

        self.setChildIndicatorPolicy(qt.QTreeWidgetItem.DontShowIndicator)

        self.info = info

    def childCount(self):
        return 0

    def setExpanded(self):
        return

    def selection(self):
        return self.info

class Directory(qt.QTreeWidgetItem):
    """
    A directory item. It can be expanded.
    Children are not created until after it is expanded.
    """
    def __init__(self, parent, loc, name = None):
        if name:
            qt.QTreeWidgetItem.__init__(self, parent, [name])
        else:
            qt.QTreeWidgetItem.__init__(self, parent, [loc.dirName()])

        self.setForeground(0, qt.QBrush(qc.Qt.blue))

        self.loc = loc
        
        self.children = None

        # No, DontShowIndicatorUnlessChildren doesn't work with this setup.
        if self.childCount() > 0:
            self.setChildIndicatorPolicy(qt.QTreeWidgetItem.ShowIndicator)
        else:
            self.setChildIndicatorPolicy(qt.QTreeWidgetItem.DontShowIndicator)
        
    def selection(self):
        return qc.QFileInfo(self.loc.path())

    def __add_children(self):
        """
        Create a list containing the children.
        """
        if self.children:
            return

        self.children = [self.create_child(x) for x in self.loc.entryInfoList()]
        self.addChildren(self.children)

    def childCount(self):
        return self.loc.count()

    def child(self, index):
        self.__add_children()
        return qt.QTreeWidgetItem.child(self, index)                

    def setExpanded(self, expanded):
        if expanded:
            self.__add_children()
            qt.QTreeWidgetItem.setExpanded(self, expanded)        
        
    def sortChildren(self):
        self.__add_children()
        qt.QTreeWidgetItem.sortChildren(self)        

    def create_child(self, info):
        if info.isDir():
            new_dir = qc.QDir(info.filePath())
            new_dir.setNameFilters(self.loc.nameFilters())
            new_dir.setFilter(self.loc.filter())
            return Directory(self, new_dir)
        else:
            return File(self, info)

class Picker(qt.QTreeWidget):
    """
    A simplified selection widget.
    """

    def __init__(self, loc, fltr = [], parent = None):
        """
        Initialize directory entries and auto select the first item if there is one.
        """
        qt.QTreeWidget.__init__(self, parent)

#        self.setFocusPolicy(qc.Qt.StrongFocus)

        self.setSortingEnabled(False)

        first = None

        for name, path in loc.iteritems():
            qdir = qc.QDir(path)

            if not qdir.exists():
                raise RuntimeError("No such directory %s." % value)

            qdir.setFilter(qc.QDir.AllDirs | qc.QDir.Files | qc.QDir.NoDotAndDotDot | qc.QDir.NoSymLinks)
            qdir.setNameFilters(fltr)

            item = Directory(self, qdir, name)

            self.addTopLevelItem(item)

            if not first:
                first = item

        if first:
            self.setCurrentItem(first)
            self.setItemSelected(first, True)

        self.itemExpanded.connect(self.expandItem)

    def expandItem(self, item):
        item.setExpanded(True)

    def selection(self):        
        return [x.selection() for x in self.selectedItems()]
"""
    def keyPressEvent(self, event):
        print "tree widget"
        print event

        qt.QTreeWidget.keyPressEvent(self, event)
"""

class FilePicker(qt.QWidget):
    """
    A picker that is specialized to select a single file.
    """
    def __init__(self, label, loc, fltr = [], parent = None):
        qt.QWidget.__init__(self, parent)

#        self.setFocusPolicy(qc.Qt.StrongFocus)

        box = qt.QVBoxLayout()

        self.picker = Picker(loc, fltr, self)
        self.picker.setHeaderLabel(label)

        box.addWidget(self.picker)

        select = qt.QHBoxLayout()

        self.cancel = qt.QPushButton("Cancel", self)
        select.addWidget(self.cancel)
        self.ok = qt.QPushButton("OK", self)
        select.addWidget(self.ok)

        box.addLayout(select)

        self.setLayout(box)

        self.picker.itemSelectionChanged.connect(self.__check_file)

        self.__check_file()
        self.setFocusProxy(self.picker)

        qt.QShortcut(qt.QKeySequence(qc.Qt.Key_Enter), self.picker, self.ok.click)

#        qt.QShortcut(qt.QKeySequence(qc.Qt.Key_0), self.picker, self.cancel.click)

        # Oddly with numlock off, key_0 on the numeric pad comes out as key_insert
        qt.QShortcut(qt.QKeySequence(qc.Qt.Key_Insert), self.picker, self.cancel.click)


    def __check_file(self):
        self.ok.setDisabled(not self.selection())

    def selection(self):      
        if len(self.picker.selection()) > 0 and self.picker.selection()[0].isFile():
            return self.picker.selection()[0]
        else:
            return None
