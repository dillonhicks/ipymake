#
# $Id: doubledict.py,v 1.4 2004/11/17 23:27:19 boie Exp $
#
# AUTHOR(s):  Andrew Boie
#
# Copyright 2003(C), The University of Kansas
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

class AttributeDict(dict):
    def __init__(self):
        dict.__init__(self)
        self.metadata = {}
        pass
    pass


class MultiDict(dict):
    def __init__(self, types):
        self.types = types
        self.maps = []
        for type in self.types:
            self.maps.append({})
            pass
        dict.__init__(self)
        pass

    def __setitem__(self, item, value):

        # used for correctness checking
        # item is a tuple of keys. each of these keys
        # maps to a full key definition in self.maps
        # the keys in item must be either found in *all* maps
        # or none of them, and if present must all map to the same
        # composite key.
        newitem = False
        olditem = None

        # checking phase
        for index in range(len(item)):
            key = item[index]
            if key not in self.maps[index]:
                newitem = True
                if olditem:
                    # we were able to define the olditem key in an earlier
                    # loop iteration, so it is incorrect for this key to be missing.
                    # if one of the keys maps, they all should.
                    raise KeyError, "key "+`item`+" partially matches "+`olditem`
                pass
            else:
                testval = self.maps[index][key]
                if newitem:
                    raise KeyError, "key "+`item`+" partially matches "+`testval`
                
                if olditem:
                    if olditem != testval:
                        # all the keys should map to the same olditem value
                        # do I even need to check this?
                        raise KeyError, "key "+`key`+" in "+`item`+" maps to " +\
                              `testval` + " but earlier keys mapped to " +\
			      `olditem`
                    pass
                else:
                    olditem = testval
                    pass
                pass
            pass

        # if we reach this point then the parameters should be good. update the maps.
        for index in range(len(item)):
            self.maps[index][item[index]] = item
            pass

        #print self.maps
        
        return dict.__setitem__(self, item, value)
    
    def __getitem__(self, item):
       	item = self._convertitem(item)
        return dict.__getitem__(self, item)
    
    def __contains__(self, item):
        try:
            item = self._convertitem(item)
        except Exception:
            return False
        return dict.__contains__(self, item)

    # private method
    # if the user passes in only one key, rather than the full composite key,
    # convert it to a full composite key by examining the type and looking in self.maps
    def _convertitem(self, item):
	if type(item) is not tuple:
		try:
			typeindex = self.types.index(type(item))
		except ValueError, ex:
			raise KeyError("Unsupported index `"+`type(item)`+"`; only allowed "+`self.types`)
		item = self.maps[typeindex][item]
		pass
        return item
    
    def __delitem__(self, item):
        item = self._convertitem(item)

        for index in range(len(item)):
            del self.maps[index][item[index]]
            pass
                
        return dict.__delitem__(self, item)
    pass

class NSDict(MultiDict):
    def __init__(self):
        MultiDict.__init__(self, [str, int])
        self.metadata = {}
        pass
    pass
