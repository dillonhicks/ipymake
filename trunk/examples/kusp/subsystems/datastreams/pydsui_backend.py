# This file was automatically generated by SWIG (http://www.swig.org).
# Version 1.3.40
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.
# This file is compatible with both classic and new-style classes.

from sys import version_info
if version_info >= (2,6,0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_pydsui_backend', [dirname(__file__)])
        except ImportError:
            import _pydsui_backend
            return _pydsui_backend
        if fp is not None:
            try:
                _mod = imp.load_module('_pydsui_backend', fp, pathname, description)
            finally:
                fp.close()
            return _mod
    _pydsui_backend = swig_import_helper()
    del swig_import_helper
else:
    import _pydsui_backend
del version_info
try:
    _swig_property = property
except NameError:
    pass # Python < 2.2 doesn't have 'property'.
def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "thisown"): return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static) or hasattr(self,name):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    if (name == "thisown"): return self.this.own()
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError(name)

def _swig_repr(self):
    try: strthis = "proxy of " + self.this.__repr__()
    except: strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0



def dstream_close():
  return _pydsui_backend.dstream_close()
dstream_close = _pydsui_backend.dstream_close

def dstream_open(*args):
  return _pydsui_backend.dstream_open(*args)
dstream_open = _pydsui_backend.dstream_open

def dstream_print(*args):
  return _pydsui_backend.dstream_print(*args)
dstream_print = _pydsui_backend.dstream_print

def dstream_event(*args):
  return _pydsui_backend.dstream_event(*args)
dstream_event = _pydsui_backend.dstream_event

def dstream_histogram_add(*args):
  return _pydsui_backend.dstream_histogram_add(*args)
dstream_histogram_add = _pydsui_backend.dstream_histogram_add

def dstream_counter_add(*args):
  return _pydsui_backend.dstream_counter_add(*args)
dstream_counter_add = _pydsui_backend.dstream_counter_add

def dstream_interval_start(*args):
  return _pydsui_backend.dstream_interval_start(*args)
dstream_interval_start = _pydsui_backend.dstream_interval_start

def dstream_interval_end(*args):
  return _pydsui_backend.dstream_interval_end(*args)
dstream_interval_end = _pydsui_backend.dstream_interval_end


