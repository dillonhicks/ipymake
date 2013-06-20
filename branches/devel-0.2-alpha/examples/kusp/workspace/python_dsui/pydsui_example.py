#!/bin/env python

import datastreams.pydsui as dsui
import math
import random

DSUI_LOG_FILE = 'pydsui_example_0.bin'
DUMB_LOOP_COUNT = 5
dumb_loop_interval = dsui.DSUIInterval('FUNC_DUMBLOOP', 'INTERVAL')

cos_angle_event = dsui.DSUIEvent('FUNC_FINDCOSINE', 'ANGLE')
cos_value_event = dsui.DSUIEvent('FUNC_FINDCOSINE', 'VALUE')

def dumb_loop():
    dumb_loop_interval.start()
    print 'DUMB LOOP ENTER'
    for i in range(10):
        find_cosine(random.random())
    print 'DUMB LOOP LEAVE'
    dumb_loop_interval.end()
    
def find_cosine(angle):
    cos_angle_event.log_event(0, angle)
    value = math.cos(angle*2.0*math.pi)
    cos_value_event.log(0, value) 
    return value



if __name__ == '__main__':

    dsui.open(DSUI_LOG_FILE)
    print 'Running example with %i dumb loops...' % num_dumb_loops
    for x in range(DUMB_LOOP_COUNT): dumb_loop()
    print 'Closing DSUI, cleaning up...'
    dsui.close()
    print 'Exiting.'
    
