

# be prepared to catch these
class ParseException(Exception):
    def __init__(self, line, message):
        Exception.__init__(self, str(line)+": "+message)
        self.line = line 
        self.message = message
        pass
    pass

class SemanticException(Exception):
    def __init__(self, data, message):
        Exception.__init__(self, str(data)+"\n"+message)
        self.data = data 
        self.message = message
        pass
    pass
