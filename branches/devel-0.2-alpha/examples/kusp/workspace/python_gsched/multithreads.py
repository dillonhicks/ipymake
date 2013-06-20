import os
import sys
from time import sleep
from threading import Thread, Event
from pygsched.gssession import GSSession
import datastreams.pydsui as dsui



class ExampleThread(Thread):
    LOOP_COUNT = 100000
    def __init__(self, suffix, syncevent):
        Thread.__init__(self, name='pyThread-%s'%suffix)
        self.letter = suffix
        self.counter = dsui.DSUICounter(self.getName(), 'COUNTER')
        self.interval = dsui.DSUIInterval(self.getName(), 'INTERVAL')
        self.event = dsui.DSUIEvent(self.getName(), 'FUNC_RUN')
        self.syncevent = syncevent 
#        print id(syncevent)

    def run(self):

#        dsui.open('multithreads-%s.bin'%self.letter)
        
    #    self.interval.start()
        
        if _USE_GSCHED:
            pid = os.getpid()
            member_name = self.getName()
            gsched.add_pid_to_group(GROUP, pid, member_name)
        
        for cnt in range(self.LOOP_COUNT):
   #         self.counter.increment()
  #          self.event.log_event()
            sys.stdout.write(self.letter)

#
#         self.interval.end()
 #       dsui.close()
        
if __name__ == '__main__':

    from string import ascii_uppercase
    global _USE_GSCHED
    _USE_GSCHED = False


    event = Event()
    global NUM_THREADS
    MAX_NUM_THREADS = 5
    global NUM_THREADS
    NUM_THREADS = 0
    NUM_EXIT = 0
    if _USE_GSCHED:
        global gsched
        gsched = GSSession()
        global GROUP_NAME
        GROUP = 'py_mulitthread_group'
        SCHEDULE = 'sdf_rr'
        gsched.create_group(GROUP, SCHEDULE)

    for i in range(MAX_NUM_THREADS):
        NUM_THREADS += 1
        id = ascii_uppercase[i]
        pid = os.fork()
        if pid == 0:
            print 'Creating Thread', id
            e_thread = ExampleThread(id, event)     
            e_thread.run()
            print 'Exiting....'
            NUM_EXIT += 1
            print NUM_EXIT
            sys.exit()
        else:
            continue
    
    event.set()
    

