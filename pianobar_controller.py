import time
import threading

from events_base import EventsBase

class PianobarController(object):
    PLAYING = 1
    PAUSED = 2
    STATION = 3
    
    def __init__(self, ui_in, ui_out):
        #self.pianobar_proc = pb_proc
        self.ui_input = ui_in
        self.ui_out = ui_out
        self.mode = PianobarController.PAUSED
        print "launching pianobar controller thread"
        self.terminate = threading.Event()
        self.thread = threading.Thread(name='controller', target=self.control)
        self.thread.start()

    def control(self):
        while not self.terminate.isSet():

            while self.ui_input.queue.empty() == False:
                e = self.ui_input.queue.get_nowait()

                if e == EventsBase.VOLUME:
                    print "VOLUME -> " + str(self.ui_input.volume)
                    
                if self.mode == PianobarController.STATION:
                    if e == EventsBase.SELECT:
                        print "select station not implemented yet"
                        self.mode = PianobarController.PLAYING
                    elif e == EventsBase.UP:
                        print "prev station not implemented yet"
                    elif e == EventsBase.DOWN:
                        print "next station not implemented yet"
                else:
                    if e == EventsBase.LEFT:
                        # flush pending events to switch mode
                        while self.ui_input.queue.empty() == False:
                            self.ui_input.queue.get_nowait()
                        self.mode = PianobarController.STATION
                        print "STATION"
                    elif e == EventsBase.SELECT:
                        if self.mode == PianobarController.PLAYING:
                            self.mode = PianobarController.PAUSED
                            print "PAUSE"
                        elif self.mode == PianobarController.PAUSED:
                            self.mode = PianobarController.PLAYING
                            print "PLAY"
                    elif e == EventsBase.RIGHT:
                        print "NEXT"
                    elif e == EventsBase.UP:
                        print "LOVE"
                    elif e == EventsBase.DOWN:
                        print "BAN"

            time.sleep(0.1)
        print "SHUTDOWN"
        
    def shutdown(self):
        self.terminate.set()
        self.thread.join()
        print "pianobar controller stopped."
