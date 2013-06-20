
class DocDict(dict):
    """a dictionary that has a docmentation string for each key,value pair."""
    def __init__(self):
        dict.__init__(self)
        pass
    

    def __setitem__(self, item, value):
        if type(value) is not tuple:
            # we are modifying an existing member, and not changing the docstring
            if item in self:
                value = (value, dict.__getitem__(item)[1])
            else:
                value = (value, "")
                pass
            pass
                
        return dict.__setitem__(self, item, value)

    def __getitem__(self, item):
        return dict.__getitem__(self, item)[0]

    def doc(self, item):
        return dict.__getitem__(self, item)[1]
    pass

