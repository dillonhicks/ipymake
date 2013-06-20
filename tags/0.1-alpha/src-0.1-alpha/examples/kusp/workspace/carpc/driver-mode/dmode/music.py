from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qc
from sound import *
from picker import FilePicker
from util import make_shortcut
from pymplayer import MPlayer
import struct
from subprocess import PIPE

tracks = "/dmode/music"
playlists = "/dmode/playlist"

class VolumeControl(qt.QWidget):
    """
    Widget to control the volume.
    """

    def __init__(self, parent):
        qt.QWidget.__init__(self,  parent)

        self.label = qt.QLabel(self)
        self.label.setAlignment(qc.Qt.AlignCenter)
        self.label.setFrameStyle(qt.QFrame.Panel | qt.QFrame.Sunken)

        hbox = qt.QHBoxLayout()

        self.down = Button("-", "volume_down.wav", self)
        hbox.addWidget(self.down)
        self.setFocusProxy(self.down)

        hbox.addWidget(self.label)

        self.up = Button("+", "volume_up.wav", self)
        hbox.addWidget(self.up)

        self.setLayout(hbox)

    def set_player(self, player):
        self.player = player
        self.label.setText(`self.player.volume`)

        self.down.clicked.connect(self.__volume_down)
        self.up.clicked.connect(self.__volume_up)

    def __volume_down(self):
        self.player.volume_down()
        self.label.setText(`self.player.volume`)

    def __volume_up(self):
        self.player.volume_up()
        self.label.setText(`self.player.volume`)

    def keyPressEvent(self, event):
        print "key pressed volume control"

search_dirs = {"Home" : qc.QDir.homePath(), "External Media" : "/media"}
music_files = ["*.mp3", "*.wav", "*.wmv", "*.ogg"]

class TrackSelector(FilePicker):
    
    def __init__(self, parent):
        FilePicker.__init__(self, "Music", search_dirs, music_files, parent)

playlist_files = ["*.m3u"]
class PlaylistSelector(FilePicker):
    def __init__(self, parent):
        FilePicker.__init__(self, "Playlists", search_dirs, playlist_files, parent)

class Player(MPlayer):
    """
    Handle playback using MPlayer.
    """

    MIN_VOL = 0
    MAX_VOL = 100

    def __init__(self):
        # Genereate methods for mplayer commands
        MPlayer.introspect()

        # Don't need infrared support
        MPlayer.__init__(self, ["-nolirc"])

        # stdout needs to be PIPE to get return values from queries
        self.start(stdout = PIPE)

        self.volume = 50

        self._playlist = None

    def loadfile(self, f):
        MPlayer.loadfile(self, f)
        self._playlist = None

    def loadlist(self, f):
        MPlayer.loadlist(self, f)
        self._playlist = qc.QFileInfo(f).baseName()

    @property
    def playlist(self):
        return self._playlist

    def next(self):
        self.pt_step(1)

    def prev(self):
        self.pt_step(-1)

    def pause(self):
        MPlayer.pause(self)

    @property
    def volume(self):
        return self.__volume

    @volume.setter
    def volume(self, val):
        self.__volume = min(Player.MAX_VOL, max(Player.MIN_VOL, val))
        MPlayer.volume(self, float(self.__volume), 1)

    def volume_up(self):
        self.volume += 10

    def volume_down(self):
        self.volume -= 10

    def __del__(self):
        self.quit()
