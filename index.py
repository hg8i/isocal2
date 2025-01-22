# import dill as pickle
import os
from datetime import datetime
import time
from collections import defaultdict

"""
This class manages the index of cal data.
Features:
    * Manage IO to avoid losses
    * Searching
    * Editing
    * Load repeating events
"""

def log(*text):
    global logon
    # if not logon: return
    f = open("log.txt","a")
    text = " ".join([str(t) for t in text])
    f.write(str(text)+"\n")
    f.close()


def dummyEvent(dt):
    event = eventdata()
    event["name"] = str(dt.day)
    event["category"] = str(dt)
    event["date"] = dt
    return event

class eventdata:
    def __init__(self,stringRep=""):
        self.delim0 = "="
        self.delim1 = ","
        self.ics = False

        self.delim0Mask = "_?subEqs?_"
        self.delim1Mask = "_?subCom?_"

        # If string rep is given, load from that
        if stringRep:
            stringRep = stringRep.strip()
            for pair in stringRep.split(self.delim1):
                pair = pair.split(self.delim0)
                k = pair[0]
                if len(pair)!=2: v = ""
                else: v = pair[1]
                # unmask values
                v = v.replace(self.delim0Mask,self.delim0)
                v = v.replace(self.delim1Mask,self.delim1)
                if k in ["date"]:
                    v = datetime.strptime(v,"%Y-%m-%d")
                elif k in ["created","modified"]:
                    v = float(v)

                setattr(self,k,v)
        else:
            self.name="noname"
    
    def __getitem__(self,k):
        return getattr(self,k)

    def __setitem__(self,k,v):
        # sanitize
        # if isinstance(v,str):
        #     v = v.replace("=",self.delim0)
        #     v = v.replace(",",self.delim1)
        setattr(self,k,v)

    def keys(self):
        return dir(self)

    def __lt__(self,other):
        stime = "time" in self.keys()
        otime = "time" in other.keys()
        if stime and otime:
            return self.time<other.time
        elif stime:
            return False
        elif otime:
            return True
        else:
            return self.name<other.name

    def __eq__(self,other):
            return self.uniqueid<other.uniqueid

    def __str__(self):
        return self.name

    def __repr__(self):
        s = ""
        for k,v in self.__dict__.items():
            if "delim" in k: continue
            if k=="date":
                v = v.strftime('%Y-%m-%d')
            # mask deliminators before generating representation
            v = str(v)
            v = v.replace(self.delim0,self.delim0Mask)
            v = v.replace(self.delim1,self.delim1Mask)
            s+=f"{k}{self.delim0}{v}{self.delim1}"
        return s[:-1]


class calindex:
    def __init__(self,pickleDir,outputq=False,inputq=False,event=False):
        self._event      = event
        self._output     = outputq
        self._input      = inputq  
        self._pickleDir  = pickleDir
        self._data       = {}
        self._modtimeAtLoad  = {}
        self._ids        = defaultdict(list) # created dynamic
        self._modifiedYears = defaultdict(int)
        self.maxDepth = 5

    # def idExists(self,year,uniqueid):
    #     """ check if id exists, stored in file """
    #     path = os.path.join(self._pickleDir,f"ids.txt")
    #     self._load(year)
    #     return uniqueid in self._ids[year]

    def run(self):
        log(f"INDEX: running")

        while True:
            update = self._input.get()
            # log(f"DEBUG INDEX: update={update}")
            if update["type"]=="quit":
                return

            if update["type"]=="ping":
                log("DEBUG index got ping")
                data = {"type":"debug"}
                self._output.put(data)

            if update["type"]=="addEvent":
                data = {}
                data["type"] = "confirm"
                data["action"] = "addEvent"
                data["result"] = self.addEvent(update["event"])
                self._output.put(data)
                self._event.set()
            if update["type"]=="delEvent":
                data = {}
                data["type"] = "confirm"
                data["action"] = "delEvent"
                data["result"] = self.delEvent(update["event"])
                self._output.put(data)
                self._event.set()
            if update["type"]=="modEvent":
                data = {}
                data["type"] = "confirm"
                data["action"] = "modEvent"
                result = self.modEvent(update["event"])
                self._output.put(data)
                self._event.set()
            if update["type"]=="getEventsOnDays":
                data = {}
                data["type"] = "getEventsOnDays"
                data["eventsByDay"] = self.getEventsOnDays(update["days"])
                self._output.put(data)
                self._event.set()

            if update["type"]=="searchByString":
                log("INDEX: searching",update["target"])
                data = {}
                data["type"] = "searchResult"
                data["hits"] = self.searchByString(update["target"])
                self._output.put(data)
                self._event.set()

    def searchByString(self,target):
        """ Search by string """
        # search first for this year
        lTarget = target.lower().split()
        matches = []
        for year in self._data.keys():
            log(f"INDEX: searching year {year}")
            for day in self._data[year].keys():
                for event in self._data[year][day]:

                    if len(lTarget)==0:
                        matches.append(event)
                    if all([s in repr(event).lower() for s in lTarget]):
                        matches.append(event)

                    # matches+=self._data[year][day]
        log(f"INDEX: searching matches {matches}")
        return matches


    def getDaysWithEvents(self,start,end):
        """ Return days with events between start, end datetimes, inclusive """
        startYear = start.year
        endYear   = end.year
        years = range(startYear,endYear+1)
        assert startYear<=endYear
        # Ensure that the years are loaded
        [self._load(y) for y in years]
        # get list of days with events between start and end
        days = []
        for year in years:
            f = lambda d: d>=start and d<=end
            daysThisYear = [d for d in self._data[year].keys() if f(d)]
            days+=daysThisYear

        return days

    def getEventsOnDays(self,days):
        """ Return events on days as dictionary """
        ret = {}
        # self.synchronize()
        # log("Index retrieving days")
        # log("="*50)
        for day in days:
            ret[day] = self.getEventsOnDay(day)
            # log(day,ret[day])
        # log("="*50)
        return ret

    def getEventsOnDay(self,day):
        """ Return events on day """

        self.synchronize(day.year)

        # # testing: events with day number 
        # return [dummyEvent(day)]

        year = day.year
        self._load(year)
        if day in self._data[year].keys():
            return sorted(self._data[year][day])
        else:
            return []

    def unaware(self,event):
        """ Remove timezone, time info (since not used) """
        if event.date.tzinfo is not None:
            event.date = event.date.replace(tzinfo=None,hour=0,minute=0,second=0)

    def addEvent(self,event,depth=1):
        """ Add this event, update modification time, update self._ids"""
        if depth>self.maxDepth: return "exceedDepth"
        log("-"*50)
        log(f"INDEX: Adding event: {event}")
        # self.unaware(event)
        dt = event["date"]
        uniqueid = event["uniqueid"]
        year = event["date"].year
        self._load(year)
        # if already exists, return
        if uniqueid in self._ids[year]:
            # ID already added, skip
            log(f"INDEX: skipping existing event {event}")
            return "skip adding existing event"
        else:
            self._ids[year].append(uniqueid)
        # assert uniqueid not in self._data[year]
        if dt not in self._data[year].keys():
            self._data[year][dt] = []
        # insert to dt dictionary
        self._data[year][dt].append(event)
        log(f"INDEX: Updated list: {self._data[year][dt]}")
        log(f"INDEX: Updated year: {year}")
        log(f"INDEX: Updated dt: {dt}")
        # update modification time
        self._modifiedYears[year]+=1
        if not self._save(): self.addEvent(event,depth+1)
        log("-"*50)
        return f"added event {depth}"

    def delEvent(self,event,depth=1):
        """ Delete this event, update modification time, update self._ids"""
        if depth>self.maxDepth: return "exceedDepth"
        log(f"INDEX: Deleting event {event}")
        dt = event["date"]
        uniqueid = event["uniqueid"]
        year = event["date"].year
        self._load(year)
        if uniqueid not in self._ids[year]:
            # ID doesn't exist, skip
            return "delete failed uniqueid check"
        else:
            self._ids[year].pop(self._ids[year].index(uniqueid))
        # delete event from day's list, by index
        idMatches = [e["uniqueid"]==uniqueid for e in self._data[year][dt]]
        if sum(idMatches)!=1:
            log("="*50)
            log("crash")
            for e in self._data[year][dt]:
                log(e)
                log(e["uniqueid"])
                log(e["created"])
                log("-"*50)
            raise Exception(f"Incorrect number of ID matches during deletion: {sum(idMatches)}")
        i = idMatches.index(True)
        self._data[year][dt].pop(i)
        # update modification time
        self._modifiedYears[year]+=1
        if not self._save(): self.delEvent(depth+1)
        return f"deleted event {depth}"

    def modEvent(self,event,depth=1):
        """ Modify this event, update modification time """
        if depth>self.maxDepth: return "exceedDepth"
        log(f"INDEX: modified event cat={event['category']}")
        year = event["date"].year
        dt = event["date"]
        uniqueid = event["uniqueid"]
        # identify and update event
        for iTarget,target in enumerate(self._data[year][dt]):
            if target.uniqueid==uniqueid:
                self._data[year][dt][iTarget] = event
                break


        self._modifiedYears[year]+=1
        if not self._save(): self.modEvent(event,depth+1)
        return f"modified event {depth}"

    def _getPath(self,year):
        path = os.path.join(self._pickleDir,f"{year}.csv")
        return path

    def _loadFile(self,path):
        """ Load and parse csv file """
        iFile =  open(path,"r")
        events = [eventdata(l) for l in iFile.readlines() if l[0]!="#"]
        data = defaultdict(list)
        for event in events:
            # log("DEBUG:",event)
            data[event.date].append(event)
        iFile.close()
        return data

    def _load(self,year):
        """ Load this year """
        if year in self._data.keys(): return
        log(f"INDEX: Loading year {year}")
        path = self._getPath(year)
        if not os.path.exists(path):
            self._modtimeAtLoad[year] = None
            self._data[year] = {}
        else:
            self._modtimeAtLoad[year] = os.path.getmtime(path)
            self._data[year] = self._loadFile(path)
            # add uniqueids
            self._ids[year] = [e["uniqueid"] for events in self._data[year].values() for e in events]
            # self._ids[year] = [e["uniqueid"] for e in events]

    def synchronize(self,year):
        log(f"INDEX: <synchronize> year {year}")
        path = self._getPath(year)

        # if year is not loaded, no sync needed
        if year not in self._data.keys():
            log(f"INDEX: <synchronize> year not loaded, no sync")
            return False

        # If file doesn't exist, or was deleted, etc, no synch needed
        if not os.path.exists(path):
            log(f"INDEX: <synchronize> path not exist, no sync")
            return False

        # log(f"INDEX: <synchronize> {self._modtimeAtLoad[year]}")
        boolFileModified  = self._modtimeAtLoad[year] and os.path.getmtime(path)>self._modtimeAtLoad[year]
        if boolFileModified:
            # if file has been modified,
            # 1) delete loaded data (including changes)
            # 2) re-load data
            # 3) return true
            log(f"INDEX: <synchronize> reload")
            del self._data[year]
            self._load(year)
            return True
        return False


    def _save(self):
        """ Save changes based on _modifiedYears """
        # Return True if successful
        log(f"INDEX: Saving to {self._pickleDir}")
        for year in self._modifiedYears.keys():
            # save data for this year
            path = self._getPath(year)
            if self.synchronize(year):
                return False
            if len(self._data[year])==0: continue
            log(f"INDEX: Saving {year} to {path}")
            with open(path,"w") as oFile:
                oFile.write(f"# Year {year}, created {datetime.now()} \n")
                for day,events in self._data[year].items():
                    oFile.write(f"## Day {day}\n")
                    for event in events:
                        oFile.write(repr(event)+"\n")
                self._modtimeAtLoad[year] = os.path.getmtime(path)
        return True

    def load(self,oFile):
        """ Replacement for pickle load """
        return {}

    def __str__(self):
        s = "Calendar index\n"
        for year,data in self._data.items():
            s+=f"* Year: {year}\n"
            for d,e in self._data[year].items():
                s+=f"  * Day: {d}\n"
                for ee in e:
                    # s+=f"    * Event: {ee['name']} {repr(ee['category'])}\n"
                    s+=f"    * Event: {repr(ee)}\n"
        return s[:-1]

def eventHelper(dt):
    r = lambda: ["Replace", "the", "list", "with", "your", "desired", "words", "or", "use", "a", "dictionary", "file", "for", "a", "larger", "selection"][random.randint(0,10)]
    ret = eventdata()
    ret["name"] = r()
    ret["date"] = dt
    ret["uniqueid"] = time.time()
    ret["created"] = time.time()
    ret["modified"] = time.time()
    ret["category"] = ["home","work","crit"][random.randint(0,2)]
    ret["time"] = f"0{random.randint(1,9)}00" if random.randint(0,4) else ""
    ret["notes"] = r()
    return ret

if __name__=="__main__":
    import random
    # os.popen("rm data/*")
    i = calindex("data")

    # for x in range(100):
    #     i.addEvent(eventHelper(datetime(2025,1,random.randint(1,26))))
    for x in range(4):
        i.addEvent(eventHelper(datetime(2025,1,12)))

    # ev = eventHelper(datetime(2023,2,6))
    # i.addEvent(ev)
    # i.delEvent(ev)

    os.popen("touch data/2025.csv").read()

    for x in range(4):
        i.addEvent(eventHelper(datetime(2025,1,12)))


    s = datetime(2023,1,1)
    e = datetime(2025,1,1)
    days = i.getDaysWithEvents(s,e)
    # print(i)
    # print(days)

    # d = datetime.datetime(2023,1,1)

    # event = {}
    # event["name"] = "name test"
    # event["category"] = "work"
    # event["time"] = None
    # event["note"] = "This is the note"
    # i.setEvent(d,event)
