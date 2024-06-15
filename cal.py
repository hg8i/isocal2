#!/bin/env python3
from setup import *
import model

def main(screen):
    curses.start_color()
    curses.use_default_colors()

    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)

    m = model.model(screen)
    m.run()




if __name__=="__main__":
    wrapper(main)


