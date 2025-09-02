from setup import *
import drawing

overflow = "…"
cursor = "◆"
uparrow = "↑"
dnarrow = "↓"
larrow = "←"
rarrow = "→"
today = "◆"
# today = "x"

def eventToString(event,full=False):
    if "name" not in event.keys():
        return "INVALID EVENT"
    if not full:
        return event["name"]

    s = ""
    if "time" in event.keys() and event["time"]:
        s+=f'{event["time"]}: '
    else:
        s+=">> "

    s+=event["name"]

    if "notes" in event.keys() and event["notes"]:
        s+=f' - {event["notes"]}'

    return s

def eventToStringSearch(event,full=False):
    if "name" not in event.keys():
        return "INVALID EVENT"
    if not full:
        return event["name"]

    s = ""
    s+=event["date"].strftime("%d-%m-%y")
    s+= ": "

    s+=event["name"]

    if "notes" in event.keys() and event["notes"]:
        s+=f' - {event["notes"]}'

    return s


def eventToColor(event):
    if "category" not in event.keys():
        return settings["colors"]["eventDefault"]
    elif event["category"] not in settings["colors"].keys():
        return settings["colors"]["invalidCategory"]
    else:
        return settings["colors"][event["category"]]

class dayView:
    def __init__(self,screen,x,y,w,h,color=1,focusColor=1,firstDayColor=1):
        h = max(1,h)
        self._color = color
        self._focusColor = focusColor
        self._firstDayColor = firstDayColor

        # create screen
        self._screen = screen.subwin(h,w,y,x)
        screenY,screenX = self._screen.getmaxyx()
        drawing._drawBox(self._screen,0,0,screenY,screenX," ",self._color)


    def setContent(self,dayNumber,events,focusMap=None,isToday=False):
        """ Content is list """
        screenY,screenX = self._screen.getmaxyx()
        if dayNumber==1:
            drawing._text(self._screen,0,0,dayNumber,color=self._firstDayColor)
        else:
            drawing._text(self._screen,0,0,dayNumber,color=self._color)
        if isToday:
            drawing._text(self._screen,0,screenX-1,today,color=self._color)
        for iEvent,event in enumerate(events):
            if iEvent==screenY-1: 
                drawing._text(self._screen,0,screenX-2,overflow,color=self._color)
                break
            y = 1+iEvent
            x = 0
            if focusMap and focusMap[iEvent]:
                color = self._focusColor
            elif focusMap:
                color = self._color
            else:
                color = eventToColor(event)
            drawing._text(self._screen,y,x,event,color=color,bold=True)

    def update(self):
        # self._screen.erase()
        screenY,screenX = self._screen.getmaxyx()
        # drawing._drawBox(self._screen,0,0,screenY,screenX," ",self._color)
        self._screen.refresh()

class view:
    def __init__(self,screen,inputq=None,outputq=None,nDaysX=7,nWeeksY=4,iDayFocus=0,iWeekFocus=0):
        self._screen = screen
        self._input = inputq
        self._output = outputq

        self._lastScreenY,self._lastScreenX = None,None

        self._commandData = False
        self._dialog = False
        self._search = False
        self._dialogFocus = False
        self._iDayToday = 1
        self._iWeekToday = 1
        self._iDayFocus = iDayFocus
        self._iWeekFocus = iWeekFocus
        self._iContentFocus = 0
        self._nDaysX = nDaysX
        self._nWeeksY = nWeeksY
        self._content = defaultdict(lambda:defaultdict(list))
        self._content_dt = defaultdict(lambda:defaultdict(lambda:now()))
        self._days = defaultdict(lambda:defaultdict(list))
        self._weekNumbers = []
        self._monthNames = []
        self._yearNames = []

        self._colorCommand      = settings["colors"]["commandView"]
        self._colorList         = settings["colors"]["listView"]
        self._colorGrid         = settings["colors"]["gridView"]
        self._colorDayNames     = settings["colors"]["dayNames"]
        self._colorDay          = settings["colors"]["gridView"]
        self._colorDayFocus     = settings["colors"]["highlight"]
        self._colorContentFocus = settings["colors"]["contentFocus"]
        self._colorSearchFocus  = settings["colors"]["searchFocus"]
        self._colorSearch       = settings["colors"]["searchView"]
        self._colorDialogFocus  = settings["colors"]["dialogFocus"]
        self._colorDialog       = settings["colors"]["dialogView"]
        self._firstDayColor     = settings["colors"]["firstDay"]

        self._commandScreen = None
        self._listScreen = None
        self._gridScreen = None

        self.rescaleCheck()

    def ensureList(self,l):
        if not isinstance(l,list):
            return [l]
        return l


    def run(self):

        while True:
            # log("VIEW: run loop")

            update = self._input.get()
            if update["type"]=="quit":
                return

            if update["type"]=="resize":
                self.rescaleCheck(force=True)

            if update["type"]=="message":
                self._commandData = update["value"]
                self.updateCommandScreen()

            if update["type"]=="updatevalue":
                key    = self.ensureList(update["key"])
                value  = self.ensureList(update["value"])
                redraw = update["redraw"]
                assert len(key)==len(value)
                for k,v in zip(key,value):
                    setattr(self,k,v)
                if redraw=="grid":
                    self.updateGridScreen()
                    self.updateListScreen()
                if redraw=="dialog":
                    self.updateDialogScreen()
                if redraw=="search":
                    self.updateSearchScreen()

            if update["type"]=="updateday":
                iDays  = self.ensureList(update["iDay"])
                iWeeks = self.ensureList(update["iWeek"])
                contents = self.ensureList(update["content"])

                for iDay,iWeek,content in zip(iDays,iWeeks,contents):
                    self._content_dt[iDay][iWeek] = content["dt"]
                    self._content[iDay][iWeek] = content["events"]

                self.updateGridScreen()
                self.updateListScreen()
                # TODO: fix articacts
                # redraw day
                # self._days[iDay][iWeek]._screen.erase()
                # self._days[iDay][iWeek]._screen.refresh()

            if update["type"]=="dialog":
                if update["instruction"]=="launch":
                    self.launchDialog(update)
                elif update["instruction"]=="close":
                    self.closeDialog(update)

            if update["type"]=="search":
                if update["instruction"]=="launch":
                    self.launchSearch(update)
                elif update["instruction"]=="close":
                    self.closeSearch(update)

    # ==================================================
    # Dialog functions
    # ==================================================

    def closeDialog(self,update):
        """ Close dialog window based on update data """
        self._dialog = False
        self._dialogFocus = False
        self.makeScreens()
        self.updateScreens()

    def launchDialog(self,update):
        """ Launch dialog window based on update data """
        self._dialog = True
        self._dialogFocus = 0
        self._dialogCursorPos = -1
        self._dialogFields = update["lines"]
        self._dialogTitle = " :"+update["title"]+": "
        self.makeScreensDialog()
        self.updateDialogScreen()

    def updateDialogScreen(self):
        """ Update grid view
        """
        # log("VIEW: updateDialogScreen")
        if not self._dialog: return
        self._dialogScreen.erase()
        screenY,screenX = self._dialogScreen.getmaxyx()
        drawing._drawBox(self._dialogScreen,0,0,screenY,screenX," ",self._colorDialog)
        drawing._drawBoxOutline(self._dialogScreen,0,0,screenY-1,screenX-1," ",self._colorDialog)
        self.updateDialogData()
        self._dialogScreen.refresh()

    def closeSearch(self,update):
        """ Close search window """
        self._search = False
        self._searchFocus = False
        self.makeScreens()
        self.updateScreens()

    def launchSearch(self,update):
        """ Launch search window """
        self._search = True
        self._searchText = ""
        self._searchEvents = []
        self._searchFocus = False
        self._searchCursorPos = -1
        self._searchTitle = " :"+update["title"]+": "
        self.makeScreensSearch()
        self.updateSearchScreen()

    def updateSearchScreen(self):
        """ Update grid view
        """
        # log("VIEW: updateSearchScreen")
        if not self._search: return
        self._searchScreen.erase()
        screenY,screenX = self._searchScreen.getmaxyx()
        drawing._drawBox(self._searchScreen,0,0,screenY,screenX," ",self._colorSearch)
        drawing._drawBoxOutline(self._searchScreen,0,0,screenY-1,screenX-1," ",self._colorSearch)
        self.updateSearchData()
        self._searchScreen.refresh()

    def updateSearchData(self):
        if not self._search: return
        screen = self._searchScreen
        colorMain = self._colorSearch
        colorFocus = self._colorSearchFocus
        screenY,screenX = screen.getmaxyx()
        centeredPos = int((screenX-len(self._searchTitle))/2)
        drawing._text(screen,0,centeredPos,self._searchTitle,color=colorMain)

        # input text box
        drawing._text(screen,2,2,self._searchText,color=colorMain)
        # if len(self._searchText):
        #     drawing._text(screen,2,self._searchCursorPos,"█",color=colorMain)
        drawing._drawBoxOutline(screen,1,1,2,screenX-3," ",colorMain)

        iContent = self._searchFocus
        maxLines = screenY-5
        if iContent>=maxLines:
            scroll = iContent-maxLines+1
        else:
            scroll = 0
        # permute and trim lines to display
        events = self._searchEvents
        displayEvents = events[scroll:]+events[:scroll]
        displayEvents = displayEvents[:maxLines]

        # search results
        maxLen = screenX-4
        for iEvent,event in enumerate(displayEvents):
            # color = eventToColor(event)
            color = colorMain
            eventName = eventToStringSearch(event,full=True)
            x = 2
            y = 4+iEvent
            log("drawing search event",x,y,eventName)
            if iEvent+scroll==iContent:
                color = self._colorContentFocus
                # drawing._text(screen,y,x-2,cursor,color=self._colorDay)
            if len(eventName)>maxLen:
                eventName=eventName[:maxLen-1]+overflow
            drawing._text(screen,y,x,eventName,color=color)

        # draw dotted dots lines if some lines not displayed
        if scroll:
            drawing._text(screen,4,screenX-1,uparrow,color=colorMain)
        if len(events)>maxLines and scroll+maxLines<len(events):
            drawing._text(screen,screenY-1,screenX-1,dnarrow,color=colorMain)

        # s = f"DEBUG: {iContent}, {len(self._searchEvents)}"
        # drawing._text(screen,0,0,s,color=colorMain)


    def updateDialogData(self):
        if not self._dialog: return
        screenY,screenX = self._dialogScreen.getmaxyx()
        screen = self._dialogScreen
        colorMain = self._colorDialog
        if len(self._dialogFields)==0:
            self._dialogFields = [{"name":"","content":""}]
        nameLength = max([len(i["name"]) for i in self._dialogFields if i["type"]!="divider"])+1
        contentLength = screenX-nameLength-4
        switchLen = 8
        centeredPos = int((screenX-len(self._dialogTitle))/2)
        drawing._text(screen,0,centeredPos,self._dialogTitle,color=colorMain)
        y = 2
        for iField,field in enumerate(self._dialogFields):
            name = field["name"]
            if "content" not in field.keys():
                content = False
            else:
                content = field["content"]

            if iField==self._dialogFocus:
                color = self._colorDialogFocus
            else:
                color = colorMain


            if field["type"] == "label":
                drawing._text(screen,y-1,2,name,color=colorMain)
                if content: drawing._text(screen,y-1,nameLength+3,content,color=colorMain)
                y+=1
            elif field["type"] == "divider":
                drawing._text(screen,y-1,1,name,color=colorMain)
                drawing._text(screen,y-1,len(name)+2,content[0]*(screenX-len(name)-3),color=colorMain)
                y+=1
            elif field["type"] == "text":
                drawing._text(screen,y,2,name,color=colorMain)
                drawing._drawBoxOutline(screen,y-1,nameLength+2,2,contentLength," ",color)
                if content: drawing._text(screen,y,nameLength+3,content,color=colorMain)
                # draw cursor
                if iField==self._dialogFocus and self._dialogCursorPos>=0:
                    drawing._text(screen,y,nameLength+2+self._dialogCursorPos,"█",color=color)
                y+=3
            elif field["type"] == "map":
                mapLen = 2+max([len(l) for l in field["list"]])
                drawing._text(screen,y,2,name,color=colorMain)
                drawing._drawBoxOutline(screen,y-1,nameLength+2,2,mapLen," ",color)
                drawing._text(screen,y,nameLength+3,field["list"][content],color=color)
                drawing._text(screen,y,nameLength+mapLen+3,"(+/-)",color=colorMain)
                y+=3
            elif field["type"] == "int":
                drawing._text(screen,y,2,name,color=colorMain)
                drawing._drawBoxOutline(screen,y-1,nameLength+2,2,switchLen," ",color)
                drawing._text(screen,y,nameLength+3,content,color=color)
                drawing._text(screen,y,nameLength+switchLen+3,"(+/-)",color=colorMain)
                y+=3
            elif field["type"] == "radio":
                drawing._text(screen,y,2,name,color=colorMain)
                drawing._drawBoxOutline(screen,y-1,nameLength+2,2,switchLen," ",color)
                if content:
                    drawing._text(screen,y,nameLength+3," on  ██",color=color)
                else:
                    drawing._text(screen,y,nameLength+3,"██ off ",color=color)
                y+=3
            else:
                drawing._text(screen,y,2,"invalid dialog type",color=colorMain)
                y+=1



    # ==================================================
    # Clear screen functions
    # ==================================================

    def clearDialogScreen(self):
        """ clear dialog view
        """
        log("VIEW: clearDialogScreen")
        if self._dialogScreen:
            self._dialogScreen.erase()
            self._dialogScreen.refresh()

    def clearCommandScreen(self):
        """ clear command view
        """
        log("VIEW: clearCommandScreen")
        if self._commandScreen:
            self._commandScreen.erase()
            self._commandScreen.refresh()

    def clearListScreen(self):
        """ clear list view
        """
        log("VIEW: clearlistScreen")
        if self._listScreen:
            self._listScreen.erase()
            self._listScreen.refresh()

    def clearGridScreen(self):
        """ clear grid view
        """
        log("VIEW: cleargridScreen")
        if self._gridScreen:
            self._gridScreen.erase()
            self._gridScreen.refresh()

    def clearScreens(self):
        self.clearCommandScreen()
        self.clearListScreen()
        self.clearGridScreen()

    # ==================================================
    # Update screen functions
    # ==================================================

    def updateCommandScreen(self):
        """ Update command view
        """
        # log("VIEW: updateCommandScreen")
        self._commandScreen.erase()
        screenY,screenX = self._commandScreen.getmaxyx()
        drawing._drawBox(self._commandScreen,0,0,screenY,screenX," ",self._colorCommand)
        self.updateCommandData()
        self._commandScreen.refresh()

    def updateCommandData(self):
        screenY,screenX = self._commandScreen.getmaxyx()
        s = self._commandScreen
        c = self._colorCommand
        if self._commandData:
            line = self._commandData
            drawing._text(s,0,0,line,color=c)


    def updateListScreen(self):
        """ Update list view
        """
        # log("VIEW: updatelistScreen")
        self._listScreen.erase()
        screenY,screenX = self._listScreen.getmaxyx()
        drawing._drawBox(self._listScreen,0,0,screenY,screenX," ",self._colorList)
        self.updateListData()
        self._listScreen.refresh()

    def updateListData(self):
        screenY,screenX = self._listScreen.getmaxyx()
        s = self._listScreen
        c = self._colorGrid

        # collect info
        iDay = self._iDayFocus
        iWeek = self._iWeekFocus
        iContent = self._iContentFocus
        events = self._content[iDay][iWeek]

        # draw border
        nMargin   = settings["listMarginN"]
        sMargin   = settings["listMarginS"]
        eMargin   = settings["listMarginE"]
        wMargin   = settings["listMarginW"]
        width     = screenX-eMargin-wMargin
        height    = screenY-nMargin-sMargin
        drawing._drawBoxOutline(s,nMargin,wMargin,height,width," ",c)

        # fill in lines
        maxLines = height-1
        maxLen = width-3

        if iContent>=maxLines:
            scroll = iContent-maxLines+1
        else:
            scroll = 0

        # permute and trim lines to display
        displayEvents = events[scroll:]+events[:scroll]
        displayEvents = displayEvents[:maxLines]

        for iEvent,event in enumerate(displayEvents):
            # log("DEBUG",type(event),event)
            color = eventToColor(event)
            eventName = eventToString(event,full=True)
            x = wMargin+3
            y = nMargin+1+iEvent
            # log("drawing list event",x,y,eventName)
            if iEvent+scroll==iContent:
                color = self._colorContentFocus
                drawing._text(s,y,x-2,cursor,color=self._colorDay)
            if len(eventName)>maxLen:
                eventName=eventName[:maxLen-1]+overflow
            drawing._text(s,y,x,eventName,color=color)

        # draw dotted dots lines if some lines not displayed
        if scroll:
            drawing._text(s,nMargin,screenX-eMargin-0,uparrow,color=self._colorDay)
        if len(events)>maxLines and scroll+maxLines<len(events):
            drawing._text(s,screenY-sMargin,screenX-eMargin-0,dnarrow,color=self._colorDay)


        # debug = f"DEBUG: scroll={scroll} iContent={iContent} maxLines={maxLines}"
        # drawing._text(s,0,0,debug,color=self._colorDayNames)

    def updateGridScreen(self):
        """ Update grid view
        """
        # log("VIEW: updategridScreen")
        self._gridScreen.erase()
        screenY,screenX = self._gridScreen.getmaxyx()
        drawing._drawBox(self._gridScreen,0,0,screenY,screenX," ",self._colorGrid)
        self.updateGridData()
        self._gridScreen.refresh()



    def updateGridData(self):
        screenY,screenX = self._gridScreen.getmaxyx()
        nWeeksY = self._nWeeksY 
        hGrid   = screenY-settings["gridMarginT"]
        hGrid   = nWeeksY*math.floor((hGrid-3)/nWeeksY)+2 # round to box height
        nLines = hGrid-2 
        linesPerWeek = math.floor(nLines/nWeeksY)
        nextNinesPerWeek = math.floor(nLines/(nWeeksY+1))


        if linesPerWeek>=1:
            self.updateGridData_normal()
        else:
            self.updateGridData_compact()

        # drawing._text(self._gridScreen,0,0,f"DEBUG: lpw={linesPerWeek}, _nWeeksY={self._nWeeksY}",color=self._colorDayNames)

    def updateGridData_compact(self):
        """ Draw grid data in compact calendar style
        """
        screenY,screenX = self._gridScreen.getmaxyx()
        s = self._gridScreen
        c = self._colorGrid

        w = min(40,screenX-8)
        h = min(8,screenY-8)
        x = int((screenX-w)/2)
        y = int((screenY-h)/2)

        iDay = self._iDayFocus
        iWeek = self._iWeekFocus
        lines = self._content[iDay][iWeek]
        dt = self._content_dt[iDay][iWeek]

        dayString = dt.strftime("%d-%m-%Y")
        drawing._text(s,y-2,int((screenX-len(dayString))/2),dayString,color=self._colorDayNames)
        drawing._drawBoxOutline(s,y-1,x-1,h+1,w+1," ",c)
        drawing._text(s,y+int(h/2),x+w+1,rarrow,color=self._colorDayNames)
        drawing._text(s,y+int(h/2),x-2,larrow,color=self._colorDayNames)


        color = self._colorDayFocus
        focusMap = [i==self._iContentFocus for i in range(len(lines))]
        isToday = iDay==self._iDayToday and iWeek==self._iWeekToday

        day = dayView(s,x,y,w,h,color=color,focusColor=self._colorContentFocus,firstDayColor=self._firstDayColor)
        day.setContent(dt.day,lines,focusMap=focusMap,isToday=isToday)
        day._screen.refresh()
        self._days[iDay][iWeek] = day

    def updateGridData_normal(self):
        """ Draw grid data in normal calendar style
        """
        screenY,screenX = self._gridScreen.getmaxyx()
        screen = self._gridScreen
        c = self._colorGrid
        yLines = []
        xLines = []

        # outer box
        nDaysX  = self._nDaysX 
        nWeeksY = self._nWeeksY 
        wMargin   = settings["gridMarginL"]
        nMargin   = settings["gridMarginT"]
        wGrid   = screenX-settings["gridMarginL"]-settings["gridMarginR"]
        wGrid   = nDaysX*math.floor(wGrid/nDaysX) # round to box width
        hGrid   = screenY-settings["gridMarginT"]
        hGrid   = nWeeksY*math.floor((hGrid-3)/nWeeksY)+2 # round to box height
        xCentering = int((screenX)/2)
        yCentering = int((screenY-hGrid)/2)
        yLines.append(yCentering)
        yLines.append(yCentering+hGrid)
        xLines.append(wMargin)
        xLines.append(wMargin+wGrid)

        # yCentering = nMargin+1

        nCols = wGrid
        colsPerDay = math.floor(nCols/nDaysX)

        # # debug status line
        # debug = f"DEBUG: iDay={self._iDayFocus} iWeek={self._iWeekFocus} focus={self._iContentFocus}"
        # drawing._text(screen,0,0,debug,color=self._colorDayNames)

        # box around grid
        drawing._drawBoxOutline(screen,yCentering,wMargin,hGrid,wGrid," ",c)

        # day label line
        yLines.append(yCentering+2)
        drawing._hline(screen,yCentering+2,wMargin+1,wGrid-1,color=c)

        # draw week lines
        nLines = hGrid-2 
        linesPerWeek = math.floor(nLines/nWeeksY)
        drawHorizontalLines = linesPerWeek>1

        if not drawHorizontalLines:
            nWeeksY-=1

        if drawHorizontalLines:
            for iWeek in range(1,nWeeksY):
                y = yCentering+2+linesPerWeek*iWeek
                yLines.append(y)
                drawing._hline(screen,y,wMargin+1,wGrid-1,color=c)


        # draw day lines
        for iDay in range(1,nDaysX):
            x = wMargin+colsPerDay*iDay
            xLines.append(x)
            drawing._vline(screen,yCentering+1,x,hGrid-1,color=c)

        # draw intersects
        for y in yLines:
            for x in xLines:
                drawing._drawIntersect(screen,y,x,"x",color=c)
        # side marks
        for y in yLines:
            drawing._drawIntersect(screen,y,wMargin,"w",color=c)
            drawing._drawIntersect(screen,y,wMargin+wGrid,"e",color=c)
        # # top/bot marks
        for x in xLines:
            drawing._drawIntersect(screen,yCentering,x,"n",color=c)
            drawing._drawIntersect(screen,yCentering+hGrid,x,"s",color=c)
        # corners
        drawing._drawIntersect(screen,yCentering,wMargin,            "nw",color=c)
        drawing._drawIntersect(screen,yCentering,wMargin+wGrid,      "ne",color=c)
        drawing._drawIntersect(screen,yCentering+hGrid,wMargin,      "sw",color=c)
        drawing._drawIntersect(screen,yCentering+hGrid,wMargin+wGrid,"se",color=c)


        # draw names in boxes
        for iDay in range(nDaysX):
            x = wMargin+colsPerDay*iDay
            name = settings["dayNames"][iDay][:colsPerDay-1]
            drawing._text(screen,yCentering+1,x+1,name,color=self._colorDayNames)

        if settings["showTopYears"] and len(self._yearNames):
            yearsMin = min(self._yearNames)
            yearsMax = max(self._yearNames)
            if yearsMin==yearsMax:
                s = f"{yearsMax}"
            else:
                s = f"{yearsMin}-{yearsMax}"
            drawing._text(screen,max(0,yCentering-1),xCentering-int(len(s)/2),s,color=self._colorDayNames)

        # draw week numbers and month names
        monthsDrawn = []
        yearsDrawn = []
        for iWeek in range(nWeeksY):
            y = yCentering+2+linesPerWeek*iWeek+1
            if not drawHorizontalLines: y+=1
            if iWeek<len(self._weekNumbers): 
                drawing._text(screen,y,wMargin-2,self._weekNumbers[iWeek],color=self._colorDayNames)
            if iWeek<len(self._monthNames): 
                monthName = self._monthNames[iWeek]
                if monthName in monthsDrawn: continue
                monthsDrawn.append(monthName)
                for i,ch in enumerate(monthName[:3]):
                    drawing._text(screen,y+i,wMargin-4,ch,color=self._colorDayNames)

            if settings["showSideYears"] and iWeek<len(self._yearNames): 
                yearName = self._yearNames[iWeek]
                if yearName in yearsDrawn: continue
                yearsDrawn.append(yearName)
                for i,ch in enumerate(str(yearName)):
                    drawing._text(screen,y+i,wMargin-6,ch,color=self._colorDayNames)

        # create day screens TODO: move
        for iWeek in range(nWeeksY):
            for iDay in range(nDaysX):
                lines = self._content[iDay][iWeek]
                # dayNumber = self._content_dt[iDay][iWeek] # more debug info
                dayNumber = self._content_dt[iDay][iWeek].day
                x = wMargin+1+colsPerDay*iDay
                y = yCentering+3+linesPerWeek*iWeek
                isToday = iDay==self._iDayToday and iWeek==self._iWeekToday
                if iDay==self._iDayFocus and iWeek==self._iWeekFocus:
                    color = self._colorDayFocus
                    focusMap = [i==self._iContentFocus for i in range(len(lines))]
                else:
                    color = self._colorDay
                    focusMap = None
                # if linesPerWeek<2: continue
                day = dayView(screen,x,y,colsPerDay-1,linesPerWeek-1,color=color,focusColor=self._colorContentFocus,firstDayColor=self._firstDayColor)
                day.setContent(dayNumber,lines,focusMap=focusMap,isToday=isToday)
                day._screen.refresh()
                self._days[iDay][iWeek] = day


    def updateScreens(self):
        self.updateCommandScreen()
        self.updateListScreen()
        self.updateGridScreen()
        self.updateDialogScreen()
        self.updateSearchScreen()

    def rescaleCheck(self,force=False):
        """ Rescale """
        # log(f"VIEW: rescale (forced={force})")
        screenY,screenX = self._screen.getmaxyx()
        log(f"VIEW: {screenY} {screenX}")
        if self._lastScreenY!=screenY or self._lastScreenX!=screenX or force:
            log("VIEW: doing rescale")

            self.clearScreens()

            self.makeScreens()
            self.makeScreensDialog()
            self.makeScreensSearch()
            self.updateScreens()


    def makeScreensDialog(self):
        log("VIEW: making dialog screen")
        if not self._dialog: return
        self._screen.clear()
        screenY,screenX = self._screen.getmaxyx()
        nLabels  = sum([1 for f in self._dialogFields if f["type"] in ["label","divider"]])
        nEntries = sum([1 for f in self._dialogFields if f["type"] in ["int","radio","text","map"]])
        targetW = 60;
        targetH = 2+nEntries*3+nLabels*1
        w = min(targetW,screenX-8)
        h = min(targetH,screenY-8)
        y = int(screenY/2-h/2)
        x = int(screenX/2-w/2)
        self._dialogScreen = self._screen.subwin(h,w,y,x)

    def makeScreensSearch(self):
        log("VIEW: making search screen")
        if not self._search: return
        self._screen.clear()
        screenY,screenX = self._screen.getmaxyx()
        targetW = screenX-10
        targetH = 20
        w = min(targetW,screenX-8)
        h = min(targetH,screenY-8)
        y = int(screenY/2-h/2)
        x = int(screenX/2-w/2)
        self._searchScreen = self._screen.subwin(h,w,y,x)



    def makeScreens(self):
        log("VIEW: making screens")
        self._screen.clear()
        screenY,screenX = self._screen.getmaxyx()

        listHeight = settings["listHeight"]
        gridHeight = screenY-2-listHeight

        # subwin(nlines, ncols, begin_y, begin_x)
        self._commandScreen = self._screen.subwin(1,screenX,screenY-1,0)
        self._gridScreen = self._screen.subwin(gridHeight+1,screenX,0,0)
        self._listScreen = self._screen.subwin(listHeight,screenX,gridHeight+1,0)
        if self._dialog:
            self.makeScreensDialog()

        self._lastScreenY,self._lastScreenX = screenY,screenX
        self._commandScreen.refresh()
        self._gridScreen.refresh()
        self._listScreen.refresh()
        if self._dialog:
            self._dialogScreen.refresh()

        # provide info on screens to model
        data = {}
        data["gridScreenY"] = self._gridScreen.getmaxyx()[0]
        self._output.put(data)
