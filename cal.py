#!/bin/env python3
from setup import *
import model
from index import *

def main(screen):
    curses.start_color()
    curses.use_default_colors()

    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)

    for iColor,name in enumerate(settings["uiColors"].keys()):
        iColor+=1
        fg = uiColors[name][1]
        bg = uiColors[name][0]
        curses.init_pair(iColor,fg,bg)
        settings["colors"][name] = iColor

    curses.curs_set(0)

    m = model.model(screen)
    m.run()




if __name__=="__main__":
    wrapper(main)


