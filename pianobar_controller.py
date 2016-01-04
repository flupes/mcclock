import os
import time
#import threading
import pexpect

from events_base import EventsBase

class PianobarController(object):
    PLAYING = 1
    PAUSED = 2
    STATION = 3

    PIANOBAR_CMD = os.environ['HOME']+'/devel/pianobar/pianobar'
    
    def __init__(self, ui_in, ui_out):
        #self.pianobar_proc = pb_proc
        self.ui_input = ui_in
        self.ui_out = ui_out
        self.mode = PianobarController.PAUSED
        self.pianobar = None
#        print "launching pianobar controller thread"
#        self.terminate = threading.Event()
#        self.thread = threading.Thread(name='controller', target=self.control)
#        self.thread.start()

    def launch(self):
        if self.pianobar == None:
            print "spawing pianobar..."
            self.pianobar = pexpect.spawn(self.PIANOBAR_CMD)
            self.pianobar.expect('Get stations... Ok.\r\n', timeout=30)
            print "pianobar started..."
            
        else:
            print "pianobar already spawned: hopping it is in a good state..."
        
    def control(self):
        self.launch()
        pattern_list = self.pianobar.compile_pattern_list(['SONG: ', 'STATION: ', 'TIME: ', 'Receiving new playlist...'])
        # force start playing
        print "start playing..."
        self.pianobar.send('P')
        self.mode = PianobarController.PLAYING

        print "start main loop"
        #while not self.terminate.isSet():
        while self.pianobar.isalive():

            counter = 0
            # Process output from pianobar
            while True:
                try:
                    x = self.pianobar.expect(pattern_list, timeout=0)
                    if x == 0:
                        title = ''
                        artist = ''
                        album = ''
                        x = self.pianobar.expect(' \| ')
                        if x == 0: # Title | Artist | Album
                            title = self.pianobar.before
                            x = self.pianobar.expect(' \| ')
                            if x == 0:
                                artist = self.pianobar.before
                                x = self.pianobar.expect('\r\n')
                                if x == 0:
                                    album = self.pianobar.before
                        print "got new song:",title,"by",artist,"on",album
                    elif x == 1:
                        x = self.pianobar.expect(' \| ')
                        if x == 0:
                            print "got new station:",self.pianobar.before
                    elif x == 2:
                        # Time doesn't include newline - prints over itself.
                        x = self.pianobar.expect('\r', timeout=1)
                        if x == 0:
                            timing = self.pianobar.before
                            if (counter % 50) == 0:
                                print "timing:",timing
                            counter = counter + 1
                    elif x == 3:
                        x = self.pianobar.expect(' Ok.\r\n')
                        if x == 0:
                            print "got playlist right."
                except pexpect.EOF:
                    break;
                except pexpect.TIMEOUT:
                    break;
                                                                                 
            # Process input events
            while self.ui_input.queue.empty() == False:
                e = self.ui_input.queue.get_nowait()

                if e == EventsBase.VOLUME:
                    print "VOLUME -> " + str(self.ui_input.volume)

                if e == EventsBase.SHUTDOWN:
                    print "SHUTDOWN"
                    self.pianobar.send('\n')
                    self.pianobar.send('q')
                    
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
                            self.pianobar.send('S')
                        elif self.mode == PianobarController.PAUSED:
                            self.mode = PianobarController.PLAYING
                            print "PLAY"
                            self.pianobar.send('P')
                    elif e == EventsBase.RIGHT:
                        print "NEXT"
                        self.pianobar.send('n')
                    elif e == EventsBase.UP:
                        print "LOVE"
                        self.pianobar.send('+')
                    elif e == EventsBase.DOWN:
                        print "BAN"
                        self.pianobar.send('t')
            # wait a little bit before processing the next events
            time.sleep(0.1)
            
        print "pianobar is down."
        
    # def shutdown(self):
    #     self.terminate.set()
    #     self.thread.join()
    #     print "pianobar controller stopped."
