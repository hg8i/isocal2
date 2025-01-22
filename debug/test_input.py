#!/bin/env python3
from setup import *
import drawing

class controller:
    def __init__(self,screen):
        self._screen = screen
        self.pos=0

    def run(self):

        while True:

            char = self._screen.getch()
            self.pos+=1
            s = char
            drawing._text(self._screen,self.pos,0,s,color=0,bold=False,reverse=False,underline=False)



def main(screen):
    c=controller(screen)
    c.run()

if __name__=="__main__":
    wrapper(main)
