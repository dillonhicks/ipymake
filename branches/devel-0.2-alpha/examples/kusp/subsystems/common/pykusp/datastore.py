#
# $Id: datastore.py,v 1.2 2004/10/26 00:09:29 tejasvi Exp $
#
# AUTHOR(s):  Andrew Boie
#
# Copyright 2003(C), The University of Kansas
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
from __future__ import generators
from filterwidgets import *
import copy


class DataStore(FilterComponent):
    """
    The Data Store is always the first component in the chain.

    Therefore it does not define the recieve() method. However,
    the data is modifiable through four methods: modify, remove,
    add, and replace.
    """

    def __init__(self, next_component):
        def unique():
            unique = 0
            while True:
                unique = unique + 1
                yield unique
                pass
            pass
        self.unique = unique()
        self.next_component = next_component
        self.datastructure = {}

        # indicates whether the next undoable modify method
        # should make a backup. this is set to true by
        # self.send(). it should be set to false by
        # modify operations that do not call send().
        self.clearbackup = True
        pass

    def newkey(self):
        """Return a unique integer key"""
        return self.unique.next()

    def __getitem__(self, item):
        return self.datastructure[item]

    def __setitem__(self, item, value):
        self.datastructure[item] = value
        pass
    
    

    # these are the atomic operations to modify the datastructure.
    
    def change(self, key, column, value):
        """Perform a change to the datastructure.

        This is a private method. You must do sanity/type checking here. You
        may need to do type conversion as well.
        """
        self.datastructure[key][column] = value
        pass

    def delete(self, key):
        """Delete a row in the datastructure."""
        
        del self.datastructure[key]
        pass
    

    # general methods to modify the datastructure --------------------
    
    def modify(self, keys, columns, value, nosend=False, remap=True):
        """
        Modify some fields in the datastructure.

        Rows in the datastructure are keyed by some unique, generated
        value. The value is always present in the datastructure that
        is passed via send() for easy retrieval.

        Columns are indexed by number.

        keys and columns are both lists.

        value can be any string. so you must do your own sanity checking.
        be sure to do type checking as well; you don't want strings to end
        up in integer fields or the program will diverge. you must do
        your own conversion from strings to integers.

        throws: InvalidValueException if it was not possible to insert
        a particular value in the datastructure.
        """
        if not (type(columns) is list):
            columns = [columns]
            pass

        if not (type(keys) is list):
            keys = [keys]
            pass
        
        self.backup()
        ds = self.datastructure
        for key in keys:
            for column in columns:
                self.change(key, column, value)
                pass
            
            pass
        
        if not nosend: return self.send(remap)
        return
        pass

    def changeRows(self, keys, cvalues, nosend=False, remap=True, makecopy=False):
        """
        keys is a list of datastore key
        cvalues is a list of (column, value) tuples
        makecopy will first copy the row, then apply the
        changes to the original row.
        """

        self.backup()
        for key in keys:
            if makecopy:
                row = self.datastructure[key]
                # make a copy of the row
                rowcopy = copy.deepcopy(row)
                # assign a new unique id to the row
                rowcopy[0] = self.newkey()
                # put the copy in the datastructure as the "original"
                self.datastructure[rowcopy[0]] = rowcopy
                pass
                
            for column, value in cvalues:
                if value == None:
                    # a value of None means leave it alone
                    continue
                else:
                    self.change(key, column, value)
                    pass
                pass
            #print self[key]
            pass  
        
        if not nosend: return self.send(remap)
        return


    def modifyRows(self, keys, values, nosend=False, remap=True, makecopy=False):
        """replace the contents of some rows with new values
        any value of None will be ignored
        """
        # THIS IS DEPRECATED! use changerows instead
        print "fatal datastore deprecation warning: modifyRows()"
        
        
        self.backup()
        
        for key in keys:

            
            if makecopy:
                row = self.datastructure[key]
                # make a copy of the row
                rowcopy = copy.deepcopy(row)
                # assign a new unique id to the row
                rowcopy[0] = self.newkey()
                # put the copy in the datastructure as the "original"
                self.datastructure[rowcopy[0]] = rowcopy
                pass
                
            for index in range(len(values)):
                value = values[index]
                if value == None:
                    # a value of None means leave it alone
                    continue
                else:
                    self.change(key, index, value)
                    pass
                pass
            pass  
        
        if not nosend: return self.send(remap)
        return

    def add(self, valueslist, nosend = False, remap=True):
        """
        add a list of values, where each member of the list
        is another list or tuple which corresponds to the layout
        of the datastructure. a unqiue id will be generated for each
        value added, and a list of these ids is the return value

        note: all items in valueslist will be strings. you must do
        type conversion and checking yourself.

        throws: InvalidValueException
        """
        #print valueslist
        self.backup()
        
        uniquelist = []
        for values in valueslist:
            u = self.newkey()
            v = [u]
            v.extend(values)
            #print v
            uniquelist.append(u)
            
            # fill the row with None values
            self.datastructure[u] = [None for item in v]
            # we can't modify the 0-row with change, so we do it
            # here.
            self.datastructure[u][0] = u

            # replace those Nones with the proper values,
            # doing checking for each assignment
            for columnindex in range(1, len(v)):
                if v[columnindex] != None:
                    self.change(u, columnindex, v[columnindex])
                    pass
                
                pass
            pass
        
        if not nosend: return self.send(remap)
        return uniquelist

    def remove(self, keys, nosend=False, remap=True):
        """
        remove all items which correspond to the unique IDs
        in keys, which is a list
        """
        for key in keys:
            self.delete(key)
            pass
        if not nosend: return self.send(remap)
        pass

    def clear(self, nosend=False, remap=True):
        """clear the contents of the datastore"""
        self.backup()
        self.datastructure = {}
        if not nosend: return self.send(remap)
        return

    #---modification methods based on search criteria
    
    def replace(self, column, criteria, newvalue, makecopy=False, nosend=False, remap=True):
        """search the datastructure, put 'newvalue' in 'column' in any row of the
        datastructure that matches all the items in 'criteria'

        criteria is a list of (column, value)
        """
        self.backup()

        oldcompare = tuple([item[1] for item in criteria])
        for key in self.datastructure:
            compare = tuple([self.datastructure[key][item[0]] for item in criteria])
            
            if compare == oldcompare:
                if makecopy:
                    row = self.datastructure[key]
                    # make a copy of the row
                    rowcopy = copy.deepcopy(row)
                    # assign a new unique id to the row
                    rowcopy[0] = self.newkey()
                    # put the copy in the datastructure as the "original"
                    self.datastructure[rowcopy[0]] = rowcopy
                    pass
                
                self.change(key, column, newvalue)
                pass
            pass
        if not nosend: return self.send(remap)
        pass

    def removeMatching(self, valueslist, nosend=False, remap=True):
        # where valueslist is a list of list of tuples: (column, value)
        # FIXME: document this confusing shit
        self.backup()
        deletekeylist = []

        for values in valueslist:
            for key in self.datastructure:
                row = self.datastructure[key]
                deleteflag = True
                for valuetuple in values:
                    if row[valuetuple[0]] != valuetuple[1]:
                        deleteflag = False
                        break
                    pass
                if deleteflag:
                    deletekeylist.append(key)
                    pass
                pass
            pass
        
        if deletekeylist:
            #print deletekeylist
            self.remove(deletekeylist)
            pass
        if not nosend: return self.send(remap)
        return

    # undo methods ----------------------------
    
    def backup(self):
        # if the clearbackup flag is set to false, then we have already set a backup point
        # and should not touch the backupdict.
        # clearbackup is only set to True initially and upon a successful self.send()
        if self.clearbackup:
            self.backupdict = copy.deepcopy(self.datastructure)
            self.clearbackup = False
            pass
        pass

    def undo(self, nosend=False):
        temp = self.datastructure
        self.datastructure = self.backupdict
        self.backupdict = temp
        if not nosend: return self.send()
        pass

    # component interface methods ---------------

    def send(self, remap=True):
        """This guarantees a consistent datastructure will be sent,
        if the return value is false, an undo or remapping had to be done"""
        result = True
        errors = self.checkConsistency()
        
        if errors:
            result = False
            if remap:
                self.fix()
            else:
                self.undo()
                return
            pass
        
        # data has been sent to the user. so if the user modifies the
        # datastore again, set a new undo point
        self.clearbackup = True
        
        ds = self.datastructure
        next_component = self.next_component

       
        next_component.receive([tuple(ds[key]) for key in ds])
        
        return result
    
    def recieve(self, param):
        """this should be the first component in the pipeline, so recieve does nothing"""
        
        pass

    def fix(self):
        """fix any conflicts"""
        pass
    

    #---abstract methods for consistency checking

    def checkConsistency(self):
        """Check the consistency of the datastructure and return a list of errors"""
        errors = []
        # suggested implementation:
        # errors will have a list
        # each element in the list is a tuple
        # each tuple shows a collision
        # it has the column, the offending value, and the datastore keys associated with this collision
        # note that the first instance of a value is ignored. so the errors list
        # will not have the keys for that first instance. it will have the keys for all
        # other instances of that value. these should be remapped to avoid conflicts.
        return errors

    def remap(self, errors):
        """Fix all the errors."""
        return
    
    #---data retrieval methods----

    def values(self, columns, filters=[], exclude=[], include=[], dict=False):
        # exclude takes priority over include
        rows = self.filter(filters)
        valueslist = {}
        for row in rows:
            key = row[0]
            if key == None:
                #print rows
                raise Exception, "key was none!"
            if (not include or key in include) and (key not in exclude):
                if type(columns) is list:
                    values = [row[column] for column in columns]
                    values = tuple(values)
                else:
                    values = row[columns]
                    pass
                
                if values not in valueslist.keys():
                    valueslist[values] = [key]
                else:
                    valueslist[values].append(key)
                    pass
                pass
            pass
        if dict:
            return valueslist
        else:
            return valueslist.keys()
        pass

    def filterkeys(self, filters):
        return [row[0] for row in self.filter(filters)]
    

    def filter(self, filters):
        """
        filters = [(column, value)]
        """
        if not (type(filters) is list):
            filters = [filters]
            pass

        result = []
        for key in self.datastructure:
            match = True
            row = self.datastructure[key]
                
            for filter in filters:
                #print filter
                column, value = filter
                if row[column] != value:
                    match = False
                    pass
                pass
            if match:
                result.append(row)
                pass
            pass
        return result
    pass


