from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qc
from sound import *
from music import *
from todo import *
from util import make_shortcut
from datetime import datetime
from threading import Timer
from time import mktime
import sys

class MainMenu(qt.QWidget):
    def __init__(self, parent):
        qt.QWidget.__init__(self, parent)

        music_l = qt.QVBoxLayout()
        controls_l = qt.QHBoxLayout()
        tp_l = qt.QHBoxLayout()

        self.vctrl = VolumeControl(self)
        controls_l.addWidget(self.vctrl)
        self.setFocusProxy(self.vctrl)

        self.prev = Button("<", "previous_track.wav", self)
        controls_l.addWidget(self.prev)

        self.play = Button("|>", "play.wav", self)
        controls_l.addWidget(self.play)

        self.pause = Button("| |", "pause.wav", self)
        controls_l.addWidget(self.pause)

        self.next = Button(">", "next_track.wav", self)
        controls_l.addWidget(self.next)
        
        music_l.addLayout(controls_l)

        self.track = Button("Track", "pick_track.wav", self)
        tp_l.addWidget(self.track)

        self.playlist = Button("Playlist", "pick_playlist.wav", self)
        tp_l.addWidget(self.playlist)
        
        music_l.addLayout(tp_l)
        
        self.todo = Button("Todo", "todo.wav", self)
        self.quit = Button("Quit", "quit.wav", self)

        # Oddly with numlock off, key_0 on the numeric pad comes out as key_insert
        make_shortcut(qc.Qt.Key_Insert, self, self.quit.click)
        
        self.quit.clicked.connect(qt.qApp.quit)

        vbox = qt.QVBoxLayout()
        vbox.addLayout(music_l)
        vbox.addWidget(self.todo)
        vbox.addWidget(self.quit)

        # Shortcuts to help with keyboard navigation
        make_shortcut(qc.Qt.Key_Down, self.vctrl, self.track.setFocus)
        make_shortcut(qc.Qt.Key_Up, self.track, self.vctrl.setFocus)
        make_shortcut(qc.Qt.Key_Down, self.prev, self.playlist.setFocus)
        make_shortcut(qc.Qt.Key_Down, self.play, self.playlist.setFocus)
        make_shortcut(qc.Qt.Key_Down, self.pause, self.playlist.setFocus)
        make_shortcut(qc.Qt.Key_Down, self.next, self.playlist.setFocus)
        make_shortcut(qc.Qt.Key_Up, self.playlist, self.prev.setFocus)
        make_shortcut(qc.Qt.Key_Down, self.track, self.todo.setFocus)
        make_shortcut(qc.Qt.Key_Up, self.todo, self.track.setFocus)        
        self.setLayout(vbox)

MSECS_IN_SEC = 1000

class Clock(qt.QLabel):
    """
    GUI clock that updates itself using a timer
    """
    def __init__(self,  parent):
        qt.QLabel.__init__(self,  parent)

        timer = qc.QTimer(self)

        self.update_time()

        timer.timeout.connect(self.update_time)

        timer.start(MSECS_IN_SEC)

    def update_time(self):
        self.setText(qc.QDateTime.currentDateTime().toString("ddd, MMM d, h:m AP"))

        self.update()

class HUD(qt.QFrame):
    """
    Always displayed information.
    """

    def __init__(self,  parent):
        qt.QFrame.__init__(self,  parent)
        self.setFrameStyle(qt.QFrame.Panel | qt.QFrame.Raised)
        self.setLineWidth(2)

        pal = self.palette();
        pal.setColor(self.backgroundRole(), qc.Qt.blue);
        self.setPalette(pal);

        self.setAutoFillBackground( True )

        layout = qt.QVBoxLayout()

        layout.addWidget(Clock(self))

        self.music = qt.QLabel(self)
        layout.addWidget(self.music)

        self.event_label = qt.QLabel(self)
        layout.addWidget(self.event_label)

        self.setLayout(layout)

        self.player = None

        self.update_event(qt.qApp.config().get_events())

        qt.qApp.local_config().events_changed.connect(self.update_event)

        timer = qc.QTimer(self)

        timer.timeout.connect(self.update_music)

        timer.start(MSECS_IN_SEC)

    def set_player(self, player):
        self.player = player

    def update_music(self):
        if not self.player:
            return

        title = self.player.get_meta_title()
        
        if not title:
            return
        
        if self.player.playlist:
            self.music.setText("%s: %s - %s" % 
                               (self.player.playlist, 
                                self.player.get_meta_artist(), 
                                title))
        else:
            self.music.setText("%s - %s" % 
                               (self.player.get_meta_artist(), 
                                title))

    def find_next_event(self, events):

        today = datetime.now()
        today_event = Event(today, '')
        td = today.date()

        later_events = []

        # Get all eligble events in sorted order and put them in a list
        map(later_events.extend, [events[k] for k in sorted(events.dates()) if k >= td])

        i = bisect.bisect_left(later_events, today_event)
        
        if i < len(later_events):
            return later_events[i]
        else:
            return None

    def update_event(self, events):
        event = self.find_next_event(events)

        if not event:
            self.event_label.setText("")
            return

        self.event_label.setText(event.datetime().strftime("%a, %b %d, %I:%M %p ") + event.desc)

        # Use python timer for events becuase it has a longer max duration(I think)
        self.event_timer = Timer(mktime(event.datetime().timetuple()) - 
                                 mktime(datetime.now().timetuple()), 
                                 self.update_event)
        self.event_timer.start()

class DriverMode(qt.QWidget):
    """
    Top level widget that drives the application.
    """
    def __init__(self):
        qt.QWidget.__init__(self)
                
        self.menu = MainMenu(self)

        self.track_select = None

        self.playlist_select = None

        self.event_list = None

        self.gps = None

        self.player = Player()

        self.menu.vctrl.set_player(self.player)

        self.menu.next.clicked.connect(self.player.next)

        self.menu.prev.clicked.connect(self.player.prev)

        self.menu.play.clicked.connect(self.player.pause)

        self.menu.pause.clicked.connect(self.player.pause)

        self.menu.track.clicked.connect(self.__pick_track)
        
        self.menu.playlist.clicked.connect(self.__pick_playlist)

        self.menu.todo.clicked.connect(self.__show_events)

        self.state = self.menu

        self.box = qt.QVBoxLayout()

        self.display = HUD(self)
        self.box.addWidget(self.display)
        self.display.set_player(self.player)

        self.box.addWidget(self.menu)

        self.setLayout(self.box)

        self.setWindowTitle("driver-mode")

        self.showMaximized()

    def __change_state(self, new_state):
        self.state.hide()
        self.state = new_state
        new_state.show()
        new_state.setFocus()

    def __pick_track(self):
       if not self.track_select:
            self.track_select = TrackSelector(self)
            self.track_select.cancel.clicked.connect(self.__exit_pick_track)
            self.track_select.ok.clicked.connect(self.__exit_pick_track)
            self.box.addWidget(self.track_select)

       self.__change_state(self.track_select)

    def __exit_pick_track(self):
        if self.track_select.selection():
            self.player.loadfile(self.track_select.selection().filePath())

        self.__change_state(self.menu)

    def __pick_playlist(self):
       if not self.playlist_select:
            self.playlist_select = PlaylistSelector(self)
            self.playlist_select.cancel.clicked.connect(self.__exit_pick_playlist)
            self.playlist_select.ok.clicked.connect(self.__exit_pick_playlist)
            self.box.addWidget(self.playlist_select)

       self.__change_state(self.playlist_select)

    def __exit_pick_playlist(self):
        if self.playlist_select.selection():
            self.player.loadlist(str(self.playlist_select.selection().filePath()))

        self.__change_state(self.menu)

    def __show_events(self):
        if not self.event_list:
            self.event_list = Todo(self)
            self.event_list.ok.clicked.connect(self.__exit_show_events)
            self.box.addWidget(self.event_list)

        self.__change_state(self.event_list)

    def __exit_show_events(self):
        self.__change_state(self.menu)
