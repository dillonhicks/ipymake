import os
import sys
from pygsched.gssession import GSSession

if __name__ == '__main__':
    from string import ascii_uppercase
    global _USE_GSCHED
    _USE_GSCHED = True
    global NUM_THREADS
    MAX_NUM_THREADS = 4
    global NUM_THREADS
    NUM_THREADS = 0
    NUM_EXIT = 0
    if _USE_GSCHED:
        global gsched
        gsched = GSSession()
        global GROUP_NAME
        GROUP = 'py_mulitthread_group'
        SCHEDULE = 'sdf_seq'
        gsched.create_group(GROUP, SCHEDULE)

    for i in range(MAX_NUM_THREADS):
        NUM_THREADS += 1
        id = ascii_uppercase[i]
        pid = os.fork()
        if pid == 0:
            print 'Creating Thread', id
            if _USE_GSCHED:
                pid = os.getpid()
                gsched.add_pid_to_group('py_multithread_group', pid, 'Thread-%s'%id)
                #gsched.thread_set_exclusive(pid)
            os.execl('pygame_thread.py')
        else:
            continue
    
    
    os.wait()
