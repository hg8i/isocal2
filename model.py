from setup import *
import view
import controller
# import noteloader
# import editWatcher
# import dialog

class model:

    def __init__(self,screen):
        self._screen = screen

        # Threading
        self._manager = multiprocessing.Manager()
        self._event   = self._manager.Event()
        self._view_i = self._manager.Queue()
        self._view_o = self._manager.Queue()
        self._controller_i = self._manager.Queue()
        self._controller_o = self._manager.Queue()
        self._char_queue = self._manager.Queue() # input from controller

        self._hotkeyMap   = settings["hotkeyMap"]
        self._commandMap = {}
        self._commandMap["quit"]   = lambda cmds: self._quit()

        # MVC
        self._controller = controller.controller(self._screen,inputq=self._controller_i,outputq=self._controller_o,charq=self._char_queue,event=self._event)
        self._view = view.view(self._screen,inputq=self._view_i,outputq=self._view_o)

    def startController(self):
        log("MODEL: Starting controller")
        self.controllerThread = multiprocessing.Process(target=self._controller.run)
        self.controllerThread.start()

    def stopController(self):
        log("MODEL: Stopping controller")
        self.controllerThread.terminate()

    def startView(self):
        log("MODEL: Starting view")
        self.viewThread = multiprocessing.Process(target=self._view.run)
        self.viewThread.start()

    def stopView(self):
        log("MODEL: Stopping view")
        self.viewThread.terminate()

    def _quit(self):

        self.stopController()
        self.stopView()

        quit()

    def processResize(self):
        message = {}
        message["type"] = "resize"
        self._view_i.put(message)


    def run(self):

        # launch threads
        self.startController()
        self.startView()

        while True:
            self._event.wait()
            self._event.clear()

            while not self._char_queue.empty():
                char = self._char_queue.get()
                log("Char:",char,chr(char))

                if chr(char) in self._hotkeyMap.keys():
                    command = self._hotkeyMap[chr(char)]
                    self._commandMap[command](None)

                if char==410: #resize
                    self.processResize()

                # self._view_i.put(1)



