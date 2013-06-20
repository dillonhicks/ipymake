
__all__ = ['Executable','SharedLibrary','StaticLibrary',
           'IncludeFile','ShareFile','PythonPackage']


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
    INCLUDE_FILE = "Include File"
    SHARE_FILE = "Share File"


class Binary:
    def __init__(self, name, sources, options, binary):
        self.name = name
        self.sources = sources
        self.options = options
        self.type = BinaryType.ABSTRACT
        self.binary = binary

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
        return "%s('%s',%s,%s,'%s')" % (class_name, self.name, self.sources, self.options,
                                    self.binary)


    def install(self):
        ip.runlines(["!cp -vf %s $env.binary_install_prefix/%s" % (self.binary, self.name)])
        pass

class Executable(Binary):
    def __init__(self, name, sources, options, binary):
        Binary.__init__(self, name, sources, options, binary)
        self.type = BinaryType.EXECUTABLE        

class SharedLibrary(Binary):
    def __init__(self, name, sources, options, binary):
        Binary.__init__(self, name, sources, options, binary)
        self.type = BinaryType.SHARED_LIBRARY
        
    def install(self):
        ip.runlines(["!cp -vf %s $env.library_install_prefix/%s" % (self.binary, self.name)])
        pass


class StaticLibrary(Binary):
    def __init__(self, name, sources, options, binary):
        Binary.__init__(self, name, sources, options, binary)
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


class PythonPackage:
    def __init__(self, **kwargs):
        self.setup_args = kwargs

    def install(self):
        print "DEBUG: INSTALL PYTHON PACKAGE"
        pass

