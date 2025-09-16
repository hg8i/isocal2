settings = {}


color_green=2
# color_brown=208
color_red=197
color_white=231
color_purple=5
color_yellow=220
color_black=0
color_cyan=75
color_dark_cyan=39
color_blue=45
color_bluegrey=12
color_dark_blue=25
color_dark_green=58
color_dark_red=88
color_salmon=9
color_dark_yellow=178
color_orange = 202
color_dark_grey= 235
color_mid_grey= 244
color_light_grey= 252
color_subtle_grey= 241
color_midnight_blue=17
color_white = 255
color_brown = 94

color_beige=11
color_light_beige=223
color_dark_brown=58

settings["deleteChar"]     = 263
settings["ctrlUChar"]      = 21
settings["enterChar"]      = 10
settings["escapeChar"]     = 27
settings["downArrowChar"]  = 258
settings["upArrowChar"]    = 259
settings["leftArrowChar"]  = 260
settings["rightArrowChar"] = 261



uiColors = {}
defaultBg = color_light_beige
defaultFg = color_dark_brown
defaultColor = [defaultBg,  defaultFg]
# interface colors
uiColors["commandView"]        = defaultColor
uiColors["searchView"]         = [color_brown,  color_white]
uiColors["searchFocus"]        = [color_dark_blue,  color_dark_cyan]
uiColors["dialogView"]         = [color_brown,  color_white]
uiColors["dialogFocus"]        = [color_brown,  color_beige]
uiColors["listView"]           = [defaultBg,  defaultFg]
uiColors["gridView"]           =  defaultColor
uiColors["dayNames"]           = [defaultBg, defaultFg]
uiColors["highlight"]          = [color_beige, defaultFg] # day highlight color
# uiColors["contentFocus"]       = [color_midnight_blue,  defaultFg]
# uiColors["contentFocus"]       = [color_brown,  color_white]
uiColors["contentFocus"]       = [color_brown,  color_beige] # cursor highlight color
uiColors["firstDay"]           = [defaultBg, color_dark_red]
# category colors
uiColors["eventDefault"]       =  defaultColor
uiColors["invalidCategory"]    = [defaultBg, defaultFg]
uiColors["work"]               = [defaultBg,color_dark_blue]
uiColors["home"]               = [defaultBg,54]
uiColors["crit"]               = [defaultBg,color_red]
uiColors["indico"]             = [defaultBg,color_subtle_grey]
uiColors["french"]             = [defaultBg,color_purple]
uiColors["plan"]               = [defaultBg,color_cyan]
uiColors["travel"]             = [defaultBg,color_green]
uiColors["ccs"]                = [defaultBg,color_salmon]
uiColors["svj"]                = [defaultBg,color_orange]
uiColors["exotics"]            = [defaultBg,color_dark_green]
# put in settings
settings["uiColors"]    = uiColors
settings["colors"]    = {}


settings["timezone"] = "Europe/Paris"
settings["showSideYears"] = False
settings["showTopYears"] = True


# for drawing calendar grid
settings["dayNames"] = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
settings["monthNames"] = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
settings["defaultCategory"] = "work"
settings["nDaysX"] = 7
settings["nWeeksY"] = 4
settings["gridMarginL"] = 6
settings["gridMarginR"] = 2
settings["gridMarginT"] = 1
settings["listMarginN"] = 0
settings["listMarginS"] = 1
settings["listMarginE"] = 2
settings["listMarginW"] = 2
settings["showPrevWeeks"] = 1
settings["listHeight"] = 11

# navigation keys
hotkeyMap = {}
hotkeyMap["q"] = {"function":"quit",        "description":"quit"}
hotkeyMap["+"] = {"function":"incNWeeks",   "description":"Show more weeks"}
hotkeyMap["-"] = {"function":"decNWeeks",   "description":"Show fewer weeks"}
hotkeyMap["d"] = {"function":"monthDown",   "description":"Jump down"}
hotkeyMap["u"] = {"function":"monthUp",     "description":"Jump up"}
hotkeyMap["j"] = {"function":"moveDown",    "description":"Move one week down"}
hotkeyMap["k"] = {"function":"moveUp",      "description":"Move one week up"}
hotkeyMap["h"] = {"function":"moveLeft",    "description":"Move one day left"}
hotkeyMap["l"] = {"function":"moveRight",   "description":"Move one day right"}
hotkeyMap["n"] = {"function":"selectNext",  "description":"Select next event"}
hotkeyMap["N"] = {"function":"selectPrev",  "description":"Select previous event"}
hotkeyMap["g"] = {"function":"jumpToday",   "description":"Jump to today"}
hotkeyMap["x"] = {"function":"deleteEvent", "description":"Delete event"}
hotkeyMap["i"] = {"function":"insertEvent", "description":"Insert event"}
hotkeyMap["c"] = {"function":"changeEvent", "description":"Change event"}
hotkeyMap["?"] = {"function":"help",        "description":"Show this message"}
hotkeyMap["y"] = {"function":"yank",        "description":"Yank event"}
hotkeyMap["p"] = {"function":"paste",       "description":"Paste event"}
hotkeyMap["w"] = {"function":"icsUpdate",   "description":"Update ICS events"}
hotkeyMap["/"] = {"function":"search",      "description":"Search for events (only loaded year)"}
hotkeyMap["r"] = {"function":"refresh",     "description":"Refresh screen"}
hotkeyMap[chr(settings["upArrowChar"])] = {"function":"moveUp", "description":"","hidden":True}
hotkeyMap[chr(settings["downArrowChar"])] = {"function":"moveDown", "description":"","hidden":True}
hotkeyMap[chr(settings["leftArrowChar"])] = {"function":"moveLeft", "description":"","hidden":True}
hotkeyMap[chr(settings["rightArrowChar"])] = {"function":"moveRight", "description":"","hidden":True}
settings["hotkeyMap"] = hotkeyMap



# ICS calendars may use private keys that should be stored safely somewhere
# How you do that is up to you
settings["privateSettingsPath"] = "/home/prime/afs/remote/isocalPrivateSettings.py"
settings["dataPath"] = "/afs/cern.ch/user/a/aawhite/remote/isocal2"
# settings["dataPath"] = "data" # DEBUG

def refreshAfs(iPath,depth=0):
    """ Refresh AFS permissions
        If it's ok, return False
        Otherwise, return status
    """
    import os,subprocess,time
    # work with directory
    if os.path.isdir(iPath):
        path = iPath
    else:
        path = os.path.dirname(iPath)

    noRead  = not os.access(path, os.R_OK)
    noWrite = not os.access(path, os.W_OK)
    ret = False
    if noRead or noWrite:
        authCommand = 'bash -c "source ~/.bashlocal && afsAuth"' # afsAuth is bash runction
        # authCommand = 'ls'
        result = subprocess.run( authCommand, capture_output=True, text=True, shell=True)
        authStatus = f"read/write={not noRead}/{not noWrite}. {str(result.stdout)} {str(result.stderr)}"
        ret = authStatus
        # try again
        if depth<2:
            return refreshAfs(iPath,depth=depth+1)
        else:
            return authStatus
        # try recovery
    # confirm readable
    tPath = os.path.join(path,".test")
    checkCommand = f"cat {tPath}"
    result = subprocess.run( checkCommand, capture_output=True, text=True, shell=True)
    if "denied" in result.stderr+result.stdout:
        ret = f"Failed to read test file {tPath}"
    # confirm writable
    try:
        tFile = open(tPath,"a")
        tFile.write(f"{time.time()}\n")
        tFile.close()
    except Exception as e:
        ret = f"Failed to write test file {tPath}: {e}"
    return ret

settings["privateSettingsOk"] = refreshAfs
settings["dataPathOk"] = refreshAfs
