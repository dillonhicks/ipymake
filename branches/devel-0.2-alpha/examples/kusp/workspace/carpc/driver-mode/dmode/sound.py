from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qc
from datetime import datetime
import pygame
from util import find_resources, Shortcut
import os.path

pygame.init()

pygame.mixer.init()

sound_dir = find_resources("sounds")

sounds = {}

bleep = pygame.mixer.Sound(sound_dir + "bleep.wav")

class SoundMode(object):
    SILENT = 0
    SIMPLE = 1
    FULL = 2

def load_sound(name):
    if name in sounds:
        return sounds[name]
    else:
        if not os.path.isfile(sound_dir + name):
            return None
        else:
            sounds[name] = pygame.mixer.Sound(sound_dir + name)
            return sounds[name]

class Button(qt.QPushButton):
    """
    A button that plays a sound when it receives focus.
    """

    # When the driver mode software starts up, the first button will receive the focus
    # and play its sound. This is somewhat annoying, particularly since gpsdrive makes
    # the sound play twice when both open at startup. Instead, wait until the user
    # does something once before starting to play sounds.
    key_event = False

    def __init__(self, text, sound, parent = None):
        qt.QPushButton.__init__(self, text, parent)

        qt.QShortcut(qt.QKeySequence(qc.Qt.Key_Enter), self, self.click).setContext( qc.Qt.WidgetWithChildrenShortcut)

        self.sound = load_sound(sound)

    def focusInEvent(self, event):
        # Unfortunately, shortcuts block key presses from being delievered.
        # This hack identifies when any of the shortcuts has been used for the first
        # time.

        if self.sound and (Button.key_event or Shortcut.first_shortcut):
            self.sound.play()

        qt.QPushButton.focusInEvent(self, event)

    def keyPressEvent(self, event):
        Button.key_event = True

        qt.QPushButton.keyPressEvent(self, event)

        # Delete this method to save on cpu. It only needs to run once.
        del Button.keyPressEvent
