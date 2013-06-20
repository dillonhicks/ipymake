#!/bin/env python

import datastreams.dsuisession as dsui
import math
import random

DSUI_LOG_FILE = 'pydsui_example.bin'

dumbloop_interval = dsui.DSUIInterval('FUNC_DUMBLOOP','INTERVAL')
cos_angle_event = dsui.DSUIEvent('FUNC_COSINE','THETA')
cos_value_event = dsui.DSUIEvent('FUNC_COSINE','VALUE')
num_dumb_loops = 50

def dumb_loop():
    dumbloop_interval.start()
    print 'DUMB LOOP ENTER'
    for i in range(100):
        find_cosine(random.random())
    print 'DUMB LOOP LEAVE'
    dumbloop_interval.end()


def find_cosine(angle):
    cos_angle_event.log_event(0, angle)
    cos_angle = math.cos(angle*2.0*math.pi)
    cos_value_event.log_event(0, cos_angle)
    return cos_angle

if __name__ == '__main__':
    dsui.open(DSUI_LOG_FILE)
    print 'Running example with %i dumb loops...' % num_dumb_loops
    for x in range(num_dumb_loops): dumb_loop()
    print 'Closing DSUI, cleaning up...'
    dsui.close()
    print 'Exiting.'
    

