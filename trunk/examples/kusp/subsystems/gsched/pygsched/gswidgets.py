"""
========================================================
:mod:`gswidgets` -- PyQt Widgets for Group Scheduling
========================================================

:synopsis: A library of widget that can be used in union with other modules 
        in `pygsched` to more easily view and edit Group Scheduling data.

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>

"""
from pykusp import configutility
from pygsched.gsstructures import *
from PyQt4.QtGui import *
from PyQt4 import QtCore
from PyQt4.Qt import *


class GSGroupItem(GSGroup):
    """
   
    A Group Scheduling Group Tree Item.

    Provides a way of wrapping a `GSGroup` object so as to make
    it more friendly with PyQt's MVC architecture.
    
    """
    
    def __init__(self, name='<New Group>', sdf=None, parent=None,
                   ccsmName='', doc=''):
        GSGroup.__init__(self, name, sdf, parent,
                   ccsmName, doc)

        self.useTag = True
        self.tag = '(G)'
    
    def appendChild(self, child):
        """
         
        Adds a child member to the list of members for this Group.
        
        :param child: Group or Thread to add to this Group. 
        :type child: `GSThreadItem` or `GSGroupItem` 
        """
        if isinstance(child, GSGroupItem):
            self.add_group(child)
        if isinstance(child, GSThreadItem):
            self.add_thread(child)
        
        
    def child(self, row):
        """
        
        Gets the refernce to the child member at row.

        :param row: The row of the child to get. 
        :type row: integer 
        :returns: The child at row in the members list.
        :rtype: GSGroupItem or GSThreadItem
        """
        return self.members[row]
    
    def childCount(self):
        """
        :rtype: integer
        :returns: The number of children (members) that the GSGroupItem has.
        """
        return len(self.members)
    
    def columnCount(self):
        """ 
        :rtype: integer
        :returns: The number of data columns (fields).
        """
        return len(self.fields)
    
    def data(self, column):
        """
        
        Gets the field data at column.
        
        :param column: The column from which to get the data.
        :type column: integer
        :rtype: string or None
        :returns: The data from column in the fields data.
        """
        
        return self.fields()[column]
    
    def row(self):
        """
        .. method:: GSGroupItem.row()
        """
        
        if self.parent:
            return parent.members.index(self)
        return 0
    
    def rowOfChild(self, child):
        """
        .. method:: GSGroupItem.rowOfChild()
        """
        
        row = 0
        try:
            row = self.members.index(child)
        except(ValueError, eargs):
            row = -1
        return row
        
    def parent(self):
        """
        :returns: The parent of the GSGroupItem
        :rtype: GSGroupItem or None
        """
        return self.parent       
    
    def fields(self):
        """
        :returns: Data fields for the `GSThreadItem`.
        :rtype: tuple
        """
        if self.useTag:
            return (self.tag+' ' +self.get_name(), self.get_SDF(), None)
        return (self.get_name(), self.get_SDF(), None)
    
    
class GSThreadItem(GSThread):
    """
    A Group Scheduling Thread Tree Item
    
    Provides a way of wrapping a GSThread object to make it more
    friendly with PyQt's MVC architecture.
    """    
    def __init__(self,name, ccsmName='', parent=None, doc=''):
        """
        
        """

        GSThread.__init__(self,name, ccsmName, parent, doc)

        self.useTag = True
        self.tag = '(T)'
    

    def columnCount(self):
        """
        
        """
        return len(self.fields)
    
    def data(self, column):
        """
        
        """

        return self.fields()[column]
    
    def row(self):
        """
        
        """

        if self.parent:
            return parent.members.index(self)
        return 0
    
    def parent(self):
        """
        """

        return self.parent    
    

    def fields(self):
        """
        """
        if self.useTag:
            return (self.tag+' ' +self.get_name(), None, None)
        return (self.get_name(), None, None)
         
        
    
class GSHierarchyModel(QAbstractItemModel):
    """

    An Group Scheduling Hierarchy Model for use with PyQt views.

    Very similar to the GSHierarchy object in the sense that it mimics
    structure of Group Scheduling Hierarchies. It is different in the
    way that it is a QAbstractItemModel so as to interface properly
    with a QTreeView. 
    """
    
    def __init__(self, parent=None):
        """
           
        """
        super(GSHierarchyModel, self).__init__()
        self.rootGroup = None;
        self.headers = []
        
        pass
    
    def load(self, gsh):
        """

        """
        self.rootGroup = GSGroupItem('Name', 'SDF')
        self.rootGroup.useTag = False
        self.__loadR(gsh.get_super_root(), self.rootGroup)
        
    def __loadR(self, root, parent=None):
        """

        """
        fields = root.fields()
        if isinstance(root, GSGroup):
            group = GSGroupItem(*fields)
            if parent is None:
                self.rootGroup = group
            else:
                parent.appendChild(group)
            for mem in root.get_members():
                self.__loadR(mem, group)
        elif isinstance(root, GSThread):
            thread = GSThreadItem(*fields)
            parent.appendChild(thread)
        else:
            print 'ERROR 0 in gsmodels'
                
        pass
    
    def data(self, index, role):
        """

        """

        if index is None:
            return QVariant()
        
        if role != Qt.DisplayRole:
            return QVariant()
        
        item = index.internalPointer()
        return item.data(index.column())
    
    def flags(self, index):
        """

        """

        if index is None:
            return 0
        
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """

        """

        if (orientation == Qt.Horizontal and role == Qt.DisplayRole):
            return self.rootGroup.data(section)

        return QVariant();


    def index(self, row, column, parent):
        """

        """

        assert self.rootGroup
        group = self.nodeFromIndex(parent)
        assert group is not None
        return self.createIndex(row, column, group.child(row))
    
    def parent(self, index):
        """

        """

        node = self.nodeFromIndex(index)
        if node is None:
            return QModelIndex()
        parent = node.parent
        if parent is None:
            return QModelIndex()
        grandparent = parent.parent
        if grandparent is None:
            return QModelIndex()
        row = grandparent.rowOfChild(parent)
        assert row != -1
        return self.createIndex(row, 0, parent)
    
    
    def rowCount(self, parent):
        """

        """

        node = self.nodeFromIndex(parent)
        if node is None or isinstance(node, GSThread):
            return 0
        return len(node.members)
    
    
    def columnCount(self, parent):
        """

        """
        
        #FIXME.DILLON: should not be a constant 3.
        return 3
#        if not parent is None:
#            parent.columnCount()
#        else:
#            self.rootGroup.columnCount()
#    

    def nodeFromIndex(self, index):
        """

        """    
        return (index.internalPointer()
                if index.isValid() else self.rootGroup)

    
class GSHierarchyTreeWidget(QTreeView):
    """
    A PyQt widget for displaying a Group Scheduling Hierarchy.
    

    """
    def __init__(self, gsh, parent=None):
        super(GSHierarchyTreeWidget, self).__init__(parent)
        self.setSelectionBehavior(QTreeView.SelectItems)
        self.setUniformRowHeights(True)
        model = GSHierarchyModel(self)
        self.setModel(model)
        model.load(gsh)
        self.connect(self, SIGNAL("activated(QModelIndex)"),
                     self.activated)
        self.connect(self, SIGNAL("expanded(QModelIndex)"),
                     self.expanded)
        self.expanded()


    def currentFields(self):
        """
            
        """
        currentItem = self.model().nodeFromIndex(self.currentIndex())
        return currentItem.fields()


    def activated(self, index):
        """
        
    
        """
        currentItem = self.model().nodeFromIndex(index)    
        self.emit(SIGNAL("activated"), currentItem.fields())


    def expanded(self):
        """
        
    
        """
        for column in range(self.model().columnCount(
                            QModelIndex())):
            self.resizeColumnToContents(column)

if __name__ == "__main__":
    configfile = "../tools/groupviewer/configs/balancedpipeline.gsh"
    gsh = configutility.parse_configfile(configfile)
    gsh = GSHierarchy(gsh)
    app = QApplication(sys.argv)
    gshtest = GSHierarchyTreeWidget(gsh)
    gshtest.show()
    sys.exit(app.exec_())      
