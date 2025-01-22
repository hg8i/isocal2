import urllib
from urllib import request
from collections import OrderedDict
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from setup import *
from index import *


class icsDownload:
    def __init__(self,inputq=None,outputq=None,event=False):
        self.downloadIcsCalendars = settings["downloadIcsCalendars"]
        self._event  = event
        self._input  = inputq
        self._output = outputq

    def parseEvent(self,primitive):
        """ Parse primitive event list-by-line into dictionary
        """
        event={}
        event = OrderedDict()
        for dat in primitive:
            # print dat
            if ":" in dat:
                # Add entry to dictionary
                event[dat.split(":")[0]] = ":".join(dat.split(":")[1:])
            elif len(event.keys())>0:
                # Try adding to previous entry
                event[list(event.keys())[-1]]
        return event

    def run(self):
        ret = {}
        for icsInfo in self.downloadIcsCalendars:
            # print("ICS info",icsInfo)
            icsEvents=self.getEventsWithUrl(icsInfo)
            ret[icsInfo["name"]] = icsEvents
            if self._output and self._event:
                data = {}
                data["type"] = "icsEvents"
                data["name"] = icsInfo["name"]
                data["events"] = icsEvents
                self._event.set()
                self._output.put(data)
        if not self._output:
            return ret


    def icsConvertData(self,icsDate):
        """ Convert ICS date and time, return """
        timezone=""

        if len(icsDate)==16 and "T" in icsDate and icsDate[-1].isalpha():
            # Expect string with time and timezone: 20250225T173000Z
            timezone = icsDate[-1]
            dt = datetime.strptime(icsDate[:-1],"%Y%m%dT%H%M%S")
        elif len(icsDate)==14 and "T" in icsDate and icsDate[-1].isalpha():
            # Expect string with time and timezone, no seconds: 20250225T1730Z
            dt = datetime.strptime(icsDate[:-1],"%Y%m%dT%H%M")
            timezone = ""
        else:
            raise Exception("Not yet supported ICS time format: {icsDate}")

        if timezone=="Z":
            dt_utc = dt.replace(tzinfo=ZoneInfo("UTC"))
        else:
            raise Exception("Not yet supported ICS timezone: {icsDate}")

        dt_local = dt.astimezone(ZoneInfo(settings["timezone"]))
        localTime = dt_local.strftime("%H%M")

        # hashed datetimes have 0 time and 0 tzinfo
        dt_date = dt_local.replace(tzinfo=None,hour=0,minute=0,second=0)

        return dt_date,localTime

    def downloadIcs(self,url):
        """ Download ICS file via URL
            Return as list of "event dictionaries" 
        """
        response = request.urlopen(url).read().splitlines()
        response = [s.decode("utf-8") for s in response]
        # checks
        if response[0]!="BEGIN:VCALENDAR": raise BaseException("Bad ICS response")
        if response[-1]!="END:VCALENDAR": raise BaseException("Bad ICS response")
        events = []
        event=[]
        for line in response:
            if "BEGIN:VEVENT" in line:
                event=[]
            elif "END:VEVENT" in line:
                events.append(self.parseEvent(event))
            else: event.append(line)
        return events

    def getEventsWithUrl(self,icsInfo):
        """ Download ICS file, convert for isocal, return events 
        """
        args = icsInfo["args"]
        url = icsInfo["url"]
        category = icsInfo["category"]
        # add arguements if given
        if args and url[-1]!="?":url+="?"
        url+="&".join(args)
        icsDictionary = self.downloadIcs(url)
        events = []
        for iEvent, icEvent in enumerate(icsDictionary):
            if "DTSTART" in icEvent.keys(): key = "DTSTART"
            elif "DTEND" in icEvent.keys(): key = "DTSTAMP"
            elif "DTEND" in icEvent.keys(): key = "DTEND"
            else:
                raise Exception("No time key found")
            dt,localTime = self.icsConvertData(icEvent[key])
            name = icEvent["SUMMARY"]
            if "require" in icsInfo.keys():
                if not icsInfo["require"](name): continue

            event = eventdata()
            event["name"] = name
            event["date"] = dt
            event["uniqueid"]  = icEvent["UID"]
            event["ics"]      = True
            event["created"]  = time.time()
            event["modified"] = time.time()
            event["category"] = category
            event["time"] = localTime
            event["notes"] = icEvent["URL"]
            events.append(event)

        return events



if __name__=="__main__":
    ics = icsDownload()
    icsEvents = ics.run()
    print(type(icsEvents))
    for name,events in icsEvents.items():
        for event in events:
            print(event)
            print(event["name"], event["time"], event["notes"])


