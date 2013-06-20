"""
targets.py test file

Not to be implemented yet.

"""

class Target:
    DEPENDENCIES = [ 'Target2' ] 
    CODE_LINES = """
potatos
"""
    def __init__(self):
        self()

    def __call__(self):
        print 'zomg it works'
        print self.CODE_LINES
        for dep in self.DEPENDENCIES:
            TARGETS_BY_NAME[dep]()


class Target3:
    DEPENDENCIES = [ ] 
    CODE_LINES = """
that it works
"""
    def __init__(self):
        self()

    def __call__(self):
        print 'zomg it works'
        print self.CODE_LINES
        for dep in self.DEPENDENCIES:
            dep()



class Target2:
    DEPENDENCIES = [ 'Target3','Target3','Target3' ] 
    CODE_LINES = """
I dont believe
"""
    def __init__(self):
        self()

    def __call__(self):
        print 'zomg it works'
        print self.CODE_LINES
        for dep in self.DEPENDENCIES:
            TARGETS_BY_NAME[dep]()


TARGETS_BY_NAME = {
    'Target3': Target3,
    'Target2':Target2,
    'Target' : Target}



if __name__=="__main__":
    Target()
