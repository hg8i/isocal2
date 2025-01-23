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
import subprocess

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


# def refreshPermission(path):
#     # log(f"DIRECTORY: check: {path}")
#     noRead  = not os.access(path, os.R_OK)
#     noWrite = not os.access(path, os.W_OK)
#     # noConn  = connectionTimedOut(path)
#     # log(f"DIRECTORY: check: read={not noRead} write={not noWrite}")
#     if noRead or noWrite:
#         cmd = settings["dataPathCmd"]
#         # log(f"DIRECTORY: recovery command: {cmd}")
#         result = subprocess.run( cmd, capture_output=True, text=True, shell=True)
#         authStatus = f"read={not noRead} write={not noWrite}. {str(result.stdout)} {str(result.stderr)}"
#         # log(f"DIRECTORY: Authentication: {result.stdout}")
#         # log(f"DIRECTORY: Authentication: {result.stderr}")
#         return authStatus
#     # elif noConn:
#         # return noConn
#     else:
#         return False


from userSettings import settings
from userSettings import uiColors

privateSettingsPath = settings["privateSettingsPath"]
settings["privateSettingsOk"](privateSettingsPath)
if not os.path.exists(privateSettingsPath):
    settings["downloadIcsCalendars"]=[]
else:
    try:
        data = open(privateSettingsPath,"r").read()
        settings["downloadIcsCalendars"] = eval(data)
    except:
        print(f"Unable to load ICS calendar file: {privateSettingsPath}. Check permissions/loading.")
        quit()

