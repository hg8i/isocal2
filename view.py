from setup import *
import drawing

class view:
    def __init__(self,screen,inputq=None,outputq=None):
        self._screen = screen
        self._input = inputq
        self._output = outputq

        self._lastScreenY,self._lastScreenX = None,None

        self._colorCommand = 1
        self._colorList = 2
        self._colorGrid = 3
        curses.init_pair(1, settings["fgColorCommandView"],settings["bkColorCommandView"])
        curses.init_pair(2, settings["fgColorListView"],settings["bkColorListView"])
        curses.init_pair(3, settings["fgColorGridView"],settings["bkColorGridView"])

        self._commandScreen = None
        self._listScreen = None
        self._gridScreen = None

        self.rescaleCheck()

    def run(self):

        while True:
            # log("VIEW: run loop")

            update = self._input.get()
            if update["type"]=="quit":
                return

            if update["type"]=="resize":
                self.rescaleCheck(force=True)
                # self.rescaleCheck(force=True)

    # ==================================================
    # Clear screen functions
    # ==================================================

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
        log("VIEW: updateCommandScreen")
        self._commandScreen.erase()
        screenY,screenX = self._commandScreen.getmaxyx()
        drawing._drawBox(self._commandScreen,0,0,screenY,screenX," ",self._colorCommand)
        # self.updateCommandData()
        self._commandScreen.refresh()

    def updateListScreen(self):
        """ Update list view
        """
        log("VIEW: updatelistScreen")
        self._listScreen.erase()
        screenY,screenX = self._listScreen.getmaxyx()
        drawing._drawBox(self._listScreen,0,0,screenY,screenX," ",self._colorList)
        # self.updateListData()
        self._listScreen.refresh()

    def updateGridScreen(self):
        """ Update grid view
        """
        log("VIEW: updategridScreen")
        self._gridScreen.erase()
        screenY,screenX = self._gridScreen.getmaxyx()
        drawing._drawBox(self._gridScreen,0,0,screenY,screenX," ",self._colorGrid)
        self.updateGridData()
        self._gridScreen.refresh()

    def updateGridData(self):
        screenY,screenX = self._gridScreen.getmaxyx()
        s = self._gridScreen
        c = self._colorGrid
        yLines = []
        xLines = []

        # outer box
        nDaysX = settings["nDaysX"]
        nWeeksY = settings["nWeeksY"]
        xGrid = settings["gridMarginL"]
        yGrid = settings["gridMarginT"]
        wGrid = screenX-settings["gridMarginL"]-settings["gridMarginR"]
        wGrid = nDaysX*math.floor(wGrid/nDaysX) # round to box width
        hGrid = screenY-settings["gridMarginT"]
        hGrid = nWeeksY*math.floor((hGrid-3)/nWeeksY)+2 # round to box height
        log(screenY,screenX)
        log(yGrid,xGrid,hGrid,wGrid)
        yLines.append(yGrid)
        yLines.append(yGrid+hGrid)
        xLines.append(xGrid)
        xLines.append(xGrid+wGrid)
        drawing._drawBoxOutline(s,yGrid,xGrid,hGrid,wGrid," ",c)

        # day label line
        yLines.append(yGrid+2)
        drawing._hline(s,yGrid+2,xGrid+1,wGrid-1,color=c)

        # draw week lines
        nLines = hGrid-2 
        linesPerWeek = math.floor(nLines/nWeeksY)
        for iWeek in range(1,nWeeksY):
            y = yGrid+2+linesPerWeek*iWeek
            yLines.append(y)
            drawing._hline(s,y,xGrid+1,wGrid-1,color=c)

        # draw day lines
        nCols = wGrid
        colsPerDay = math.floor(nCols/nDaysX)
        for iDay in range(1,nDaysX):
            x = xGrid+colsPerDay*iDay
            xLines.append(x)
            drawing._vline(s,yGrid+1,x,hGrid-1,color=c)

        # draw intersects
        for y in yLines:
            for x in xLines:
                drawing._drawIntersect(s,y,x,"x",color=c)

    def rescaleCheck(self,force=False):
        """ Rescale """
        # log(f"VIEW: rescale (forced={force})")
        screenY,screenX = self._screen.getmaxyx()
        log(f"VIEW: {screenY} {screenX}")
        if self._lastScreenY!=screenY or self._lastScreenX!=screenX or force:
            log("VIEW: doing rescale")

            self.clearScreens()

            self.makeScreens()

            self.updateCommandScreen()
            self.updateListScreen()
            self.updateGridScreen()


    def makeScreens(self):
        log("VIEW: making screens")
        self._screen.clear()
        screenY,screenX = self._screen.getmaxyx()

        listHeight = settings["listHeight"]
        gridHeight = screenY-2-listHeight

        # subwin(nlines, ncols, begin_y, begin_x)
        self._commandScreen = self._screen.subwin(1,screenX,screenY-1,0)
        self._gridScreen = self._screen.subwin(gridHeight,screenX,0,0)
        self._listScreen = self._screen.subwin(listHeight,screenX,gridHeight+1,0)

        self._lastScreenY,self._lastScreenX = screenY,screenX
        self._commandScreen.refresh()
        self._gridScreen.refresh()
        self._listScreen.refresh()
