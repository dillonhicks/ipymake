#!/usr/bin/env python
"""PathFinder.py
This module resolves pathnames relative to the 
Python path."""
import sys, os
class Error(Exception):  """Raised when a pathname cannot be resolved."""
def find(pathname):
    """Resolve pathname to a location on the 
    Python path."""
    #print "find"
    if os.path.isabs(pathname):
        return pathname
    for dirname in sys.path:
     #   print dirname
        
        candidate = os.path.join(dirname, pathname)
      #  print candidate
        if os.path.isfile(candidate):
            return candidate
    raise Error("Cannot find %s on the Python path."
                % `pathname`)


def main():
    """Module mainline (for standalone execution)"""
    def testFind(path, expectError=0):
        """Try to resolve path, with diagnostic 
        messages."""
        print "Resolving %s..." % path
        try:
            print find(path)
        except Error, info:
            if expectError:
                print "As expected:", info
            else:
                print "ERROR:", info
                pass
            pass
        pass
    
    # Try to find something known to be on the path, using both
    # relative and absolute paths.
    testFind("socket.py")
    join = os.path.join
    socketPath = join(sys.prefix, join("lib", 
                                       join("python", "socket.py")))
    testFind(socketPath)
    
    # Try to find something which probably  soesn't exist.
    testFind("I_Dont_Exist.nonexistent_path", 1)
    return


if __name__ == "__main__":
    main()
    
    
