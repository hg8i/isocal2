from setup import *

class controller:
    def __init__(self,screen,charq=None,outputq=None,inputq=None,event=None):
        self._output = outputq
        self._charq = charq
        self._input = inputq
        self._screen = screen
        self._pause = False
        self._event = event


    def run(self):
        log("CONTROLLER: run")
        while True:

            char = self._screen.getch()
            self._charq.put(char)
            self._event.set()

