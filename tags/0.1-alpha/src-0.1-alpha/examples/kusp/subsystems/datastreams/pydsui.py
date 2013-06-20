"""
:mod:`dsuisession` -- DSUI Sessions for Python
=================================================

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>


"""
from pykusp.devutils.enforcetypes import enforcetypes
from datastreams import pydsui_backend
import cPickle

_DSUI_IS_OPEN = False

def open(filename):
    """
    if not already opened, this will open the binary DSUI log file
    *filename*.
    """
    global _DSUI_IS_OPEN
    if not _DSUI_IS_OPEN:
        pydsui_backend.dstream_open(filename)
        _DSUI_IS_OPEN = True

def close():
    """
    Closes if file opened by :func:`open` (if any).
    """
    global _DSUI_IS_OPEN
    if _DSUI_IS_OPEN:
        pydsui_backend.dstream_close()
        _DSUI_IS_OPEN = False

def event(group_name, event_name, tag=0, extra_data=None):
    pickled_data = cPickle.dumps(extra_data)
    pydsui_backend.dstream_event(group_name, event_name, 
                             tag, pickled_data);
    
def interval_start(group_name, event_name):
    pydsui_backend.dstream_interval_start(group_name, event_name)

def interval_end(group_name, event_name, tag=0):
    pydsui_backend.dstream_interval_end(group_name, event_name, tag)

def histogram_add(group_name, event_name, value):
    pydsui_backend.dstream_histogram_add(group_name, event_name, value)

def counter_add(group_name, event_name, increment=1):
    pydsui_backend.dstream_counter_add(group_name, event_name, increment)


###################################
# Wrapper classes that may prove
# useful.
###################################

class DSUIAbstractObject:
    """
    Definies the basic attributes that all DSUI Logging objects should
    have. This boils down to keeping the group name and event name.
    In the C DSUI interface it would be the GROUP_NAME and EVENT_NAME
    in a statement such as::

        DSTRM_EVENT(GROUP_NAME, EVENT_TAME, TAG)

    The classes that inherit the DSUIAbstractObject will implement
    some type of logging routine wrapper specific to their function. This
    abstract class is merely a container and will not have any of
    those features.

    The motivation behind this is to provide a higher level interface
    (as is the way of Python) that keeps track of the reused
    information for you.
    """

    def __init__(self, group, event):
        self._group_name = str(group)
        self._event_name = str(event)
 
    def get_group_name(self):
        return self._group_name

    def get_event_name(self):
        return self._event_name

        
class DSUIEvent(DSUIAbstractObject):
    """
    Provides the same functionality as :func:`event`, but only
    for a given GROUP_NAME EVENT_NAME pair. 
    """
    def __init__(self, group, event, default_tag=0):
        DSUIAbstractObject.__init__(self, group, event)
        self._default_tag = int(default_tag)

    @enforcetypes(int)
    def log_event(self, tag=None, extra_data=None):
        pickled_data = cPickle.dumps(extra_data)
        if tag is None:
            tag = self._default_tag
        pydsui_backend.dstream_event(self._group_name, self._event_name, 
                             tag, pickled_data);
    

class DSUIHistogram(DSUIAbstractObject):
    def __init__(self, group, event):
        DSUIAbstractObject.__init__(self, group, event)
        
    @enforcetypes([int,long])
    def add(self, value):
        pydsui_backend.dstream_histogram_add(self._group_name, 
                                     self._event_name,
                                     value)

class DSUICounter(DSUIAbstractObject):
    def __init__(self, group, event):
        DSUIAbstractObject.__init__(self, group, event)
    
    def increment(self, incr=1):
        pydsui_backend.dstream_counter_add(self._group_name, 
                                   self._event_name,
                                   incr)


class DSUIInterval(DSUIAbstractObject):
    def __init__(self, group, event, default_tag=0):
        DSUIAbstractObject.__init__(self, group, event)
        self._default_tag = int(default_tag)

    def start(self):
        pydsui_backend.dstream_interval_start(self._group_name, self._event_name)

    @enforcetypes(int)
    def end(self, tag=None):
        if tag is None:
            tag = self._default_tag
        pydsui_backend.dstream_interval_end(self._group_name, self._event_name, tag);
    
