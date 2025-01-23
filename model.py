from setup import *
import view
import controller
from index import *
from icsDownload import *

class model:

    def __init__(self,screen):
        self._screen = screen

        # Threading
        self._manager = multiprocessing.Manager()
        self._event   = self._manager.Event()
        self._view_i = self._manager.Queue()
        self._view_o = self._manager.Queue()
        self._index_i = self._manager.Queue()
        self._index_o = self._manager.Queue()
        self._controller_i = self._manager.Queue()
        self._controller_o = self._manager.Queue()
        self._icsDownload_i = self._manager.Queue()
        self._icsDownload_o = self._manager.Queue()
        self._char_queue = self._manager.Queue() # input from controller

        self.icsDownloadThread = False

        self._hotkeyMap   = settings["hotkeyMap"]
        self._commandMap = {}
        self._commandMap["quit"]   = lambda cmds: self._act_quit()
        self._commandMap["refresh"]     = lambda cmds: self._act_refresh()
        self._commandMap["incNWeeks"]   = lambda cmds: self._act_modNWeeks(n=1)
        self._commandMap["decNWeeks"]   = lambda cmds: self._act_modNWeeks(n=-1)
        self._commandMap["monthDown"]   = lambda cmds: self._act_move("S")
        self._commandMap["monthUp"]     = lambda cmds: self._act_move("N")
        self._commandMap["moveDown"]    = lambda cmds: self._act_move("s")
        self._commandMap["moveUp"]      = lambda cmds: self._act_move("n")
        self._commandMap["moveLeft"]    = lambda cmds: self._act_move("w")
        self._commandMap["moveRight"]   = lambda cmds: self._act_move("e")
        self._commandMap["selectNext"]  = lambda cmds: self._act_select(1)
        self._commandMap["selectPrev"]  = lambda cmds: self._act_select(-1)
        self._commandMap["jumpToday"]   = lambda cmds: self._act_jump(now())
        self._commandMap["deleteEvent"] = lambda cmds: self._act_deleteEvent()
        self._commandMap["insertEvent"] = lambda cmds: self._act_dialog("insertEvent")
        self._commandMap["changeEvent"] = lambda cmds: self._act_dialog("changeEvent")
        self._commandMap["help"]        = lambda cmds: self._act_dialog("help")
        self._commandMap["yank"]        = lambda cmds: self._act_copyPaste("yank")
        self._commandMap["paste"]       = lambda cmds: self._act_copyPaste("paste")
        self._commandMap["search"]      = lambda cmds: self._act_search()
        self._commandMap["icsUpdate"]   = lambda cmds: self._act_icsUpdate()


        self.startIndex() # before updateContent

        self._messageTime = time.time()
        self._messageTimeout = 5


        # navigation state
        self._state_nWeeksY = settings["nWeeksY"]
        self._state_nDaysX  = settings["nDaysX"]

        # defines self._state_iDayFocus and self._state_iWeekFocus
        self._state_iDayToday = -1
        self._state_iWeekToday = -1
        self._state_dialogFocus = 0
        self._state_cursorPos = -1
        self._state_updateContentCounter = 0
        self._state_clipboard = False
        self._state_viewUpdates = {}
        self._act_jump(now())


        # MVC
        self._controller = controller.controller(self._screen,inputq=self._controller_i,outputq=self._controller_o,
                                                 charq=self._char_queue,event=self._event
                                                )
        self._view = view.view(self._screen,inputq=self._view_i,outputq=self._view_o,
                              nWeeksY = self._state_nWeeksY,
                              nDaysX = self._state_nDaysX,
                              iDayFocus = self._state_iDayFocus,
                              iWeekFocus = self._state_iWeekFocus,
                              )

        self._icsDownload = icsDownload(inputq=self._icsDownload_i,outputq=self._icsDownload_o,
                                                 event=self._event
                                                )


    def _act_refresh(self):
        self.updateContent()
        self.processResize()

    def _act_quit(self):
        self.stopIcsDownload() # do first
        self.stopController()
        self.stopIndex()
        self.stopView()
        quit()

    def _act_select(self,direction):
        """ Increment/decrement selection """
        self._state_iContentFocus+=direction
        iDay = self._state_iDayFocus
        iWeek = self._state_iWeekFocus
        dayContent = self._contents[iDay][iWeek]["events"]
        maxSelect = len(dayContent)

        if direction:
            # is moved, do "roll over"
            if self._state_iContentFocus<0:
                self._state_iContentFocus = maxSelect-1
            if self._state_iContentFocus>=maxSelect:
                self._state_iContentFocus = 0
        else:
            if self._state_iContentFocus<0:
                self._state_iContentFocus = 0
            if self._state_iContentFocus>maxSelect-1:
                self._state_iContentFocus = maxSelect-1

        # send updates
        data = {}
        data["type"] = "updatevalue"
        data["redraw"] = "grid"
        data["key"] = "_iContentFocus"
        data["value"] = self._state_iContentFocus
        self._view_i.put(data)

    def _sendDialogFocusUpdate(self):
        """ Update focuses """
        # send updates
        data = {}
        data["type"] = "updatevalue"
        data["key"] = []
        data["value"] = []
        data["redraw"] = "dialog"
        data["key"].append("_dialogFocus")
        data["value"].append(self._state_dialogFocus)
        self._view_i.put(data)

    def _sendDialogFieldsUpdate(self):
        """ Update dialog data """
        # send updates
        data = {}
        data["type"] = "updatevalue"
        data["key"] = []
        data["value"] = []
        data["redraw"] = "dialog"
        data["key"].append("_dialogCursorPos")
        data["value"].append(self._state_cursorPos)
        data["key"].append("_dialogFields")
        data["value"].append(self._dialogFields)
        self._view_i.put(data)

    def _sendGridFocusUpdate(self):
        """ Update focuses """
        # send updates
        data = {}
        data["type"] = "updatevalue"
        data["key"] = []
        data["value"] = []
        data["redraw"] = "grid"
        data["key"].append("_iWeekToday")
        data["value"].append(self._state_iWeekToday)
        data["key"].append("_iDayToday")
        data["value"].append(self._state_iDayToday)
        data["key"].append("_iContentFocus")
        data["value"].append(self._state_iContentFocus)
        data["key"].append("_iDayFocus")
        data["value"].append(self._state_iDayFocus)
        data["key"].append("_iWeekFocus")
        data["value"].append(self._state_iWeekFocus)
        self._view_i.put(data)

    def message(self,text):
        """ Display a message """
        self._messageTime = time.time()
        data = {}
        data["type"] = "message"
        data["value"] = text
        self._view_i.put(data)

    def _act_deleteEvent(self):
        """ Delete currently selected event
        """
        event = self.getFocusedEvent()
        if event is None:
            self.message("No event to delete")
            return
        self._state_clipboard = event
        self.message(f"Delete event: {event}")
        self._index_i.put({"type":"delEvent","event":event})
        self.updateContent()

        if self._state_iContentFocus<0:
            self._state_iContentFocus = 1

        self._sendGridFocusUpdate()

    def _act_copyPaste(self,mode):
        """ Copy and paste events """

        if mode=="yank":
            event = self.getFocusedEvent()
            # change ID, modification, creation
            self._state_clipboard = event
            self.message("Yanked event")

        elif mode=="paste":
            if not self._state_clipboard: 
                self.message("No event to paste")
                return
            day = self.getFocusedDay()
            event = copy.deepcopy(self._state_clipboard)
            event["date"] = day
            event["uniqueid"]  = hash(str(time.time())+"yanked"+event.name)
            event["modified"] = time.time()
            self._index_i.put({"type":"addEvent","event":event})
            self.updateContent()

    def _runSearchTopLoop(self):

        # initially, start search
        searchData = {}
        searchData["type"] = "searchByString"
        searchData["target"] = self._state_searchText
        self._index_i.put(searchData)


        while True:
            self._event.wait()
            self._event.clear()
            # input processing loop
            while not self._char_queue.empty():
                char = self._char_queue.get()
                log("Char for search navigation:",char,chr(char))

                if char==410: #resize
                    self.processResize()

                # exit or quit
                elif char in [settings["escapeChar"],settings["enterChar"]]:
                    data = {}
                    data["type"] = "search"
                    data["instruction"] = "close"
                    self._view_i.put(data)
                    return

                else:
                    if char in [settings["escapeChar"],settings["enterChar"]]:
                        self._state_cursorPos = -1
                        self._sendDialogFieldsUpdate()
                        return
                    elif char == settings["downArrowChar"]:
                        self._state_searchFocus+=1
                        self._state_searchFocus%=len(self._state_searchHits)
                    elif char == settings["upArrowChar"]:
                        self._state_searchFocus-=1
                        self._state_searchFocus%=len(self._state_searchHits)
                    else:
                        self._state_searchText = self._processTextMod(self._state_searchText,char)

                    # send updates to gui
                    data = {}
                    data["type"] = "updatevalue"
                    data["redraw"] = "search"
                    data["key"]    = []
                    data["value"]  = []
                    data["key"]   .append("_searchText")
                    data["value"] .append(self._state_searchText)
                    data["key"]   .append("_searchCursorPos")
                    data["value"] .append(self._state_cursorPos)
                    data["key"]   .append("_searchFocus")
                    data["value"] .append(self._state_searchFocus)
                    self._view_i.put(data)

                    # send updates to index
                    searchData = {}
                    searchData["type"] = "searchByString"
                    searchData["target"] = self._state_searchText
                    self._index_i.put(searchData)


            # search processing loop
            while not self._index_o.empty():
                update = self._index_o.get()
                if update["type"] != "searchResult": continue
                self._state_searchHits = sorted(update["hits"])
                # self._state_searchFocus = 0 # TODO: replace with index calculated to match previous position
                # send update to gui
                data = {}
                data["type"] = "updatevalue"
                data["redraw"] = "search"
                data["key"]    = []
                data["value"]  = []
                data["key"]   .append("_searchEvents")
                data["value"] .append(self._state_searchHits)
                data["key"]   .append("_searchCursorPos")
                data["value"] .append(self._state_cursorPos)
                self._view_i.put(data)




    def _act_search(self):
        """ Pop up and process search
        """
        self._state_searchFocus = 0
        self._state_searchText = ""
        self._state_searchHits = []

        data = {}
        data["type"] = "search"
        data["instruction"]  = "launch"
        data["title"]  = f"Search"
        self._view_i.put(data)

        self._runSearchTopLoop()

    def _act_dialog(self,mode):
        """ Pop up and process dialog window 
            Define self._dialogFields
        """
        self._state_dialogFocus = 0


        # setup
        if mode=="help":
            self._dialogFields = []
            i = 0
            self._dialogFields += [{"name":"Info","type":"divider","content":"-"}]
            self._dialogFields += [{"name":"dataPath","type":"label","content":settings["dataPath"]}]
            self._dialogFields += [{"name":"Hotkeys","type":"divider","content":"-"}]
            for k,v in settings["hotkeyMap"].items():
                self._dialogFields += [{"name":k,"type":"label","content":v["description"]}]

            data = {}
            data["type"] = "dialog"
            data["instruction"]  = "launch"
            data["title"]  = f"Help"
            data["lines"] = self._dialogFields
            self._view_i.put(data)

            # run dialog
            self._runDialogTopLoop()

        # setup
        if mode=="insertEvent":
            periods = ["week","biweek","month","year","day"]
            self._dialogFields = []
            self._dialogFields += [{"name":"name","type":"text","content":""}]
            self._dialogFields += [{"name":"category","type":"text","content":settings["defaultCategory"]}]
            self._dialogFields += [{"name":"time","type":"text","content":""}]
            self._dialogFields += [{"name":"notes","type":"text","content":""}]
            # self._dialogFields += [{"name":"repeat","type":"radio","content":False}]
            self._dialogFields += [{"name":"repeat","type":"int","content":0}]
            self._dialogFields += [{"name":"period","type":"map","content":0,"list":periods}]

            data = {}
            day = self.getFocusedDay().strftime("%d/%m/%y")
            data["type"] = "dialog"
            data["instruction"]  = "launch"
            data["title"]  = f"New Event {day}"
            data["lines"] = self._dialogFields
            self._view_i.put(data)

            # run dialog
            self._runDialogTopLoop()
            fields = {f["name"]:f["content"] for f in self._dialogFields}
            if not fields["name"]: 
                self.message("No event created")
                return

            if periods[fields["period"]] == "day":
                delta = timedelta(days=1)
            elif periods[fields["period"]] == "week":
                delta = timedelta(weeks=1)
            elif periods[fields["period"]] == "biweek":
                delta = timedelta(weeks=2)
            elif periods[fields["period"]] == "month":
                delta = timedelta(months=1)
            elif periods[fields["period"]] == "year":
                delta = timedelta(years=1)

            # process new event(s)
            for repeat in range(fields["repeat"]+1):
                event = eventdata()
                event["name"] = fields["name"]
                event["date"] = self.getFocusedDay()+repeat*delta
                event["uniqueid"]  = hash(str(time.time())+fields["name"]+str(repeat))
                event["created"]  = time.time()
                event["modified"] = time.time()
                event["category"] = fields["category"]
                event["time"] = fields["time"]
                event["notes"] = fields["notes"]
                if repeat:
                    event["notes"] = "(R)"+fields["notes"]
                self._index_i.put({"type":"addEvent","event":event})

            self.updateContent()

        # setup
        if mode=="changeEvent":
            event = self.getFocusedEvent()
            if not event: 
                self.message("No event to change")
                return
            periods = ["day","week","biweek","month","year"]
            self._dialogFields = []
            self._dialogFields += [{"name":"name","type":"text","content":event.name}]
            self._dialogFields += [{"name":"category","type":"text","content":event.category}]
            self._dialogFields += [{"name":"time","type":"text","content":event.time}]
            self._dialogFields += [{"name":"notes","type":"text","content":event.notes}]
            self._dialogFields += [{"name":"repeat","type":"int","content":0}]
            self._dialogFields += [{"name":"period","type":"map","content":0,"list":periods}]

            data = {}
            day = event.date.strftime("%d/%m/%y")
            data["type"] = "dialog"
            data["instruction"]  = "launch"
            data["title"]  = f"Change event {day}"
            data["lines"] = self._dialogFields
            self._view_i.put(data)

            # run dialog
            self._runDialogTopLoop()
            fields = {f["name"]:f["content"] for f in self._dialogFields}
            if not fields["name"]: return

            if periods[fields["period"]] == "day":
                delta = timedelta(days=1)
            elif periods[fields["period"]] == "week":
                delta = timedelta(weeks=1)
            elif periods[fields["period"]] == "biweek":
                delta = timedelta(weeks=2)
            elif periods[fields["period"]] == "month":
                delta = timedelta(months=1)
            elif periods[fields["period"]] == "year":
                delta = timedelta(years=1)

            # process modifications to event
            event["name"] = fields["name"]
            event["date"] = self.getFocusedDay()
            event["modified"] = time.time()
            event["category"] = fields["category"]
            event["time"] = fields["time"]
            event["notes"] = fields["notes"]
            self._index_i.put({"type":"modEvent","event":event})
            log(f"MODEL: modified event cat={fields['category']}")

            # process new repeated events
            for repeat in range(fields["repeat"]):
                event = eventdata()
                event["name"] = fields["name"]
                event["date"] = self.getFocusedDay()+(1+repeat)*delta
                event["uniqueid"]  = hash(str(time.time())+fields["name"]+str(repeat))
                event["created"]  = time.time()
                event["modified"] = time.time()
                event["category"] = fields["category"]
                event["time"] = fields["time"]
                event["notes"] = "(R)"+fields["notes"]
                self._index_i.put({"type":"addEvent","event":event})


            self.updateContent()
            self.message(f"Modified event: {event}")



    def _runDialogEditLoop(self,clear=False):
        content=self._dialogFields[self._state_dialogFocus]["content"]
        self._state_cursorPos = -1

        # return if this not text field
        if self._dialogFields[self._state_dialogFocus]["type"]=="line":
            return
        elif self._dialogFields[self._state_dialogFocus]["type"]=="map":
            if clear:
                content-=1
            else:
                content+=1
            content%=len(self._dialogFields[self._state_dialogFocus]["list"])
            self._dialogFields[self._state_dialogFocus]["content"] = content
            self._sendDialogFieldsUpdate()
            return
        elif self._dialogFields[self._state_dialogFocus]["type"]=="int":
            if clear:
                content-=1
            else:
                content+=1
            content%=53
            self._dialogFields[self._state_dialogFocus]["content"] = content
            self._sendDialogFieldsUpdate()
            return
        elif self._dialogFields[self._state_dialogFocus]["type"]=="radio":
            self._dialogFields[self._state_dialogFocus]["content"] = not content
            self._sendDialogFieldsUpdate()
            return


        if clear:
            content = ""
        self._dialogFields[self._state_dialogFocus]["content"] = content
        self._state_cursorPos = len(content)+1
        self._sendDialogFieldsUpdate()

        while True:
            self._event.wait()
            self._event.clear()
            while not self._char_queue.empty():
                char = self._char_queue.get()
                if char==410: #resize
                    self.processResize()
                    continue
                log("Char for dialog:",char,chr(char))
                if char in [settings["escapeChar"],settings["enterChar"]]:
                    self._state_cursorPos = -1
                    self._sendDialogFieldsUpdate()
                    return
                else:
                    content = self._processTextMod(content,char)
            self._dialogFields[self._state_dialogFocus]["content"] = content
            self._sendDialogFieldsUpdate()

    def _processTextMod(self,content,char):
        if char==settings["ctrlUChar"]:
            content=""
            self._state_cursorPos=1
        elif char==settings["deleteChar"]:
            if len(content): content=content[:-1]
            self._state_cursorPos-=1
        else:
            content+=chr(char)
            self._state_cursorPos+=1
        return content


    def _runDialogTopLoop(self):
        while True:
            self._event.wait()
            self._event.clear()
            while not self._char_queue.empty():
                char = self._char_queue.get()
                log("Char for dialog navigation:",char,chr(char))

                if char==410: #resize
                    self.processResize()
                    continue
                    
                if char == ord("j"):
                    self._state_dialogFocus+=1
                    self._state_dialogFocus%=len(self._dialogFields)
                    self._sendDialogFocusUpdate()
                if char == ord("k"):
                    self._state_dialogFocus-=1
                    self._state_dialogFocus%=len(self._dialogFields)
                    self._sendDialogFocusUpdate()
                if char == ord("c") or char == ord("-"):
                    self._runDialogEditLoop(clear=True)
                if char == ord("i") or char == ord("+"):
                    self._runDialogEditLoop(clear=False)

                # exit or quit
                if char in [settings["escapeChar"],settings["enterChar"],ord("q")]:
                    data = {}
                    data["type"] = "dialog"
                    data["instruction"] = "close"
                    self._view_i.put(data)
                    return


    def _act_jump(self,target):
        """ Jump to datetime target """
        year = target.year
        week = target.isocalendar().week

        nWeeksShowBefore = settings["showPrevWeeks"]*(self._state_nWeeksY>1)
        self._state_year = year
        self._state_week = now().isocalendar().week-1-nWeeksShowBefore
        self._state_iDayFocus = target.weekday()
        self._state_iWeekFocus = nWeeksShowBefore
        self._state_iContentFocus = 0

        self.updateContent()
        self._sendGridFocusUpdate()

    def _act_icsUpdate(self):
        """ Download ICS updates """
        log(f"Launch ICS update")
        if self.icsDownloadThread:
            # if alive, don't interrupt
            if self.icsDownloadThread.is_alive(): 
                self.message("Be patient for the download")
                return
        self.icsDownloadThread = multiprocessing.Process(target=self._icsDownload.run)
        self.icsDownloadThread.start()


    def _act_move(self,direction):
        """ Increment/decrement number of weeks shown """
        log(f"Moving {direction}")
        iDayOrig = self._state_iDayFocus
        iWeekOrig = self._state_iWeekFocus
        scroll = False
        if direction=="S":
            self._state_iWeekFocus+=self._state_nWeeksY-1
        if direction=="N":
            self._state_iWeekFocus-=self._state_nWeeksY-1
        if direction=="s":
            self._state_iWeekFocus+=1
        if direction=="n":
            self._state_iWeekFocus-=1
        if direction=="w":
            self._state_iDayFocus-=1
        if direction=="e":
            self._state_iDayFocus+=1
        # reset selection
        self._state_iContentFocus=0

        # rollovers
        maxDay = 6 # TODO
        if self._state_iDayFocus<0:
            self._state_iDayFocus=maxDay
            self._state_iWeekFocus-=1
        if self._state_iDayFocus>maxDay:
            self._state_iDayFocus=0
            self._state_iWeekFocus+=1

        if self._state_iWeekFocus<0:
            self._state_week+=self._state_iWeekFocus
            self._state_iWeekFocus=0
            scroll = True
        if self._state_iWeekFocus>=self._state_nWeeksY:
            self._state_week+=self._state_iWeekFocus-self._state_nWeeksY+1
            self._state_iWeekFocus=self._state_nWeeksY-1
            scroll = True

        if scroll:
            self.updateContent()

        self._sendGridFocusUpdate()


    def _act_modNWeeks(self,n=1):
        """ Increment/decrement number of weeks shown """
        self.collectViewUpdates()

        self._state_nWeeksY += n
        self._state_nWeeksY = max(1,self._state_nWeeksY)

        # Limit number of lines based on available
        if "gridScreenY" in self._state_viewUpdates.keys():
            self._state_nWeeksY = min(self._state_nWeeksY,self._state_viewUpdates["gridScreenY"]-3)

        self.updateContent() # update day content for new range
        data = {}
        data["type"] = "updatevalue"
        data["key"] = "_nWeeksY"
        data["value"] = self._state_nWeeksY
        data["redraw"] = "grid"
        self._view_i.put(data)

    def _updateDays(self):
        """ Update display with current content """
        data = {}
        data["type"] = "updateday"
        data["content"] = []
        data["iDay"] = []
        data["iWeek"] = []
        for iDay in self._contents.keys():
            for iWeek in self._contents[iDay].keys():
                content = self._contents[iDay][iWeek]
                data["content"].append(content)
                data["iDay"].append(iDay)
                data["iWeek"].append(iWeek)
        self._view_i.put(data)

    def getFocusedEvent(self):
        """ Return current selected event """
        week = self._state_iWeekFocus
        day  = self._state_iDayFocus
        focus = self._state_iContentFocus

        if len(self._contents[day][week]["events"])==0:
            return None
        event = self._contents[day][week]["events"][focus]
        return event


    def getFocusedDay(self):
        """ Return current selected day datetime """
        year = self._state_year
        week = self._state_week+self._state_iWeekFocus
        day  = self._state_iDayFocus
        dt = self._getDatetime(year,week,day)
        return dt

    def _getDatetime(self,year,week,day):
        """ Get datetime object from week/year/day"""
        mod = 0
        # self._state_year
        if week<0:
            mod  = math.floor(week/52)
            week%=52
        elif week>52:
            mod  = math.floor(week/52)
            week%=52
        s = f"{year+mod}-{week}-{(day+1)%7}"
        dt = datetime.strptime(s,"%Y-%W-%w")
        return dt

    def updateContent(self):
        """ Get grid of days to display """
        start = self._state_week
        stop = start+self._state_nWeeksY
        year = self._state_year
        weekNumbers = []
        monthNames = []
        yearNames = []
        self._state_iDayToday = -1
        self._state_iWeekToday = -1
        self._state_updateContentCounter+=1
        # self.message(f"Updates: {self._state_updateContentCounter}")

        # first, post requests to index
        self._dtToNumber = {}
        days = []
        for iWeek,week in enumerate(range(start,stop)):
            for iDay,day in enumerate(range(self._state_nDaysX)):
                dt = self._getDatetime(year,week,day)
                days.append(dt)

                # update "today" token
                if dt.date()==now().date():
                    self._state_iDayToday = iDay
                    self._state_iWeekToday = iWeek

                self._dtToNumber[dt] = [iWeek,iDay]

            # update left side text
            weekNumbers.append(dt.isocalendar().week)
            monthNames.append(settings["monthNames"][dt.month%12-1])
            yearNames.append(dt.year)
        
        # post request for day data
        self._index_i.put({"type":"getEventsOnDays","days":days})

        # update week numbers
        data = {}
        data["type"] = "updatevalue"
        data["key"] = ["_weekNumbers","_monthNames","_yearNames"]
        data["value"] = [weekNumbers,monthNames,yearNames]
        data["redraw"] = "grid"
        self._view_i.put(data)

    def startController(self):
        log("MODEL: Starting controller")
        self.controllerThread = multiprocessing.Process(target=self._controller.run)
        self.controllerThread.start()

    def stopController(self):
        log("MODEL: Stopping controller")
        self.controllerThread.terminate()

    def startIndex(self):
        log("MODEL: Starting index")

        self._index = calindex(settings["dataPath"],
                              inputq = self._index_i,
                              outputq= self._index_o,
                              event  = self._event,
                              )

        self.indexThread = multiprocessing.Process(target=self._index.run)
        self.indexThread.start()

    def stopIndex(self):
        log("MODEL: Stopping index")
        self.indexThread.terminate()


    def stopIcsDownload(self):
        log("MODEL: Stopping icsDownloadThread")
        if self.icsDownloadThread:
            # if alive, don't interrupt
            while self.icsDownloadThread.is_alive(): 
                self.message("Waiting for ICS update to finish")
                time.sleep(0.1)
            self.icsDownloadThread.terminate()


    def startView(self):
        log("MODEL: Starting view")
        self.viewThread = multiprocessing.Process(target=self._view.run)
        self.viewThread.start()

    def stopView(self):
        log("MODEL: Stopping view")
        self.viewThread.terminate()

    def processResize(self):
        message = {}
        message["type"] = "resize"
        self._view_i.put(message)

    def collectViewUpdates(self):
        """ View sends updates, update variables
        """
        # get most recent message
        while not self._view_o.empty():
            update = self._view_o.get()
            self._state_viewUpdates.update(update)



    def run(self):

        # download updates on startup
        # self._act_icsUpdate()

        self.updateContent()

        # launch threads
        self.startController()
        self.startView()

        self.processResize()
        self._sendGridFocusUpdate()


        while True:
            self._event.wait()
            self._event.clear()

            while not self._char_queue.empty():
                if time.time()-self._messageTime>self._messageTimeout:
                    self.message(f"")
                char = self._char_queue.get()
                log("Char:",char,chr(char))
                if chr(char) in self._hotkeyMap.keys():
                    command = self._hotkeyMap[chr(char)]["function"]
                    self._commandMap[command](None)
                if char==410: #resize
                    self.processResize()

                self._index_i.put({"type":"ping"})

            # updates from ICS download
            iEvent=0
            while not self._icsDownload_o.empty():
                update = self._icsDownload_o.get()
                if update["type"] == "icsEvents":
                    self.message(f"Downloading: {update['name']}")
                    for event in update["events"]:
                        iEvent+=1
                        self._index_i.put({"type":"addEvent","event":event})
                self.message(f"Synchronized {iEvent} events: {update['name']}")
                self.updateContent()

            while not self._index_o.empty():
                update = self._index_o.get()

                if update["type"] == "getEventsOnDays":
                    self._contents = defaultdict(lambda:defaultdict(lambda:{"events":[],"dt":dt}))
                    eventsByDay = update["eventsByDay"]
                    for dt,events in eventsByDay.items():
                        iWeek = self._dtToNumber[dt][0]
                        iDay  = self._dtToNumber[dt][1]
                        self._contents[iDay][iWeek]["events"]+=events

                    self._updateDays()
                    self._act_select(0) # update focus for new day content

                elif update["type"] == "error":
                    status = update["status"]
                    self.message(f"Index error: {status}")

                elif update["type"] == "message":
                    status = update["status"]
                    self.message(f"Index: {status}")

                # debugging
                # elif update["type"] == "confirm":
                #     action = update["action"]
                #     result = update["result"]
                #     self.message(f"{action}: {result}")


