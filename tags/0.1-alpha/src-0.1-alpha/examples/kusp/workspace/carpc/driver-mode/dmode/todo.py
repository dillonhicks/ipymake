from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qc
from sound import Button
from util import make_shortcut
from datetime import datetime, date, timedelta
import pickle
import bisect

class Event(object):
    def __init__(self, dt = datetime.now(), desc = "A new event"):
        self.dt = dt
        self.desc = desc

    def datetime(self):
        return self.dt

    def __eq__( self, other ):
        return self.dt == other.dt
    def __lt__( self, other ):
        return self.dt < other.dt
    def __le__( self, other ):
        return self.dt <= other.dt
    def __gt__( self, other ):
        return self.dt > other.dt
    def __ge__( self, other ):
        return self.dt >= other.dt
    def __ne__( self, other ):
        return self.dt != other.dt

class EventLog(object):
    """
    A dictionary of events indexed by day.
    """
    def __init__(self, events = {}):
        self._events = events

    @property
    def events(self):
        return self._events

    def dates(self):
        return self._events.keys()

    def __getitem__(self, date):
        return self._events[date]

    def __contains__(self, date):
        return date in self._events

    def insert(self, event):
        date = event.datetime().date()

        if date in self._events:
            bisect.insort(self._events[date], event)
        else:
            self._events[date] = [event]

    def remove(self, event):
        date = event.datetime().date()

        if date in self._events:
            self._events[date].remove(event)

class DayItem(qt.QListWidgetItem):
    """
    Used to display an event in the todo list.
    """
    def __init__(self, event):
        qt.QListWidgetItem.__init__(self, event.datetime().strftime("%I:%M %p | ") + event.desc)

        self.event = event;

class DayList(qt.QListWidget):

    """
    List a series of events for a day.
    """
    def __init__(self, parent):
        qt.QWidget.__init__(self,  parent)

        self.events = qt.qApp.config().get_events()

        local_config = qt.qApp.local_config()

        if local_config:
            local_config.events_changed.connect(self.__events_changed)

        # Items in the list widget
        self.items = []

        self.date = date.today()

    def save(self):
        qt.qApp.config().set_events(self.events)
        qt.qApp.config().save()

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, date):
        self._date = date
        self.__list_events()

    def insert(self, event):
        self.events.insert(event)

        if self.date == event.datetime().date():
            self.__list_events()

    def remove_selected(self):
        map(self.events.remove, [x.event for x in self.selectedItems()])

        self.__list_events()

    def __events_changed(self, events):
        self.events = events
        self.__list_events()

    def __list_events(self):
        # Remove everything.
        self.clear()

        if self.date in self.events:
            self.items = [DayItem(e) for e in self.events[self.date]]            
            map(self.addItem, self.items)
            
            if self.items:
                self.setCurrentItem(self.items[0])
                self.setItemSelected(self.items[0], True)

class Todo(qt.QWidget):
    """
    Display a list of events for a particular day with prev and next controls.
    """
    def __init__(self, parent):
        qt.QWidget.__init__(self,  parent)

        layout = qt.QVBoxLayout()
        self.setLayout(layout)

        hbox = qt.QHBoxLayout()
        
        prev = Button("<-", "prev.wav", self)
        prev.clicked.connect(self.prev_date)
        hbox.addWidget(prev)

        self.day_label = qt.QLabel(self)
        self.day_label.setAlignment(qc.Qt.AlignCenter)
        hbox.addWidget(self.day_label)

        next = Button("->", "next.wav", self)
        next.clicked.connect(self.next_date)
        hbox.addWidget(next)        

        layout.addLayout(hbox)

        self.event_list = DayList(self)
        layout.addWidget(self.event_list)
        self.setFocusProxy(self.event_list)

        self.ok = qt.QPushButton("Ok", self)
        layout.addWidget(self.ok)

        self.set_date(date.today())

        make_shortcut(qc.Qt.Key_Enter, self.event_list, self.ok.click)
        make_shortcut(qc.Qt.Key_Left, self.event_list, self.prev_date)
        make_shortcut(qc.Qt.Key_Right, self.event_list, self.next_date)

    def set_date(self, day):
        self.event_list.date = day
        self.day_label.setText(self.event_list.date.strftime("%a, %b %d, %Y"))

    def next_date(self):
        self.set_date(self.event_list.date + timedelta(days=1))

    def prev_date(self):
        self.set_date(self.event_list.date - timedelta(days=1))

class EventDialog(qt.QDialog):
    def __init__(self, date, parent):
        qt.QDialog.__init__(self, parent)

        self.setWindowTitle("New Event")

        layout = qt.QVBoxLayout()

        self.dt = qt.QDateTimeEdit(qc.QDateTime(date, qc.QTime.currentTime()), self)
        self.dt.setCalendarPopup(True)
        layout.addWidget(self.dt)
        
        self.desc = qt.QTextEdit("A new event", self)
        layout.addWidget(self.desc)

        button_l = qt.QHBoxLayout()
        ok = qt.QPushButton("OK", self)
        button_l.addWidget(ok)
        ok.clicked.connect(self.ok)

        cancel = qt.QPushButton("Cancel", self)
        button_l.addWidget(cancel)
        cancel.clicked.connect(self.cancel)
        
        layout.addLayout(button_l)

        self.setLayout(layout)

    def ok(self):
        self.event = Event(self.dt.dateTime().toPyDateTime(), self.desc.toPlainText())
        self.accept()

    def cancel(self):
        self.event = None
        self.reject()

    def exec_(self):
        if qt.QDialog.Accepted == qt.QDialog.exec_(self):
            return self.event
        
class Editor(qt.QWidget):
    """
    An editor to create new events.
    """
    def __init__(self):
        qt.QWidget.__init__(self)

        self.setWindowTitle("Todo List")

        layout = qt.QHBoxLayout()

        self.cal = qt.QCalendarWidget(self)
        self.cal.selectionChanged.connect(lambda : self.set_date(self.cal.selectedDate().toPyDate()))
        layout.addWidget(self.cal)

        list_l = qt.QVBoxLayout()
        self.event_list = DayList(self)
        self.event_list.setSelectionMode(qt.QListView.ExtendedSelection)
        self.setFocusProxy(self.event_list)
        list_l.addWidget(self.event_list)

        control_l = qt.QHBoxLayout()
        prev = qt.QPushButton("<-", self)
        control_l.addWidget(prev)
        prev.clicked.connect(self.prev_date)

        new = qt.QPushButton("New", self)
        control_l.addWidget(new)
        new.clicked.connect(self.create_new)

        delete = qt.QPushButton("Delete", self)
        control_l.addWidget(delete)
        delete.clicked.connect(self.event_list.remove_selected)

        next = qt.QPushButton("->", self)
        control_l.addWidget(next)        
        next.clicked.connect(self.next_date)

        save = qt.QPushButton("Save", self)
        control_l.addWidget(save)
        save.clicked.connect(self.event_list.save)

        list_l.addLayout(control_l)
        layout.addLayout(list_l)

        self.set_date(date.today())

        self.setLayout(layout)

        make_shortcut(qc.Qt.Key_Left, self.event_list, self.prev_date)
        make_shortcut(qc.Qt.Key_Right, self.event_list, self.next_date)

    def create_new(self):
        event = EventDialog(self.event_list.date, self).exec_()

        if event:
            self.event_list.insert(event)

    def set_date(self, date):
        self.cal.setCurrentPage(int(date.year), int(date.month))
        self.cal.setSelectedDate(date)
        self.event_list.date = date

    def next_date(self):
        self.set_date(self.event_list.date + timedelta(days=1))

    def prev_date(self):
        self.set_date(self.event_list.date - timedelta(days=1))
