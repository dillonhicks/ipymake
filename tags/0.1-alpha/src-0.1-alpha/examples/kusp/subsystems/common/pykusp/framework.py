#
# $Id: framework.py,v 1.3 2004/11/17 23:27:20 boie Exp $
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


import gtk
import gobject
from os.path import *
import os

# general-purpose classes and functions go here, for lack of a better
# place to put them

def relative(path):
    
    return relativePath(os.getcwd(), path)

class SimpleBuffer(gtk.TextBuffer):
    def get_text(self):
        return gtk.TextBuffer.get_text(self,*self.get_bounds()).strip()
    pass


def relativePath(path1, path2):
    """Convert absolute path2 into a path relative to path1"""

    # path1 = /usr/local/lib/frank
    # path2 = /usr/local/games/doom3
    #print path2,"relative to",path1
    if not isdir(path1):
        #print "path1 not a dir"
        path1 = split(path1)[0]
        pass
    
    import string
    path1 = string.split(abspath(path1),"/")
    path2 = string.split(abspath(path2),"/")

    
    
    # eliminate the common elements
    while(True):
        if not path1 or not path2:
            break
        
        item1 = path1[0]
        item2 = path2[0]
        

        if item1 != item2:
            # we have found the point where the paths diverge.
            break
        else:
            path1 = path1[1:]
            path2 = path2[1:]
            pass
        pass

    # path1 = ["lib","frank"]
    # path2 = ["games", "doom3"]

    #print path1, path2
    result = "./"

    # back up to the divergence point
    for item in path1:
        result = result + "../"
        pass

    # move up to path2
    for item in path2:
        result = result + "/" + item
        pass
    #print result
    result = normpath(result)
    #print result
    return result
    

    
    
def check24():
    """Return True if we are using PyGTK 2.4 or above."""
    major, minor, revision = gtk.pygtk_version
    if major > 2:
        return True

    if major == 2 and minor > 2:
        return True

    return False



class ControllerWindow:
    def say(self, string, type=gtk.MESSAGE_ERROR, parent=None):
        if not parent:
            parent = self
            pass
        
        #print "gtkgui.message: " + string
        msgdia = gtk.MessageDialog(parent,
                                   gtk.DIALOG_MODAL,
                                   type,
                                   gtk.BUTTONS_OK,
                                   string)
        msgdia.run()
        msgdia.destroy()
        return
    
    def ask(self, string, parent=None):
        if not parent:
            parent = self
            pass
        #print "gtkgui.question: " + string
        
        msgdia = gtk.MessageDialog(parent,
                                   gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_YES_NO,
                                   string)
        response = msgdia.run()
        msgdia.destroy()
        if response == gtk.RESPONSE_YES:
            #print "response yes"
            return True
        else:
            #print "response no"
            return False
        pass


    def getSaveFilename(self, string="Save File As", filename=None, parent=None):
        if not parent:
            parent = self
            pass
        
        if check24():
            fs = gtk.FileChooserDialog(title=string, parent=parent, action=gtk.FILE_CHOOSER_ACTION_SAVE)
            fs.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
            fs.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            if filename:
                #fs.set_current_folder(filename)
                #fs.set_current_name(filename)
                pass
            response = fs.run()
            if response == gtk.RESPONSE_OK:
                filename = fs.get_filename()
            else:
                filename = None
                pass
            fs.destroy()
            #print "chose",filename
            return filename
        else:
            return self.getFilename(string)
        pass
    

    def getDirectory(self, string="Choose folder", filename=None, parent=None):
        if not parent:
            parent = self
            pass
        
        if check24():
            fs = gtk.FileChooserDialog(title=string, parent=parent, action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
            fs.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
            fs.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            if filename:
                fs.set_current_folder(filename)
                pass
            response = fs.run()
            if response == gtk.RESPONSE_OK:
                filename = fs.get_filename()
            else:
                filename = None
                pass
            fs.destroy()
            return filename
        else:
            return self.getFilename(string)
        pass
    
    
    def getFilename(self, string="Open File", filename=None, parent=None):
        #print "getfilename"
        if not parent:
            parent = self
            pass
        
        if check24():
            fs = gtk.FileChooserDialog(title=string, parent=parent, action=gtk.FILE_CHOOSER_ACTION_OPEN)
            fs.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
            fs.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            if filename:
                fs.set_current_folder(filename)
                pass
            response = fs.run()
            if response == gtk.RESPONSE_OK:
                filename = fs.get_filename()
            else:
                filename = None
                pass
            fs.destroy()
            return filename
        else:
            fs = gtk.FileSelection(string)
            fs.set_select_multiple(True)
            
            response = fs.run()
            
            if response == gtk.RESPONSE_OK:
                filename = fs.get_filename()
            else:
                filename = None
                pass
            fs.destroy()
            return filename
            
        pass

    def getFilenames(self, string="Open File(s)", filename=None, parent=None):
        if not parent:
            parent = self
            pass
        
        if check24():
            fs = gtk.FileChooserDialog(title=string, parent=parent, action=gtk.FILE_CHOOSER_ACTION_OPEN)
            fs.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
            fs.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            fs.set_select_multiple(True)
            if filename:
                fs.set_current_folder(filename)
                pass
            response = fs.run()
            if response == gtk.RESPONSE_OK:
                filename = fs.get_filenames()
            else:
                filename = []
                pass
            fs.destroy()
            return filename
        else:
            result = self.getFilename(string, filename, parent)
            if result:
                return [result]
            else:
                return []
            pass
            ##fs = gtk.FileSelection(string)
##            fs.set_select_multiple(True)
##            response = fs.run()
            
##            if response == gtk.RESPONSE_OK:
##                filenames = fs.get_selections()
##            else:
##                filenames = []
##                pass
##            fs.destroy()
##            return filenames
        pass

    def getString(self, string, default=None, parent=None):
        #print string
        if not parent:
            parent = self
            pass
        class SimpleDialog(gtk.Dialog):
            def __init__(self, parent1, message):
                gtk.Dialog.__init__(self,
                                    title="Question",
                                    parent=parent1,
                                    flags=gtk.DIALOG_MODAL,
                                    buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
                                             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
                                    )
                self.vbox.pack_start(gtk.Label(message))
                self.entry = gtk.Entry()
                if default != None: self.entry.set_text(default)
                self.vbox.pack_start(self.entry)
                self.vbox.show_all()
                return
            def getData(self):
                return self.entry.get_text()
            pass
        dialog = SimpleDialog(parent, string)
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            result = dialog.getData()
        else:
            result = None
            pass
        dialog.destroy()
        return result
    pass

class JustifiedLabel(gtk.HBox):
    # this is basically a hack, to get the labels to right-justify in the table
    def __init__(self, text):
        gtk.HBox.__init__(self)
        label = gtk.Label(text)
        self.active = True
        self.pack_end(label, fill=False, expand=False)
        pass
    pass

class ActiveLabel(JustifiedLabel):
    def get_active(self):
        return True

    def set_active(self, *param):
        pass
    
    pass

def get_active_text(combobox):
    model = combobox.get_model()
    active = combobox.get_active()
    if active < 0:
        return None
    return model[active][0]


def get_combo(editable=False):
    if check24():
        # declaring thse classes here so non-pygtk 2.4 machines
        # won't explode
        class ComboWrapper(gtk.ComboBox):
            def __init__(self):
                self.model = gtk.ListStore(gobject.TYPE_STRING)
                gtk.ComboBox.__init__(self, self.model)
                self.entry = self.child
                cell = gtk.CellRendererText()
                self.pack_start(cell, True)
                self.add_attribute(cell, "text", 0)
                self.entry = self
                pass
            def get_text(self):
                iter = self.get_active_iter()
                if iter:
                    row =  self.model[iter]
                    return row[0]
                else:
                    return ""
                pass
            
            def set_text(self, text):
                iter = self.model.get_iter_root()
                flag = False
                while iter:
                    row = self.model[iter][0]
                    
                    if row == text:
                        flag = True
                        break
                    iter = self.model.iter_next(iter)
                    pass
                if flag:
                    self.set_active_iter(iter)
                    
                else:
                    
                    pass
                pass
            
            def set_editable(self, param):
                pass
            
            
            def set_popdown_strings(self, textlist):
                print "set strings"
                self.model.clear()
                for text in textlist:
                    iter = self.model.append()
                    self.model[iter][0] = text
                    
                    pass
                iter = self.model.get_iter_root()
                self.set_active_iter(iter)
                pass
            pass
        
        class ComboEntryWrapper(gtk.ComboBoxEntry):
            def __init__(self):
                self.model = gtk.ListStore(gobject.TYPE_STRING)
                gtk.ComboBoxEntry.__init__(self, self.model, 0)
                self.entry = self.child
                
                pass
            
            def set_popdown_strings(self, textlist):
                self.model.clear()
                for text in textlist:
                    iter = self.model.append()
                    self.model[iter][0] = text
                    pass
                iter = self.model.get_iter_root()
                self.set_active_iter(iter)
                pass
            
            pass
        
        if editable:
            result = ComboEntryWrapper()
        else:
            result =  ComboWrapper()
            pass
        pass
    else:
        result =  gtk.Combo()
        result.entry.set_editable(editable)
        pass
    return result

class IntEntry(gtk.Entry):
    """A gtk.Entry that only accepts input that represents an integer value"""

    def __init__(self):
        gtk.Entry.__init__(self)
        self.connect("changed", self.textEdited)
        self.verified = ""
        self.lock = False
        pass

    def textEdited(self, *param):
        if not self.lock:
            text = gtk.Entry.get_text(self)
            
            try:
                if text:
                    intval = int(text)
                    if intval < 0: raise ValueError
                    if text.strip() != text: raise ValueError
                    pass
                pass
            
            except ValueError:
                self.lock = True
                self.set_text(self.verified)
                self.lock = False
            else:
                self.verified = text
                pass
            pass
    
        return

    def get_text(self):
        text = gtk.Entry.get_text(self)
        if text:
            return int(text)
        else:
            return None
        pass

    def set_text(self, value):
        gtk.Entry.set_text(self, str(value))
        pass
    pass

