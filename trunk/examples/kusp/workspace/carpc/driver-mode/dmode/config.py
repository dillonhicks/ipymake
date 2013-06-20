from PyQt4 import QtCore as qc
from sound import SoundMode
from todo import EventLog
import os, threading, SimpleXMLRPCServer, pickle, xmlrpclib

home_dir = os.path.expanduser("~")

config_file = home_dir + "/" + "config.pkl"

class ColorStyle(object):
    def __init__(self, name, style):
        self.name = name
        self.style = style

    def __str__(self):
        return self.name

Colors = [ 
    ColorStyle('button bg','style'),
    ColorStyle('button fg','style'),
    ColorStyle('button focus bg','style'),
    ColorStyle('button focus fg','style')
    ]

class Store(object):
    """
    Simple object that is primarily data for pickling.
    """
    def __init__(self):
        self.events = EventLog()
        self.colors = {}
        for color in Colors:
            self.colors[color.name] = None

        self.sound_mode = SoundMode.FULL

    def set_color(self, name, color):
        self.color[name] = color

    def get_color(self, name):
        return self.color[name]
   
    def set_events(self, events):
        self.events = events

    def get_events(self):
        return self.events

class Config(qc.QObject):
    """
    QObject causes a segmentation fault when it is pickled.
    Therefor, this object contains a data object which is a pure python object
    and that object is used for pickling.
    """
    color_changed = qc.pyqtSignal(object, object)
    events_changed = qc.pyqtSignal(object)

    def __init__(self):
        qc.QObject.__init__(self)

        try:
            f = open(config_file, 'rb')
            self.store = pickle.load(f)
            f.close()
        except IOError:
            self.store = Store()

    def set_color(self, name, color):
        self.store.set_color(name, color)
        self.color_changed.emit(name, color)

    def get_color(self, name):
        return self.store.get_color(name)

    def set_events(self, events):
        self.store.set_events(pickle.loads(events))
        self.events_changed.emit(events)

    def get_events(self):
        return pickle.dumps(self.store.get_events())

    def save(self):
        f = open(config_file, 'wb')
        pickle.dump(self.store, f)
        f.close()

class RemoteConfig(object):
    """
    Wraps xml rpc methods on the client side.
    """
    def __init__(self, address, port):
        self.proxy = xmlrpclib.ServerProxy('http://'+str(address)+':'+str(port), allow_none=True)

    def set_color(self, name, color):
        self.proxy.set_color(name, color)

    def get_color(self, name):
        return self.proxy.get_color(name)

    def set_events(self, events):
        self.proxy.set_events(pickle.dumps(events))

    def get_events(self):
        return pickle.loads(self.proxy.get_events())

    def save(self):
        self.proxy.save()

class ConfigServer(threading.Thread):
    def __init__(self, config, port):
        threading.Thread.__init__(self)
        self.port = port
        self.config = config

    def run(self):
        self.server = SimpleXMLRPCServer.SimpleXMLRPCServer(("localhost", self.port), allow_none=True)
        self.server.register_instance(self.config)
        self.server.serve_forever()
