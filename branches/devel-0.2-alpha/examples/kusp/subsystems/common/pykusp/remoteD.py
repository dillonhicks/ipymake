"""

multi-process shared remote dict module - 
remoteD
                     ( aka 'agentsmith' )

Overview:
   provides an easy interface for 'multiprograming'
   that is to say, fork a child each time newProc is called,
   and have that child use a socket to talk to a shared data
   repository... hilarity ensues.

Details:
   A remoteD server process is created by the first call to
   initShare in your script, automatically.

   initShare returns a shareStub object - a network aware
   client to the server that behaves like a dictionary.

   newProc calls on a shareStub object fork a new child proccess,
   the child automatically gets its own shareStub client,
   and starts executions with the function and arguments
  passed to the newProc call.
   the shareStub object in the child is assigned to the variable
   passed as an argument to newProc - most of the time, this will
   be a reference to the current shareStub variable.
   

Copyright 2003, Jonathan M. Franz, NeuroKode Labs, LLC
BSD-style liscense  

"""
import thread, time, pickle, string
import socket, os, select, copy, sys, os.path

## first, some constants required for use by other modules
# socket type to use
UNIXSOCK    = socket.AF_UNIX
IPSOCK      = socket.AF_INET
DEFAULTSOCK = IPSOCK


def initShare(port=7450, sType=DEFAULTSOCK, autoKill=1):
    """
    initShare returns a share object in the calling process, 
    and will fork and start a server.  only call this once.
    """
    if sType not in (UNIXSOCK, IPSOCK, DEFAULTSOCK):
        raise "Bad socket type used"
        
    if sType == IPSOCK:    
        # lets figure out our port
        if port < 1024 or port > 60000:
            raise BadPortNumber, "Port number out of range"
    
        # test to see if port is available
        try:
            sockobj = socket.socket(sType, socket.SOCK_STREAM)  # basic TCP/IP socket server
            sockobj.bind(('', port))  # localhost, port xxx
            sockobj.shutdown(2)
            sockobj.close()
        except:
            raise "Port Number in use"
    else:
        # for a unix socket, test to see if the file exists
        if os.path.exists(str(port)):
            raise "Unix Socket In Use"
        
        
    # if we get here, we're good    
    
    # now fork to create the child and the server
    pid = os.fork()
    if pid == 0:
        # lets create our server
        if sType == IPSOCK:
            createShareServer(('',port), sType, autoKill)
        else:
            createShareServer(str(port), sType, autoKill)
        #time.sleep(25.0) # sleep ten seconds, for top
        #if sType == UNIXSOCK:
            # remove socket file
        # when we get here, things are done and the share server is being shutdown
        
        sys.exit()
    else:
        # this version returns!
        time.sleep(0.03) # sleep to allow for server creation
        
        return stubShare(port, sType)

def createShareServer(socketArgs, sType, autoKill=1):
    if sType not in (UNIXSOCK, IPSOCK, DEFAULTSOCK):
        raise BadSockType, "Bad socket type used"
    # ok, we're gona listen, and then setup to fork each child, create share first.
    Contents = {}
    ShareLock = None
    #Content_Locks = {}
    # now bind to a socket
    serverSock = socket.socket(sType, socket.SOCK_STREAM)  # basic stream server
    serverSock.setblocking(1)
    serverSock.bind(socketArgs)  # localhost, port xxxx, or filename
    serverSock.listen(50)  # upto 50 new connections, for now.
    readables = []
    readables.append(serverSock)
    had_children = 0
    served = 0
    should_die = 0
    socketData = {}
    while 1:  # keep on trucking
        haveData, wantData, haveErr = select.select(readables, [], [], 0.001) # wait for data
        if len(readables) == 1 and had_children == 1 and autoKill == 1 and serverSock not in haveData:
            should_die += 1
            if should_die == 5000:  # wait 5 seconds before dying
                # all children dead, we're supposed to autoKill, and no pending connections, and we _had_ children already
                serverSock.close()
                # if we had a unix socket, time to remove the filesystem entry
                if sType == UNIXSOCK:
                    os.remove(socketArgs)
                print "Sever closing, " + str(len(Contents)) + " keys, " + str(served) + " clients served in lifetime."
                return
        #print ">" + str(haveData), str(wantData), str(haveErr), str(readables)
        for sockobj in haveData:
            if sockobj == serverSock:  # we have a new connection
                #print ">Accepting"
                connection, address = sockobj.accept()  # create child sockobj
                served += 1
                should_die = 0
                #print ">Accepted"
                connection.setblocking(1)
                socketData[connection] = ""
                had_children = 1
                readables.append(connection)
                #print "Server " + str(readables)
            else:
                if ShareLock == None or ShareLock == sockobj:  # we cannot read data from other sockets who do not have the lock!
                    newData = sockobj.recv(4096) # this wont block, but if it returns 0 bytes, it means the socket is closed
                    if not newData:
                        if ShareLock == sockobj:
                            # release lock on socket death
                            ShareLock = None
                        del socketData[sockobj]
                        # officially close
                        sockobj.close()
                        # remove from list
                        readables.remove(sockobj)
                        #print "Server: " + str(readables)
                        
                              
                    else:
                        socketData[sockobj] += newData  # buffer new data
                        
                        # only process if no lock or current sock holds lock
    
                        #socketData[sockobj] += sockobj.recv(4096)     # this wont block, just return whats there
                        if socketData[sockobj][-2:] == "\n\n":  # double \n\n ends the msg, only process if msg complete
                            data = socketData[sockobj]
                            #print ">" + data + "\n("+ str(len(data)) + ")"        
                            
                            data = data[:-2] # remove last two \n\n
                            
                            # first line is always the command, rest is payload, if any
                            Lines = data.split("\n", 1) # maxsplit is 1 time
                            commandLine = Lines[0]
                            payload = string.join(Lines[1:],"\n")
                            
                            # command is first two chars, followed by arg if any
                            command = commandLine[:2]
                            arg = commandLine[2:]
                            oldLock = ShareLock
                            ShareLock = do_command(sockobj, command, arg, payload, ShareLock, Contents) # we may lock
                            
                                # loop through built-up-queue
                                
                                
                            socketData[sockobj] = "" # clean out the data
    
                   
      
        #time.sleep(0.1)
        
def do_command(conn, command, arg, payload, ShareLock, Contents): # do we hold the lock?
    
    ########### we either have the lock, or the lock doesn't exist
    # now, which command did we get?  whats the list again?
    # G as-in Get (an item by key from the server)
    # P as-in Put (an item by key into the server)
    # D as in delete item (by key on the server)
    # H as-in has_key (in the server)                   
    # ? for query share for keys (K is used by the OK result, thus '?' here)
    # L for Lock Share server
    # U for Unlock Share server
    ####
    # most commands short-lock, if needed, and return orig value for isLocked
    # L and U change isLocked!
    err = "" # error string, empty on success
    if command == "G:":     #get key
        if len(arg) > 0:
            try:
                result = Contents[arg]
            except:
                err = "Key Not Found"
        else:
            err = "Key too short or empty"
        if err == "":
            
            #print "res::" + result
            conn.send(result + "\n\n")
        else:
            #print "err:->" + err
            conn.send("\n\n")
        ## done with get
            
    elif command == "P:":   # put key
        if len(arg) > 0:
             #ShareLock.acquire()       
           # try:
           #     data = pickle.loads(payload)
           # except:
           #     err = "Bad pickled data"
           pass
        else:
            err = "Key too short or empty"
        if err == "":
            Contents[arg] = payload
            #print Contents.keys()
            conn.send("K:\n\n")    
        else:
            conn.send(err + "\n\n")
        # end put
        
    elif command == "D:":   # delete key
        if len(arg) > 0:
            try:
                del Contents[arg]
            except:
                err = "Bad Key - does not exist in Contents"
        else:
            err = "Key too short or empty"
        if err == "":
            conn.send("K:\n\n")
        else:
            conn.send(err + "\n\n")
        # end Delete
        
    elif command == "H:":   # has key
        if len(arg) > 0:
            result = Contents.has_key(arg)
        else:
            err = "Key too short or empty"                
        if err == "":
            if result == 0: # its bad
                conn.send("0\n\n")
            else:
                conn.send("1\n\n")
        else:
            conn.send("0\n\n") # error we return no-key
        # end has key
        
    elif command == "?:":   # list keys, one per line
        # no args for this one
        kList = Contents.keys()
        rText = string.join(kList, "\n")
        conn.send(rText + "\n\n")
        # end list keys
   
    elif command == "L:":  # lock the share
        # simpler than it seems, if we are here, we either have the lock
        # of the lock isn't set.
        # set and return
        # a lock when the lock already exists does nothing, and does not report an error
        #print "locked"
        ShareLock = conn
        conn.send("K:\n\n")
    
    elif command == "U:": # unlock
        # simpler than it seems, if we are here, we either have the lock
        # of the lock isn't set.
        # set and return
        # note: an unlock when the lock doesnt exist does not throw and error
        ShareLock = None
        conn.send("K:\n\n")
        #print "unlocked"
    
    return ShareLock
    ### leave rest of commands for later
        
        
            
                  

# this class pretends to be a dict, but really uses pickle
# and a socket to communicate with the parent process

class stubShare:
    def __init__(self, port=7450, sType=DEFAULTSOCK, host=''):
        if sType not in (UNIXSOCK, IPSOCK, DEFAULTSOCK):
            raise BadSockType, "Bad socket type used"
        # lets figure out our port
        if sType == IPSOCK:
            if port < 1024 or port > 60000:
                raise "Port number out of range"
        self.host = host
        self.port = port
        self.sType = sType
        self.sock = socket.socket(sType, socket.SOCK_STREAM)
        self.sock.setblocking(1)
        
        
        if sType == IPSOCK:
            self.sock.connect((host, self.port))
        else:
            self.sock.connect(str(self.port))
        
            
    def __getitem__(self, key):
        # get an item from the share
        
        # if key contains newlines, it will hoark
        ourKey = str(key).replace("\n","\\n")
        # send request
        self.sock.send("G:" + ourKey + "\n\n")  # G as-in Get
        notdone = 0
        data = ""
        # read until we timeout, limit is reached (data is too big!)
        # or we get a end-of-message (two newlines)
        while notdone != 2000: # max tries is 2000, 10 meg basicaly (after pickling)
            data += self.sock.recv(5120)
            if data[-2:] == "\n\n":  # double \n\n ends the msg
                notdone = 2000
            else:
                notdone += 1
        if len(data) == 2:
            raise ShareKeyError, "Share does not contain an item of that name"
        else:
            data = data[:-2]
            #print "::" + data
            data = pickle.loads(data)
            return data

    def __setitem__(self, key, value):
        # put an item in the share,
        # and wait for a ok - this call blocks
        # if key contains newlines, it will hoark
        ourKey = str(key).replace("\n","\\n")
        # need to do a deep cop on value in
        # case it hold references to anything
        data = pickle.dumps(copy.deepcopy(value))                
        #print "<<" + data
        self.sock.send("P:" + ourKey + "\n" + data + "\n\n")    # P as-in Put
        result = self.sock.recv(128)
        if result != "K:\n\n":
            raise CannotWriteError, "Share Server refused write, data: " + result
            #print "Bad Result: " + result
        

    def has_key(self, key):
        # if key contains newlines, it will hoark
        ourKey = str(key).replace("\n","\\n")
        self.sock.send("H:" + ourKey + "\n\n")  # H as-in has_key
        # server will respond with 1 or 0 followed by \n\n
        data = self.sock.recv(128)
        #print "got:[" + data + "]"
        return int(data[:-2])
    
    def keys(self):
        # gets all the keys from the server
        self.sock.send("?:\n\n")    # ? for query share for keys (K is used by the OK result
        notdone = 0
        data = ""
        # read until we timeout, limit is reached (data is too big!)
        # or we get a end-of-message (two newlines)
        while notdone != 2000: # max tries is 2000, 10 meg basicaly of keys
            data += self.sock.recv(5120)
            if data[-2:] == "\n\n":  # double \n\n ends the msg
                notdone = 2000
            else:
                notdone += 1
        data = data[:-2] # remove last two lines
        keys = data.split("\n")
        return keys
    
    def __delitem__(self, key):
        # if key contains newlines, it will hoark
        ourKey = str(key).replace("\n","\\n")
        self.sock.send("D:" + ourKey + "\n\n") # A for delete
        result = self.sock.recv(512)
        if result != "K:\n\n":
            raise CannotLockItem, "Share Item lock refused by server, data: " + result                
            #print result + "[" +  ourKey + "]"
    
    def Lock(self):
        # lock the share for exclusive use
        self.sock.send("L:\n\n")    # L for Lock Share
        result = self.sock.recv(512)
        if result != "K:\n\n":
            raise CannotLockShare, "Share Server refused lock, data: " + result
            
    def Unlock(self):
        self.sock.send("U:\n\n")    # U for Unlock Share
        result = self.sock.recv(512)
        if result != "K:\n\n":
            raise CannotUnLockShare, "Share Server lock not removed! data: " + result
    
    def newProc(self, function, args):
        # ok, we fork, then run passed function
        nuPid = os.fork()
        if nuPid == 0:
            # we're the child
            nuStub = stubShare(self.port, self.sType, self.host)
            # put nuStub at the front of the list
            args.insert(0, nuStub)
            # call the function
            apply(function,args)
            sys.exit()
            
            
class CannotUnlockShare(Exception):
    def __init__(self, value):
        self.value=value
    def __str__(self):
        return repr(self.value)       

class CannotLockItem(Exception):
    def __init__(self, value):
        self.value=value
    def __str__(self):
        return repr(self.value)       

class CannotLockShare(Exception):
    def __init__(self, value):
        self.value=value
    def __str__(self):
        return repr(self.value)       

class CannotWriteError(Exception):
    def __init__(self, value):
        self.value=value
    def __str__(self):
        return repr(self.value)       
        
class ShareKeyError(Exception):
    def __init__(self, value):
        self.value=value
    def __str__(self):
        return repr(self.value)       
                       