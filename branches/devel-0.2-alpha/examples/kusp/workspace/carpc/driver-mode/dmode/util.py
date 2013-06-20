from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qc
import os, sys, logging

def ambigious_shortcut():
    logging.warning("ambigious shortcut occurred")
    pass

class Shortcut(qt.QShortcut):
    first_shortcut = False

    def __init__(self, key, parent, slot):
        qt.QShortcut.__init__(self, key, parent, slot, ambigious_shortcut)
        self.setContext(qc.Qt.WidgetWithChildrenShortcut)

    def event(self, e):
        # Not very pretty but it allows the sound button to know when
        # at least one shortcut has been used.
        Shortcut.first_shortcut = True
        return qt.QShortcut.event(self, e)

def make_shortcut(key, parent, slot):
    # Oddly, specifying the context in the constructor causes a crash.
    shortcut = Shortcut(qt.QKeySequence(key), parent, slot)
    return shortcut

def find_resources(res_type):
    return [x + "/dmode/"+res_type+"/" for x in sys.path if os.path.exists(x + "/dmode/"+res_type)][0]

