#
# $Id: filterwidgets.py,v 1.2 2004/10/26 00:09:29 tejasvi Exp $
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
#!/usr/bin/env python
from __future__ import generators
import gtk
import gtk.glade


from pykusp.pathfinder import find
from pykusp.framework import *


import pango
import gobject
import string



class InvalidValueException(Exception):
    def __init__(self, column, value, reason):
        Exception.__init__(self)
        self.column = column
        self.value = value
        self.reason = reason
        pass
    pass



class FilterComponent:
    """
    GUI widgets that allow the user to filter data, in a pipeline.

    The filter chain should be built up backwards. The last item in the chain
    should display the data only; its send() method should do nothing.

    Examples of filterComponents:
    1) A text field that searches the datastruture, and filters out any
    rows that don't have data matching what the user typed in.

    2) A list showing a particular column in the datastructure, allowing
    the user to filter based upon which rows are selected.

    3) A filter to perform a specific operation/conversion on the data. It
    will have no GUI widget to go along with it, so leave getWidget() unimplemented.
    """

    def __init__(self, nextcomponent, controllerwindow=None):
        self.controllerwindow = controllerwindow
        self.nextcomponent = nextcomponent
    
    def receive(self, datastructure):
        """
        Take in the datastructure, update cached copy and display, and invoke send().

        This method should be invoked when the datastructure changes in any
        way, due to filtering. Instances of FilterComponent should keep a
        cached copy of the datastructure to compare for changes. This
        cached copy should be replaced with the parameter.

        If this component has/is a GUI widget that displays part of
        the datastructure, it should be updated.

        Finally, send() should be called so it can be passed to the next
        component in the chain.

        After the pipeline has been constructed, you should send the datastructure
        to the first FilterComponent via this method. The data will propagate through
        the pipeline. If the datastructure is changed in any way, you should
        call this again.
        """
        self.datastructure = datastructure
        self.send()
        return
    
    
    def send(self):
        """
        Apply any filtration necessary and pass data to the next component.

        What we are filtering and passing along is the cached copy of the
        datastructure. This cached copy is updated in any calls to
        receive().
        
        This method should be called under two circumstances:

        1) If receive was called, we must propagate the data to the next
        link in the chain. So after receive finishes its tasks, it automatically
        calls this method.

        2) If the filter parameters have changed, the cached data must be refiltered.
        """
        self.nextcomponent.receive(self.datastructure)
        return

    def setDatastore(self, datastore):
        """
        Indicate which DataStore instance any data modifications should be sent to

        Don't bother calling if your filter component doesn't have any editing
        facilities.
        """
        self.datastore = datastore
        pass

    def ask(self, string):
        """ask the user a question, return a boolean indicating the answer."""
        
        return self.controllerwindow.ask(string)
    
    


class EndComponent(FilterComponent):
    """
    This is always the last component in the pipeline, and
    the first one instantiated. It should
    show the results of the filtration. It does not do any
    filtering itself, so its send() method should do nothing
    """
    def __init__(self, controllerwindow=None):
        FilterComponent.__init__(self, None, controllerwindow)
        pass
    
    
    def send(self):
        pass
    
    pass


# FIXME: when pygtk 2.4 is out, use gtk.RadioToolButton
class RadioFilter(FilterComponent, gtk.HBox):
    def __init__(self, nextcomponent, tuples, column):
        """
        Tuples is a list of tuples of the format:
        (text, filtertext)
        """
        gtk.HBox.__init__(self)
        FilterComponent.__init__(self, nextcomponent)
        
        allbutton = gtk.RadioButton(None, "All")
        allbutton.set_active(True)
        
        allbutton.connect("toggled", self.toggled, None)
        
        self.pack_start(allbutton, expand=False)
        self.datastructure = None
        self.next_component = nextcomponent
        self.active = None
        self.column = column
        for tuple in tuples:
            radiobutton = gtk.RadioButton(allbutton, tuple[0])
            radiobutton.connect("toggled", self.toggled, tuple[1])
            self.pack_start(radiobutton, expand=False)
            pass
        pass

    def send(self):
        if self.active == None:
            self.next_component.receive(self.datastructure)
        else:
            self.next_component.receive([row for row in self.datastructure if row[self.column]==self.active])
            pass
        pass

    def toggled(self, togglebutton, active):
        if togglebutton.get_active():
            self.active = active
            self.send()
            pass
        pass
    pass        

class CheckFilter(FilterComponent, gtk.CheckButton):
    def __init__(self, label, column, nextcomponent):
        gtk.CheckButton.__init__(self, label)
        FilterComponent.__init__(self, nextcomponent)
        
        self.column = column
        self.datastructure = []
        self.connect("toggled", self.userToggled)
        self.next_component = nextcomponent
        
        
        pass

    def userToggled(self, button):
        self.send()
        pass
    
    def send(self):
        if self.get_active():
            # button is checked, so do filtering
            self.next_component.receive([row for row in self.datastructure if row[self.column]])
        else:
            self.next_component.receive(self.datastructure)
            pass
        pass
    
    

class SearchField(FilterComponent, gtk.HBox):
    """
    A text field to allow the user to interactively filter the datastore.

    If nothing is typed in, no filtration is done. As soon as a character
    is typed into the box, filtration is done, for each keypress.

    There is a button which will clear the contents of the search box, and
    consequently eliminate any filtration.

    There should be a popup menu which will allow the user to search
    all fields in the datastructure, or just one of them.
    """

    def __init__(self, next_component, filterkeys):
        """
        nextComponent is the next FilterComponent in the pipeline.
        pipelines should be built up backwards, so the instance
        of the next Component should already exist.

        filterkeys is a list of (column numbers, column names)
        in the datastructure to search in.
        by default, searching is done in all of these fields, but the
        user may narrow that down.
        """
        gtk.HBox.__init__(self)
        FilterComponent.__init__(self, next_component)
        
        # define instance variables
        self.datastructure = []
        # the list of all keys we can filter on
        self.filterkeys = [item[0] for item in filterkeys]

        self.allkeys = {"All":[item[0] for item in filterkeys]}
        for num, name in filterkeys:
            self.allkeys[name] = [num]
            pass
        
        # the list of keys we are filtering on
        self.next_component = next_component

        # GUIness
        # search option menu

        combobox = gtk.combo_box_new_text()
        combobox.append_text("All")
        for filterkey in filterkeys:
            combobox.append_text(filterkey[1])
            pass
        combobox.connect("changed", self.menuActivated) 
       
        self.pack_start(combobox, expand=False)
    
        # text entry
        self.entry = gtk.Entry()
        self.entry.connect("changed", self.textEdited)
        self.pack_start(self.entry)
        # clear button
        self.button = gtk.Button("Clear")
        self.button.connect("clicked", self.buttonClicked)
        self.button.set_sensitive(False)
        self.pack_start(self.button, expand=False)
        self.lock = True
        combobox.set_active(0)
        self.lock = False
        pass


    def send(self):
        result = []
        filtertext = self.entry.get_text().lower()
        if filtertext:
            for row in self.datastructure:
                for column in self.filterkeys:
                    if string.find(str(row[column]).lower(), filtertext) >= 0:
                        result.append(row)
                        break
                    pass
                pass
            self.next_component.receive(result)
        else:
            self.next_component.receive(self.datastructure)
            pass
        return

    def menuActivated(self, item):
        self.filterkeys = self.allkeys[get_active_text(item)]

        if not self.lock:
            self.send()
            pass
        pass
    
    def textEdited(self, *param):
        if self.entry.get_text():
            self.button.set_sensitive(True)
        else:
            self.button.set_sensitive(False)
            pass
        
        self.send()
        
        
        return

    def buttonClicked(self, *param):
        self.entry.set_text("")
        pass
    pass

# FIXME:
# add support for:
# 4. gtk theme-compatible highlighting. no idea how to do this. 
# 7. docstring badly out of date

class MultiColumnFilterList(FilterComponent, gtk.ScrolledWindow):
    """
    Very similar to FilterList, but the table has an arbitrary
    number of columns. This is for datastructures that have multiple
    unique keys; namespaces must have unique family names and family numbers,
    and there must be a one-to-one correspondence between the two.

    what sets this class apart from filterlist is that all keys are
    displayed, and any conflicts are highlighted by changing the text
    color to red. using the namespace example, if rows in the datastructure
    had the same family name but different number, or different names but
    identical family numbers, they will be highlighted so that the user can
    fix them quickly.
    """
    def __init__(self, controllerwindow, next_component, filterkeys, groupingrow, groupingval, skiplist=[], defaultsort=0, hide=[], name1=None ):
        """
        controllerwindow is a ControllerWindow instance, for sending
        messages
        
        nextComponent is the next FilterComponent in the pipeline.
        pipelines should be built up backwards, so the instance
        of the next Component should already exist.

        filterkeys is a list of (column number, name, type, editable, groupingrow, groupingval)
         0   column number is the index in the the datastructure's rows
         1   name is the name of the column, to put in the header
         2   type is the gobject type of the column's data
         3   editable is if the column can be edited
         
        skiplist is a list of filterkey indexes to NOT check for conflicts

        defaultsort is the filterkey index to sort by default

        hide is a list of filterkey indices to not display

        name1 is a string name for debugging purposes
        """
        # call superclass constructors
        gtk.ScrolledWindow.__init__(self)
        FilterComponent.__init__(self, next_component, controllerwindow)
        
        # because we only have style, variant, weight, and underline
        if len(filterkeys) - len(skiplist) > 4:
            raise Exception, "Cannot have more than 4 columns to check for conflicts."

        
        # create the liststore
        params = [key[2] for key in filterkeys]
        params.append(gobject.TYPE_INT)
        liststore = gtk.ListStore(*params)
        treeview = gtk.TreeView(liststore)
        # provides a speedup in displaying the treeview, but only
        # available in pygtk 2.4
        if check24():
            #treeview.set_property("fixed-height-mode",True)
            pass
        lastcolumn = len(filterkeys)
        global_editable = False
        
           
        #treeview.connect("row_activated", self.rowActivated())
        
        
        z = 0
        # create the columns        
        for filterkey in filterkeys:
            column_number, column_name, column_type, editable = filterkey
            global_editable = global_editable or editable
            if z not in hide:
                renderer = gtk.CellRendererText()
                if editable:
                    renderer.set_property("editable", True)

                    # FIXME: make it so editing requires a double-click
                    renderer.connect("edited", self.cellEdited, column_number, z)
                    pass
                
                column = gtk.TreeViewColumn(column_name,
                                            renderer,
                                            text=z)
                column.set_resizable(True)
                column.set_sort_column_id(z)
                liststore.set_sort_func(z,self.comparefunction, lastcolumn)
              
                def highlight(column, cell_renderer, tree_model, iter):
                        highlightflag = tree_model[iter][lastcolumn]
                        if highlightflag > 15: highlightflag = 15
                        
                        if highlightflag >= 8:
                            cell_renderer.set_property("variant", pango.VARIANT_SMALL_CAPS)
                            highlightflag = highlightflag - 8
                        else:
                            cell_renderer.set_property("variant", pango.VARIANT_NORMAL)
                            pass
                        if highlightflag >= 4:
                            cell_renderer.set_property("weight", pango.WEIGHT_HEAVY)
                            highlightflag = highlightflag - 4
                        else:
                            cell_renderer.set_property("weight", pango.WEIGHT_NORMAL)
                            pass
                        if highlightflag >= 2:
                            cell_renderer.set_property("underline", pango.UNDERLINE_SINGLE)
                            highlightflag = highlightflag - 2
                        else:
                            cell_renderer.set_property("underline", pango.UNDERLINE_NONE)
                            pass
                        if highlightflag >= 1:
                            cell_renderer.set_property("style", pango.STYLE_ITALIC)
                            highlightflag = highlightflag - 1
                        else:
                            cell_renderer.set_property("style", pango.STYLE_NORMAL)
                            pass
                        
                        pass
                column.set_cell_data_func(renderer, highlight)
                treeview.append_column(column)
                if z == defaultsort:
                    column.clicked()
                    pass
                z = z + 1
                pass
            pass
    
        treeview.get_selection().connect("changed", self.__selectionChanged)
        if global_editable:
            self.key_event_id = treeview.connect("key-press-event", self.key_press)
            pass
        
        treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        iter = liststore.append()
        liststore[iter][0] = "All"
        # the -512 value in the last column indicates that this is the "All" row
        liststore[iter][lastcolumn] = -512
        
        self.add(treeview)
        
        # initialize attributes
        self.treeview = treeview
        self.datastructure = []
        self.liststore = liststore
        self.lock = False
        self.groupingrow = groupingrow
        self.groupingval = groupingval
        
##        self.columnnames = [filterkey[1] for filterkey in filterkeys]
##        self.filterkeys = [filterkey[0] for filterkey in filterkeys]
##        self.filtertypes = [filterkey[2] for filterkey in filterkeys]
##        self.flags = [filterkey[3] for filterkey in filterkeys]

        self.filterkeys = filterkeys
        self.lastcolumn = lastcolumn
        self.treeselection = treeview.get_selection()
        self.next_component = next_component
        self.datastore = None
        self.skiplist = skiplist
        self.controllerwindow = controllerwindow
        self.reselect = False
        self.name1 = name1
        pass
    

    def __selectionChanged(self, treeselection):
        """
        Refilter cached datastructure based upon what is now selected
        """
        if not self.lock:
            self.send()
            pass
        return

    # keyboard listener stuff

    def delete(self, *param):

        vallist = self.getSelectedValues()
        # transform vallist so that each value in it
        # is converted into a tuple of (column, value).
        # this is the format required by removeMatching()
        if vallist:
            for i in range(len(vallist)):
                for j in range(len(vallist[i])):
                    vallist[i][j] = (self.filterkeys[j][0], vallist[i][j])
                    pass
                pass
            
            if self.ask("Really remove "+`len(vallist)`+ " row(s)?"):
                self.datastore.removeMatching(vallist)
                pass
            pass
        pass

    def key_press(self, widget, event):
        if event.keyval in [65535, 65288]:
            self.delete()
            pass
        pass
    
    
    # edit cell callback
   
    def cellEdited(self, cellrenderertext, path, new_text, dcolumn, lcolumn):
        # obtain the unique key for the edited row
        
        iter = self.liststore.get_iter_from_string(path)
        oldtext = [(self.filterkeys[index][0],self.liststore[iter][index]) for index in range(self.lastcolumn)]
        

        # we shall make a note that a field was modified. the call to receive() thru the pipeline
        # will add and delete a row in our liststore; this flag will tell us to select the new row.
        self.reselect = True

        try:
            
            if self.datastore.replace(dcolumn, oldtext, new_text, remap=False):
                self.controllerwindow.status("Row value changed successfully.")
            else:
                self.controllerwindow.say("Conflicting value entered; changes rejected.")
                pass
            pass
        except InvalidValueException, ex:
            self.controllerwindow.say("Invalid value '"+ex.value+"' entered in column "+str(ex.column)+":\n"+ex.reason)
            pass
        pass
    
    def receive(self, datastructure):
        """
        Examine new datastructure, add/remove rows in list as necessary.

        We want, as much as possible, to preserve rows that are already
        selected. So we need to compare the contents of self.liststore
        against this new datastructure, removing and adding rows as needed.

        If, by doing this, we have unselected all rows, then the "All" row
        should be automatically selected. We need to block __selectionChanged
        while we are doing all of this; when done we will call send() ourselves.
        """
        
        # obtain attributes we need
        liststore = self.liststore
        filterkeys = self.filterkeys
        
        # block any callbacks to __selectionChanged() from doing anything, since
        # we may modify the liststore's selection.
        self.lock = True

        # update our copy of the datastructure
        self.datastructure = datastructure

        # obtain a list of unique values in the datastructure for our filterkey
        valueslist = []
        for row in datastructure:
            
            values = [row[filterkey[0]] for filterkey in filterkeys]
            # third item in values is whether there is a conflict; initialize to -1
            values.append(0)
            
            if None not in values and values not in valueslist:
                valueslist.append(values)
                pass
            pass
        
        # we need to know which columns we are looking at
        # for conflicts; we may not be examining all of them
        flagindex = self.lastcolumn
        # no point in doing this if there is only one column

        # debug code
    
        # end debug code
        
        if flagindex > 1:
            indices = [index for index in range(flagindex) if index not in self.skiplist]
            
            for index in indices:
                
                known_values = {}
                for values in valueslist:
                    
                    value = values[index]
                    
                    if value in known_values:
                        # flagval will determine the color of the row. we use
                        # 2**index so that the color represents what column the problem is in;
                        # and problems with multiple columns can be added together
                        flagval = 2**index
                        if known_values[value][flagindex] < flagval:
                            # we do a check to make sure we aren't adding flagval more than once
                            # for a particular column
                            known_values[value][flagindex] = known_values[value][flagindex] + flagval
                            pass
                        
                        values[flagindex] = values[flagindex] + flagval
                        
                    else:
                        known_values[value] = values
                        pass
                    pass
                pass
            pass
        
        

        # update the "All" row to indicate the number of values
        if len(valueslist) != 1:
            allstring = "All ("+`len(valueslist)`+" items)"
        else:
            allstring = "All (1 item)"
            pass

        liststore[0][0] = allstring
        liststore[0][flagindex] = -512

        # synchronize valuelist and liststore.
        # it would be easy to just reset liststore, but we do
        # not want to disturb selected rows that haven't changed.
        
        # Step 1: make lists of all our values; using dictionaries
        # is faster than nested loops

        lskeys = {}
        lskeys2 = {}
        iter = self.liststore.get_iter_root()
        # skip the 0-row, since it is the "All" row
        iter = liststore.iter_next(iter)
        valueslist2 = [values[:-1] for values in valueslist]
        while iter != None:
            row = liststore[iter]
            key = tuple([column for column in row])
            key2 = tuple([column for column in row][:-1])
            lskeys[key] = iter
            lskeys2[key2] = iter
            iter = liststore.iter_next(iter)
            pass

        # step 2: check for rows to add
        for values in valueslist:
            # check to see if this value is already in the list
            addflag = True
            
            if tuple(values) not in lskeys:
                
                # values does not match precisely anything currently in the liststore
                if tuple(values[:-1]) not in lskeys2:
                
                    # the row is missing. add it.
                    iter = liststore.append()
                    newrow = liststore[iter]
                    for index in range(len(values)):
                        newrow[index] = values[index]
                        pass
                    if self.reselect:
                        self.treeselection.select_iter(iter)
                        self.reselect = False
                        pass
                    pass
                else:
                    # the row is present, but the update flag is different
                
                    liststore[lskeys2[tuple(values[:-1])]][flagindex] = values[flagindex]
                    pass
                pass
            pass

        # step 3: check for rows to delete
        for key in lskeys:
            if list(key) not in valueslist and list(key)[:-1] not in valueslist2:
                # this row needs to be deleted
                
                liststore.remove(lskeys[key])
                pass
            pass

        # if at this point nothing is selected, select the "all" row

        self.scounter = 0
        
        def func(model, path, iter):
            self.scounter = self.scounter + 1
            pass
        
        self.treeselection.selected_foreach(func)
        if self.scounter == 0:
            iter = self.liststore.get_iter_root()
            self.treeselection.select_iter(iter)
            pass    
        
        # at this point our liststore should be up-to-date.
        # we are ready to filter the datastructure, and pass
        # the filtered data down the pipe.
        
        self.send()
        self.lock = False
        
        pass

    

    def send(self):
        
        

        # get attributes
        datastructure = self.datastructure
        filterkeys = self.filterkeys
        next_component = self.next_component

        # create a list of selected values.
        # enable the skipall flag, for speed; if "all" is selected,
        # we just pass the datastructure unmodified
        selected_values = self.getSelectedValues(True)

    
        

        # filter the datastructure based upon what is selected.
        if selected_values:
            filtered = [row for row in datastructure if
                        [row[filterkey[0]] for filterkey in filterkeys] in selected_values]
        else:
            filtered = datastructure
            pass
        
        
        # send the filtered datastructure to the next component in the pipeline
        
        next_component.receive(filtered)
        pass

    def iterIsFirstRow(self, iter):
        firstrow_iter = self.liststore.get_iter_root()
        firstrow_path = self.liststore.get_path(firstrow_iter)
        path = self.liststore.get_path(iter)
        return path == firstrow_path

    def getSelectedValues(self, skipall=False):
        
         # create a list of selected values.
        selected_values = []
        liststore = self.liststore
        treeselection = self.treeselection
        # first, determine whether the 0-row, All, in the store was selected.
        # if so, delselect all other rows
        firstrow_iter = liststore.get_iter_root()
        if treeselection.iter_is_selected(firstrow_iter):
            # block callbacks to __selectionChanged
            self.lock = True
            treeselection.unselect_all()
            treeselection.select_iter(firstrow_iter)
            # unlock the __selectionChanged callback, since we are done
            # modifying the selection
            self.lock = False
            
            if skipall:
                return []
            
            iter = liststore.iter_next(firstrow_iter)
            while iter != None:
                selected_values.append([column for column in liststore[iter]][:-1])
                iter = liststore.iter_next(iter)
                pass
            pass
        else:
            def foo(treemodel, path, iter):
                selected_values.append([column for column in liststore[iter]][:-1])
                pass
            treeselection.selected_foreach(foo)
            pass
        
        
        return selected_values
        

    def comparefunction(self, treemodel, iter1, iter2, allcolumn):
        column = treemodel.get_sort_column_id()[0]
        if treemodel.get_sort_column_id()[1] == gtk.SORT_DESCENDING:
            
            i1 = iter2
            i2 = iter1
        else:
            
            i1 = iter1
            i2 = iter2
            pass
        
        if treemodel[i1][allcolumn] == -512:
            return -1
        if treemodel[i2][allcolumn] == -512:
            return 1
        
        if treemodel[iter1][column] > treemodel[iter2][column]:
            return 1
        elif treemodel[iter1][column] == treemodel[iter2][column]:
            return 0
        else:
            return -1
        pass
    pass

