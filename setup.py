import multiprocessing
import curses
from curses import wrapper
import time,os,sys,glob,json
from datetime import datetime
from collections import defaultdict
import re
import pickle
import math

from subprocess import call

logon = True
os.popen("rm log.txt"); time.sleep(0.01)
def log(*text):
    global logon
    # if not logon: return
    f = open("log.txt","a")
    text = " ".join([str(t) for t in text])
    f.write(str(text)+"\n")
    f.close()


thispath = os.path.dirname(os.path.abspath(__file__))

# cal box
# list box
# command box

settings = {}
settings["listHeight"] = 11

settings["pickleDir"] = "/home/prime/dev/isoplan_mvc/data/dump.pkl"


color_green=40
color_red=197
color_white=231
color_purple=201
color_yellow=220
color_black=0
color_cyan=123
color_dark_cyan=39
color_blue=45
color_dark_blue=25
color_dark_green=28
color_dark_red=88
color_dark_yellow=178
color_dark_grey= 235
color_mid_grey= 244
color_light_grey= 252

# settings["deleteChar"]         = 263
# settings["ctrlUChar"]         = 21
# settings["enterChar"]         = 10
# settings["escapeChar"]         = 27
# settings["overflowSymbol"] = ">"

settings["bkColorCommandView"]        = color_dark_blue
settings["fgColorCommandView"]        = color_white
settings["bkColorListView"]           = color_green
settings["fgColorListView"]           = color_white
settings["bkColorGridView"]           = color_mid_grey
settings["fgColorGridView"]           = color_white

# for drawing calendar grid
settings["nDaysX"] = 7
settings["nWeeksY"] = 4
settings["gridMarginL"] = 6
settings["gridMarginR"] = 2
settings["gridMarginT"] = 2


hotkeyMap = defaultdict(lambda:None)
hotkeyMap["q"] = "quit"
# hotkeyMap["/"] = "search"
# hotkeyMap["\t"] = "cfocus"
# hotkeyMap["c"] = "change"
# hotkeyMap["e"] = "edit"
# hotkeyMap["h"] = "help"
# hotkeyMap["n"] = "new"
# hotkeyMap[":"] = "command"
# hotkeyMap["p"] = "publish"
settings["hotkeyMap"] = hotkeyMap

