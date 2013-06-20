import sys
import os
from pygsched.gssession import GSSession
import math
import datastreams.dsuisession as dsui

OUTER_LOOP_COUNT = 1
INNER_LOOP_COUNT = 100000
SKIP_COUNT = 1
USE_GS = True

a_event = dsui.DSUIEvent('THREAD0','LOOP_A')
b_event = dsui.DSUIEvent('THREAD1','LOOP_B')
c_event = dsui.DSUIEvent('THREAD2','LOOP_C')
d_event = dsui.DSUIEvent('THREAD3','LOOP_D')
   

def thread_a():
    letter='A'
    for count in range(OUTER_LOOP_COUNT):
        for x in range(INNER_LOOP_COUNT):
            sys.stdout.write(letter)
            a_event.log_event()


def thread_b():
    letter='B'
    for count in range(OUTER_LOOP_COUNT):
        for x in range(INNER_LOOP_COUNT):
            sys.stdout.write(letter)
            b_event.log_event()
    

def thread_c():
    letter='C'
    for count in range(OUTER_LOOP_COUNT):
        for x in range(INNER_LOOP_COUNT):
            sys.stdout.write(letter)
            c_event.log_event()
    
    

def thread_d():
    letter='D'
    for count in range(OUTER_LOOP_COUNT):
        for x in range(INNER_LOOP_COUNT):
            sys.stdout.write(letter)
            d_event.log_event()
    



if __name__ == '__main__':
    dsui.open('python_gsched.bin')

    if USE_GS:
        gsched = GSSession()
        gsched.create_group('pa_sched', 'sdf_rr')
        gsched.install_group('pa_sched')
        pid = os.getpid()        
        
        gsched.add_pid_to_group('pa_sched', pid, 'thread-d')
     
    pid = os.fork()
    if pid == 0:
        thread_a()
        
    else:
        if USE_GS:
            
            gsched.add_pid_to_group('pa_sched', pid, 'thread-a')
            
        pid = os.fork()
        if pid == 0:
            
            thread_b()
            
        else:
            if USE_GS:
                
                gsched.add_pid_to_group('pa_sched', pid, 'thread-b')
                

            pid = os.fork()
            if pid == 0:
                thread_c()

                
            else:
                if USE_GS:
                    
                    gsched.add_pid_to_group('pa_sched', pid, 'thread-c')
                   
                    
                thread_d()
                


    dsui.close()
