#! /bin/env python
import os
import sys
from time import sleep
from threading import Thread, Event
from pygsched.gssession import GSSession
import datastreams.pydsui as dsui
import pygame

class ExampleThread():
    LOOP_COUNT = 1000

    def run(self):
        pygame.init()
        size = width, height = 640, 480
        speed = [0, 2]
        black = 0, 0, 0
        ballrect = pygame.rect.Rect(int(width/2), 0, 30, 30) 
        screen = pygame.display.set_mode(size)
        
        while 1:
            screen.fill(black)
            ballrect = ballrect.move(speed)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
            
            if ballrect.top < 0 or ballrect.bottom > height:
                speed[1] = -speed[1]
                
            pygame.draw.rect(screen, (255,255,255), ballrect)
            pygame.display.flip()
        
if __name__ == '__main__':
    e_thread = ExampleThread()     
    e_thread.run()
    sys.exit()
        

    
