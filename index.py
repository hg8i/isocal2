import pickle
import os
import datetime
import time

"""
This class manages the index of cal data.
Features:
    * Manage IO to avoid losses
    * Searching
    * Editing
    * Load repeating events
"""

# class defaultdict:
#     def __init__(self,f):
#         self.f = f
#         self.data = {}


class index:
    def __init__(self,pickleDir,year=None):
        self._pickleDir = pickleDir
        self._yearData = {}
        self._loadtimes = {}
        self._actionLog = []

    def formPath(self,year):
        return os.path.join(self._pickleDir,f"dump-{year}.pkl")

    def initPickle(self,path):
        f = open(path,"wb")
        d = {}
        d["meta"] = {}
        d["events"] = {}
        pickle.dump(d,f)

    def getEvents(self,d):
        year = d.year
        if year not in self._yearData.keys():
            print("Load year",year)
            self.loadYear(year)
        if d not in self._yearData[year].keys():
            return []
        else:
            return self._yearData[year][d]

    def setEvent(self,d,event):
        log = {"func":self.setEvent,"args":[d,event]}
        self._actionLog.append(log)

        event["meta"] = {}
        event["meta"]["created"] = datetime.datetime.now()
        year = d.year
        if year not in self._yearData.keys():
            print("Load year",year)
            self.loadYear(year)
        if d not in self._yearData[year].keys():
            self._yearData[year][d] = []

        self._yearData[year][d].append(event)
        self.saveYear(year)

    def saveYear(self,year):
        # TODO: use _loadtimes to make sure pickle file has not been edited since loading!
        # TODO: if conflict, use self._actionLog to play back actions
        print("Save year",year)
        path = self.formPath(year)
        f = open(path,"wb")
        pickle.dump(self._yearData[year],f)
        f.close()

    def loadYear(self,year):
        path = self.formPath(year)
        if not os.path.exists(path):
            self.initPickle(path)
        self._yearData[year] = pickle.load(open(path,"rb"))
        self._loadtimes[year] = time.time()


if __name__=="__main__":
    i = index("data")
    d = datetime.datetime(2023,1,1)

    event = {}
    event["name"] = "name test"
    event["category"] = "work"
    event["time"] = None
    event["note"] = "This is the note"
    i.setEvent(d,event)

    x = i.getEvents(d)
    print(x)


