from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qc
from sound import SoundMode
from config import Colors

class ColorOption(qt.QWidget):
    def __init__(self, text, color = qc.Qt.white, parent = None):
        qt.QWidget.__init__(self, parent)

        main = qt.QHBoxLayout()
        main.addWidget(qt.QLabel(text, self))

        self.color_name = qt.QLabel(self)
        main.addWidget(self.color_name)

        self.select = qt.QPushButton("Select")
        main.addWidget(self.select)
        self.select.clicked.connect(self.pick_color)

        if not color:
            self.color = qc.Qt.white
        else:
            self.color = color

        self.setLayout(main)

    def pick_color(self):
        new_color = qt.QColorDialog.getColor(self.color, self)

        if not new_color.isValid():
            return

        self.color = new_color

        self.color_name.setText(self.color.name())

class ColorSettings(qt.QWidget):
    def __init__(self, parent):
        qt.QWidget.__init__(self, parent)

        main = qt.QVBoxLayout()

        for c in Colors:
            opt = ColorOption(c.name, None, self)
            main.addWidget(opt)

        self.setLayout(main)

class SoundSettings(qt.QWidget):
    def __init__(self, parent):
        qt.QWidget.__init__(self, parent)

        main = qt.QVBoxLayout()

        label = qt.QLabel("Sound Mode:", self)
        main.addWidget(label)

        full = qt.QRadioButton("Full", self)
        main.addWidget(full)
        full.toggle()

        simple = qt.QRadioButton("Simple", self)
        main.addWidget(simple)

        silent = qt.QRadioButton("Silent", self)
        main.addWidget(silent)

        self.setLayout(main)

class Editor(qt.QWidget):
    def __init__(self):
        qt.QWidget.__init__(self)

        main = qt.QVBoxLayout()

        sections = qt.QVBoxLayout()

        sound = qt.QPushButton("Sound", self)
        sections.addWidget(sound)
        self.sound_settings = SoundSettings(self)
        sound.clicked.connect(lambda: self.__show(self.sound_settings))

        color = qt.QPushButton("Color", self)
        sections.addWidget(color)
        self.color_settings = ColorSettings(self)
        color.clicked.connect(lambda: self.__show(self.color_settings))

        save = qt.QPushButton("Save", self)
        sections.addWidget(save)

        quitb = qt.QPushButton("Quit", self)
        quitb.clicked.connect(qt.qApp.quit)
        sections.addWidget(quitb)

        hbox = qt.QHBoxLayout()
        hbox.addLayout(sections)
        hbox.addWidget(self.sound_settings)
        hbox.addWidget(self.color_settings)

        main.addLayout(hbox)
        self.setLayout(main)

        self.current = self.sound_settings
        self.sound_settings.show()        
        self.color_settings.hide()

    def __show(self, settings):
        self.current.hide()
        settings.show()
        self.current = settings
