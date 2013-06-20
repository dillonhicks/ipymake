from multiprocessing import Process
import os



def f(name):
    print 'start work look for ', name
    dumb = 2.7
    work = 0;
    while work < 100000:
        dumb *= dumb
        work += 1
        if work % 5000 == 0:
            print '[ %s ] Completed %d loops'%(name, work) 
    print 'done ', name

if __name__ == '__main__':
    
    procs = []
    for i in range(0, 200):
        p = Process(target=f, args=('bob - %d'%i,))
        p.start()
        procs.append(p)
        
    for proc in procs:
        proc.join()
    
