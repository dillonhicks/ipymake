"""
:mod:`ipymake.production` -- Classes for handling build files
================================================================

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>

"""

__all__ = ['Executable','SharedLibrary','StaticLibrary',
           'IncludeFile','ShareFile','PythonPackage']
from distutils.core import setup
from stat import ST_MTIME # Stat modification time index for os.stat
from os import stat, path


from IPython import ipapi
ip = ipapi.get()

class BinaryType:
    """
    Just the names of each of the type of compiled binary/install file
    types as defined constants.
    """
    ABSTRACT = "ABSTRACT"
    EXECUTABLE = "Executable"
    SHARED_LIBRARY = "Shared Library"
    STATIC_LIBRARY = "Static Library"

class FileType:
    """
    The different types of install files.
    """
    INCLUDE_FILE = "Include File"
    SHARE_FILE = "Share File"

class SourceFile:
    """
    Provides a little higher abstraction for source files and provides
    a modification timestamp.
    """
    def __init__(self, path, mod_time=None):
        self._path = path
        self._mod_time = mod_time
        if self._mod_time is None:
            self._mod_time = stat(path)[ST_MTIME]
        
    def get_name(self): return path.basename(self._path)
    name = property(get_name)

    def get_path(self): return self._path
    path = property(get_path)

    def get_mod_time(self): return self._mod_time
    modification_time = property(get_mod_time)

    def __str__(self):
        return self.name

    def __repr__(self):
        class_name = self.__class__.__name__
        return '%s(%s,%s)' % (class_name, repr(self.path), repr(self.modification_time))

    def has_changed(self):
        if path.exists(self.path):
           new_mod_time = stat(self.path)[ST_MTIME]
           if new_mod_time == self.modification_time:
               return False
        return True

    def needs_recompile(self):
        return self.has_changed()


class ObjectFile(SourceFile):
    def __init__(self, ofpath, srcfile, mod_time=None):
        SourceFile.__init__(self, ofpath, mod_time)
        if not isinstance(srcfile, SourceFile):
            self._source_file = SourceFile(srcfile)
        else:
            self._source_file = srcfile

    def needs_recompile(self):
        return self._source_file.needs_recompile() or \
            not path.exists(self.path)


    def __repr__(self):
        class_name = self.__class__.__name__
        return "%s(%s, %s, %s)" % (class_name, repr(self.path), 
                                   repr(self._source_file), repr(self.modification_time))

class Binary:
    def __init__(self, name, sources, objfiles, options, binary):
        NAME, EXTENTION = range(2)
        self.name = name
        self.source_files = []
        self.sources = []
        for ofile, sfile in zip(objfiles, sources):
            srcfile_obj = SourceFile(sfile)
            self.source_files.append(srcfile_obj)
            self.sources.append(ObjectFile(ofile, srcfile_obj))

        self.options = options
        self.type = BinaryType.ABSTRACT
        self.binary = binary

    def needs_recompile(self):
        return any( map(lambda ofile: ofile.needs_recompile(), self.sources))

    def __str__(self):
        return \
"""
%s : %s
------------------------------------

BINARY     : %s
SOURCES    : %s
OPTIONS    : %s
""" % (self.type, self.name, self.binary,
       ', '.join(self.sources), '\n\t '.join([ str(ip) for ip in self.options.items()]))

    def __repr__(self):
        class_name = self.__class__.__name__
        return "%s(%s,%s,%s,%s)" % (class_name, repr(self.name), 
                                    repr(self.sources), repr(self.options),
                                    repr(self.binary))


    def install(self):
        ip.runlines(["!cp -vf %s $env.binary_install_prefix/%s" % (self.binary, self.name)])
        pass

class Executable(Binary):
    def __init__(self, name, sources, objfiles, options, binary):
        Binary.__init__(self, name, sources, objfiles, options, binary)
        self.type = BinaryType.EXECUTABLE        

class SharedLibrary(Binary):
    def __init__(self, name, sources, objfiles, options, binary):
        Binary.__init__(self, name, sources, objfiles, options, binary)
        self.type = BinaryType.SHARED_LIBRARY
        
    def install(self):
        ip.runlines(["!cp -vf %s $env.library_install_prefix/%s" % (self.binary, self.name)])
        pass


class StaticLibrary(Binary):
    def __init__(self, name, sources, objfiles, options, binary):
        Binary.__init__(self, name, sources, objfiles, options, binary)
        self.type = BinaryType.STATIC_LIBRARY

    def install(self):
        ip.runlines(["!cp -vf %s $env.library_install_prefix/%s" % (self.binary, self.name)])
        pass
        

class InstallFile:
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.type = BinaryType.ABSTRACT

    def __str__(self):
        return \
"""
%s : %s
------------------------------------

LOCATION : %s
""" % (self.type, self.name, self.location)



class IncludeFile(InstallFile):
    def __init__(self, name, location):
       InstallFile.__init__(self, name, location)
       self.type = FileType.INCLUDE_FILE

    def install(self):
        ip.runlines(["!cp -vf %s $env.include_install_prefix" % self.location])
        pass



class ShareFile(InstallFile):
    def __init__(self, name, location):
       InstallFile.__init__(self, name, location)
       self.type = FileType.SHARE_FILE

    def install(self):
        ip.runlines(["!cp -vf %s $env.share_install_prefix" % self.location])
        pass



import sys
class PythonPackage:
    def __init__(self, **kwargs):
        self.setup_args = kwargs
        self.name = self.setup_args['name']
        

    def install(self):
        print 'DEBUG: Install Python Package '+self.name
       # tmp_args = sys.argv
       # sys.argv = [self.name + '.install()', 'install', '--prefix=/tmp']
       # setup(**self.setup_args)
       # sys.argv = tmp_args
        pass

