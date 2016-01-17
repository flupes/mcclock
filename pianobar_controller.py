import os
import time
import pexpect

from events_base import EventsBase

class PianobarController(object):
    OFF = 0
    PLAYING = 1
    PAUSED = 2
    STATION = 3

    PIANOBAR_CMD = os.environ['HOME']+'/devel/pianobar/pianobar'
    
    def __init__(self, ui_in, ui_out):
        #self.pianobar_proc = pb_proc
        self.ui_input = ui_in
        self.ui_out = ui_out
        self.mode = PianobarController.OFF
        self.pianobar = None
        self.counter = 0

    def launch(self):
        # spawn the pianobar process
        if self.pianobar == None:
            try:
                print "spawing pianobar..."
                self.pianobar = pexpect.spawn(self.PIANOBAR_CMD)
                self.pianobar.expect('Get stations... Ok.\r\n', timeout=30)
                print "pianobar started..."
                self.mode = PianobarController.PAUSED
            except:
                print "launching pianobar failed!"
        else:
            print "pianobar already spawned: hopping it is in a good state..."
        
        # force start playing
        print "start playing..."
        self.pianobar.send('P')
        self.mode = PianobarController.PLAYING

    def stop(self):
        if self.mode == PianobarController.OFF:
            print "pianobar already stopped. skip command!"
            return
        
        print "stop pianobar"
        self.pianobar.send('\n')
        self.pianobar.send('q')
        self.pianobar = None
        self.mode = PianobarController.OFF
            
    def play(self):
        self.pianobar.send('P')
        self.mode = PianobarController.PLAYING

    def pause(self):
        self.pianobar.send('S')
        self.mode = PianobarController.PAUSED

    def next(self):
        self.pianobar.send('n')

    def love(self):
        self.pianobar.send('+')

    def tired(self):
        self.pianobar.send('t')

    def update(self):
        # Process output from pianobar
        # Receive initial playlist
        if self.mode == PianobarController.OFF:
            return
        
        pattern_list = self.pianobar.compile_pattern_list(['SONG: ', 'STATION: ', 'TIME: ', 'Receiving new playlist...'])
        
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
                        self.counter = self.counter + 1
                        if (self.counter % 20) == 0:
                            print "timing:",timing
                elif x == 3:
                    x = self.pianobar.expect(' Ok.\r\n')
                    if x == 0:
                        print "got playlist right."
            except pexpect.EOF:
                break;
            except pexpect.TIMEOUT:
                break;
