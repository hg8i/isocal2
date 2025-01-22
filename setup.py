import multiprocessing
import curses
from curses import wrapper
import time,os,sys,glob,json
from datetime import datetime, timedelta
from collections import defaultdict
import re
import pickle
import math
import random
import copy

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

def now():
    return datetime.now()

thispath = os.path.dirname(os.path.abspath(__file__))

# cal box
# list box
# command box

settings = {}
settings["listHeight"] = 11

settings["pickleDir"] = "/home/prime/dev/isocal2/data"


color_green=2
color_brown=208
color_red=197
color_white=231
color_purple=201
color_yellow=220
color_black=0
color_cyan=123
color_dark_cyan=39
color_blue=45
color_bluegrey=12
color_dark_blue=25
color_dark_green=28
color_dark_red=88
color_salmon=9
color_dark_yellow=178
color_dark_grey= 235
color_mid_grey= 244
color_light_grey= 252
color_subtle_grey= 241
color_midnight_blue=17

settings["deleteChar"]     = 263
settings["ctrlUChar"]      = 21
settings["enterChar"]      = 10
settings["escapeChar"]     = 27
settings["downArrowChar"]  = 258
settings["upArrowChar"]    = 259
settings["leftArrowChar"]  = 260
settings["rightArrowChar"] = 261



uiColors = {}
defaultBg = 235
defaultFg = 251
defaultColor = [defaultBg,  defaultFg]
# interface colors
uiColors["commandView"]        = defaultColor
uiColors["searchView"]         = [color_dark_blue,  defaultFg]
uiColors["searchFocus"]        = [color_dark_blue,  color_dark_cyan]
uiColors["dialogView"]         = [color_dark_blue,  defaultFg]
uiColors["dialogFocus"]        = [color_dark_blue,  color_dark_cyan]
uiColors["listView"]           = [defaultBg,  defaultFg]
uiColors["gridView"]           =  defaultColor
uiColors["dayNames"]           = [defaultBg, defaultFg]
uiColors["highlight"]          = [defaultFg, defaultBg]
uiColors["contentFocus"]       = [color_midnight_blue,  defaultFg]
uiColors["firstDay"]           = [defaultBg, color_dark_grey]
# category colors
uiColors["eventDefault"]       =  defaultColor
uiColors["invalidCategory"]    = [defaultBg, defaultFg]
uiColors["work"]               = [defaultBg,color_cyan]
uiColors["home"]               = [defaultBg,color_dark_blue]
uiColors["crit"]               = [defaultBg,color_red]
uiColors["indico"]             = [defaultBg,color_subtle_grey]
# uiColors["ccs"]                = [defaultBg,color_salmon]
uiColors["travel"]             = [defaultBg,color_green]
uiColors["exotics"]            = [defaultBg,color_salmon]
# put in settings
settings["uiColors"]    = uiColors
settings["colors"]    = {}




# for drawing calendar grid
settings["dayNames"] = ["Mon","Tues","Weds","Thurs","Fri","Sat","Sun"]
settings["dayNames"] = ["Monday","Tuesday","Wednsday","Thursday","Friday","Satday","Sunday"]
settings["monthNames"] = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
settings["nDaysX"] = 7
settings["nWeeksY"] = 4
settings["gridMarginL"] = 6
settings["gridMarginR"] = 2
settings["gridMarginT"] = 1
settings["defaultCategory"] = "work"

settings["listMarginN"] = 0
settings["listMarginS"] = 1
settings["listMarginE"] = 2
settings["listMarginW"] = 2
settings["showPrevWeeks"] = 1


hotkeyMap = defaultdict(lambda:None)
hotkeyMap["q"] = {"function":"quit",        "description":"quit"}
hotkeyMap["+"] = {"function":"incNWeeks",   "description":"incNWeeks"}
hotkeyMap["-"] = {"function":"decNWeeks",   "description":"decNWeeks"}
hotkeyMap["d"] = {"function":"monthDown",   "description":"monthDown"}
hotkeyMap["u"] = {"function":"monthUp",     "description":"monthUp"}
hotkeyMap["j"] = {"function":"moveDown",    "description":"moveDown"}
hotkeyMap["k"] = {"function":"moveUp",      "description":"moveUp"}
hotkeyMap["h"] = {"function":"moveLeft",    "description":"moveLeft"}
hotkeyMap["l"] = {"function":"moveRight",   "description":"moveRight"}
hotkeyMap["n"] = {"function":"selectNext",  "description":"selectNext"}
hotkeyMap["N"] = {"function":"selectPrev",  "description":"selectPrev"}
hotkeyMap["g"] = {"function":"jumpToday",   "description":"jumpToday"}
hotkeyMap["x"] = {"function":"deleteEvent", "description":"deleteEvent"}
hotkeyMap["i"] = {"function":"insertEvent", "description":"insertEvent"}
hotkeyMap["c"] = {"function":"changeEvent", "description":"changeEvent"}
hotkeyMap["?"] = {"function":"help",        "description":"Show this message"}
hotkeyMap["r"] = {"function":"refresh",     "description":""}
hotkeyMap["y"] = {"function":"yank",        "description":""}
hotkeyMap["p"] = {"function":"paste",       "description":""}
hotkeyMap["/"] = {"function":"search",      "description":"Do one a search"}
hotkeyMap["w"] = {"function":"icsUpdate",   "description":""}
hotkeyMap[chr(settings["upArrowChar"])] = {"function":"moveUp", "description":""}
hotkeyMap[chr(settings["downArrowChar"])] = {"function":"moveDown", "description":""}
hotkeyMap[chr(settings["leftArrowChar"])] = {"function":"moveLeft", "description":""}
hotkeyMap[chr(settings["rightArrowChar"])] = {"function":"moveRight", "description":""}
settings["hotkeyMap"] = hotkeyMap


# ICS calendars may use private keys that should be stored safely somewhere
# How you do that is up to you
import os
privateSettingsPath = "/home/prime/afs/remote/isoplan/privateSettings.py"
# create if needed
if not os.path.exists(privateSettingsPath):
    settings["downloadIcsCalendars"]=[]
else:
    settings["downloadIcsCalendars"] = eval(open(privateSettingsPath).read())
settings["timezone"] = "Europe/Paris"

settings["showSideYears"] = False
settings["showTopYears"] = True
