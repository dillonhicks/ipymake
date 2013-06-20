"""
:mod:`environment` -- Build Environment Variables
=====================================================

"""
import os
import shelve
import pickle, csv
import shutil

class VerbosityLevels:
    NORMAL             = 0
    VERBOSE            = 1
    VERY_VERBOSE       = 2
    EXTREMELY_VERBOSE  = 3


class DictDB(dict):
    """Alternate DB based on a dict subclass

    Runs like gdbm's fast mode (all writes all delayed until close).
    While open, the whole dict is kept in memory.  Start-up and
    close time's are potentially long because the whole dict must be
    read or written to disk.
    
    Input file format is automatically discovered.
    Output file format is selectable between pickle, json, and csv.
    All three are backed by fast C implementations.
    
    Recipe from Python shelve
    """

    def __init__(self, filename, flag=None, mode=None, format=None, *args, **kwds):
        self.flag = flag or 'c'             # r=readonly, c=create, or n=new
        self.mode = mode                    # None or octal triple like 0x666
        self.format = format or 'pickle'       # csv,  or pickle
        self.filename = filename
        if flag != 'n' and os.access(filename, os.R_OK):
            file = open(filename, 'rb')
            try:
                self.load(file)
            finally:
                file.close()
        self.update(*args, **kwds)

    def sync(self):
        if self.flag == 'r':
            return
        filename = self.filename
        tempname = filename + '.tmp'
        file = open(tempname, 'wb')
        try:
            self.dump(file)
        except Exception:
            file.close()
            os.remove(tempname)
            raise
        file.close()
        shutil.move(tempname, self.filename)    # atomic commit
        if self.mode is not None:
            os.chmod(self.filename, self.mode)

    def close(self):
        self.sync()

    def dump(self, file):
        if self.format == 'csv':
            csv.writer(file).writerows(self.iteritems())
        elif self.format == 'pickle':
            pickle.dump(self.items(), file, -1)
        else:
            raise NotImplementedError('Unknown format: %r' % self.format)

    def load(self, file):
        # try formats from most restrictive to least restrictive
        for loader in (pickle.load, csv.reader):
            file.seek(0)
            try:
                return self.update(loader(file))
            except Exception:
                pass
        raise ValueError('File not in recognized format')



class Environment(DictDB):
    """
    Holds all of the Ipymake environmental variables
    """
    CACHE_FILENAME = './ipymake_cache.db'

    def __init__(self, build_path='./build', prefix="/tmp", binary_prefix="/bin",
		 library_prefix="/lib", share_prefix="/share", 
		 include_prefix="/include", compiled_binaries=[], install_files=[],
		 built_targets={}, verbosity_level=VerbosityLevels.NORMAL, load_from_cache=True ):
	        
        DictDB.__init__(self, filename=self.CACHE_FILENAME)

        if not os.path.exists(self.CACHE_FILENAME) or not load_from_cache:
            self.rpath = lambda path : os.path.realpath(path)
	
	    #paths
            self['build_path'] = build_path
            self['install_prefix'] = prefix
            self['binary_prefix'] = binary_prefix
            self['library_prefix'] = library_prefix #check for lib64?
            self['share_prefix'] = share_prefix
            self['include_prefix'] = include_prefix
	
	    # Compilation
            self['compiled_binaries'] = compiled_binaries
            self['install_files'] = install_files
   
	    # System Parameters
            self['verbosity_level'] = verbosity_level

            

        # House Keeping
        self._built_targets = built_targets
        
        self.install_dirs = [ self.binary_install_path,
                                      self.library_install_path,
                                      self.include_install_path,
                                      self.share_install_path]
    
        
    def get_build_path(self): 
        return self['build_path']
    def set_build_path(self, value): self['build_path'] = value
    build_path = property(get_build_path, set_build_path)

    def get_install_prefix(self): 
        return self['install_prefix']
    def set_install_prefix(self, value): self['install_prefix'] = value
    install_prefix = property(get_install_prefix, set_install_prefix)
    
    def get_binary_prefix(self): 
        return self['install_prefix'] + self['binary_prefix']
    def set_binary_prefix(self, value): self['binary_prefix'] = value
    binary_install_prefix = property(get_binary_prefix, set_binary_prefix)

    def get_library_prefix(self): 
        return self['install_prefix'] + self['library_prefix']
    def set_library_prefix(self, value): self['library_prefix'] = value
    library_install_prefix = property(get_library_prefix, set_library_prefix)
 
    def get_share_prefix(self): 
        return self['install_prefix'] + self['share_prefix']
    def set_share_prefix(self, value): self['share_prefix'] = value
    share_install_prefix = property(get_share_prefix, set_share_prefix)

    def get_include_prefix(self): 
        return self['install_prefix'] + self['include_prefix']
    def set_include_prefix(self, value): self['include_prefix'] = value
    include_install_prefix = property(get_include_prefix, set_include_prefix)

    def get_compiled_binaries(self): return self['compiled_binaries']
    def set_compiled_binaries(self, value): self['compiled_binaries'] = value
    compiled_binaries = property(get_compiled_binaries, set_compiled_binaries)

    def get_install_files(self): return self['install_files']
    def set_install_files(self, value): self['install_files'] = value
    install_files = property(get_install_files, set_install_files)

    def get_built_targets(self): return self._built_targets
    def set_built_targets(self, value): self._built_targets = value
    built_targets = property(get_built_targets, set_built_targets)

    def get_verbosity_level(self): return self['verbosity_level']
    def set_verbosity_level(self, value): self['verbosity_level'] = value
    verbosity_level = property(get_verbosity_level, set_verbosity_level)


    current_build_path = property(lambda self: os.path.realpath(self['build_path']))
    binary_install_path = property(lambda self: os.path.realpath(self['install_prefix'] + self['binary_prefix']))
    library_install_path = property(lambda self: os.path.realpath(self['install_prefix'] + self['library_prefix']))
    include_install_path = property(lambda self: os.path.realpath(self['install_prefix'] + self['include_prefix']))    
    share_install_path =  property(lambda self: os.path.realpath(self['install_prefix'] + self['share_prefix']))        
    

    def __repr__(self):
        binaries_str = '[ ' + ', '.join(map(lambda b: repr(b), self.compiled_binaries))+' ]'
	files_str = '[ ' + ', '.join(map(lambda b: repr(b), self.install_files)) + ' ]'

        return """Environment(build_path=\"%s\", prefix=\"%s\", binary_prefix=\"%s\",
		 library_prefix=\"%s\", share_prefix=\"%s\", 
		 include_prefix=\"%s\", compiled_binaries=\"%s\", install_files=\"%s\",
		 built_targets=%s, verbosity_level=%i )""" % \
	    (self.build_path, self.install_prefix, self.binary_prefix, self.library_prefix,
	     self.share_prefix, self.include_prefix, binaries_str, files_str,
	     self.built_targets, self.verbosity_level)

