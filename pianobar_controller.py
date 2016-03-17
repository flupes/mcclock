import os
import re
import time
import pexpect

from events_base import EventsBase
from lcd_menu import LcdMenu

class PianobarController(object):
    OFF = 0
    PLAYING = 1
    PAUSED = 2
    STATION = 3

    STATE = 1
    SONG = 2
    STATION = 4
    TIMING = 8
    
    PIANOBAR_CMD = 'pianobar'
    
    station_list = []
    station_index = 1

    def __init__(self, display):
        print "initializing PianobarController in OFF state"
        self.display = display
        self.mode = PianobarController.OFF
        self.pianobar = None

    def launch(self):
        # spawn the pianobar process
        if self.pianobar == None:
            try:
                print "spawing pianobar..."
                self.display.static_msg(2, 'Starting...', 1 , True)
                self.pianobar = pexpect.spawn(self.PIANOBAR_CMD)
                try:
                    self.pianobar.expect('Get stations... Ok.\r\n', timeout=30)
                except:
                    print "pianobar did not come up properly!"
                    self.mode.PianobarController.STOP
                    self.pianobar.terminate(force=True)
                    self.display.static_msg(2, 'Error! Try Again...', 1, True)
                print "pianobar started..."
                self.mode = PianobarController.PLAYING
            except:
                self.mode = PianobarController.OFF
                print "launching pianobar failed!"
        else:
            print "pianobar already spawned: hopping it is in a good state..."

        self.current_station = None

        if self.mode == PianobarController.PLAYING:
            # send a default station: if it was not cached, this should
            # help pianobar to start. Otherwise it should do not harm to
            # pianobar (keys ignored?).
            self.pianobar.send('0\n')
            print "start playing..."
            # force start playing, just to be on the safe side
            self.pianobar.send('P')
            self.mode = PianobarController.PLAYING
        else:
            # kill the process for clean start next time
            if self.pianobar.isalive():
                print "kill stuck pianobar process"
                self.pianobar.kill(9)
            self.pianobar = None
            self.display.scroll_msg(2, 'Pianobar failed to start! Try again later...', 0.3)

    def stop(self):
        if self.mode == PianobarController.OFF:
            print "pianobar already stopped. skip command!"
            return
        
        print "stop pianobar"
        self.pianobar.send('\n')
        self.pianobar.send('q')
        time.sleep(0.2)
        self.pianobar = None
        self.mode = PianobarController.OFF
            
    def play(self):
        self.pianobar.send('P')
        self.mode = PianobarController.PLAYING
        self.update_display(self.STATE)

    def pause(self):
        self.pianobar.send('S')
        self.mode = PianobarController.PAUSED
        self.update_display(self.STATE)

    def next(self):
        self.pianobar.send('n')

    def love(self):
        self.display.timed_msg(2, 'LOVE !', 5)
        self.pianobar.send('+')

    def tired(self):
        self.display.timed_msg(2, 'NOT TIRED ;-)', 5)
        #self.pianobar.send('t')

    def select_station(self, station_id):
        self.pianobar.send(station_id)
        self.pianobar.send('\n')
        
    def get_stations(self):
        self.pianobar.send('s')
        try:
            self.pianobar.expect('Select station: ', timeout=12)
        except:
            print "error parsing string of new stations"
            return None
        
        lines = self.pianobar.before.splitlines()
        # print lines
        stations = []
        p = re.compile('^(\S*\t ?)(\d+)\) [ q][ Q][ S] (.+)$')
        for st in lines:
            m = p.match(st)
            if m is not None:
                try:
                    num = m.group(2)
                except:
                    "Error in parsing ID of station list!"
                name = m.group(3)
                stations.append((num, name))
        return stations

    def update_display(self, what):
        if (what & self.STATION) or (what & self.STATE):
            print "update station or state"
            if self.mode == PianobarController.PLAYING:
                msg = '\x00 ' + self.current_station
            else:
                msg = '\x01 ' + self.current_station
            self.display.static_msg(1, msg, 1, True)

        if (what & self.SONG) or (what & self.TIMING):
            print "update song or timing"
            msg = self.current_song[1] + ' | ' + self.current_song[0]
            self.display.scroll_msg(2, msg, 0.3)
        
    def station_menu(self):
        self.station_list = self.get_stations()
        self.station_index = 0
        for s in self.station_list:
            if self.current_station == s[1]:
                break;
            self.station_index = self.station_index+1
        if self.station_index == len(self.station_list):
            print "current station not found in list!"
            self.station_index = 1
        # print self.station_list
        print "current station index is:", self.station_index
        self.station_id = self.station_list[self.station_index][0]
        self.menu = LcdMenu(self.display, self.station_list, self.station_index)
        
    def process_key(self, key):
        if self.mode == PianobarController.STATION:
            selection = self.menu.process_key(key)
            if selection is not None:
                if selection == -1:
                    # menu exit without selection, however we cannot cancel the
                    # pianobar station selection, so select the station currently
                    # played. the side effect is that a new song will start playing
                    self.select_station(self.station_id)
                else:
                    self.select_station(selection)
                self.display.clear()
                self.mode = PianobarController.PLAYING
        elif self.mode != PianobarController.OFF:
            if key == EventsBase.KEY_LEFT:
                self.mode = PianobarController.STATION
                print "STATION"
                self.station_menu()
            elif key == EventsBase.KEY_SELECT:
                if self.mode == PianobarController.PLAYING:
                    print "PAUSE"
                    self.pause()
                elif self.mode == PianobarController.PAUSED:
                    print "PLAY"
                    self.play()
            elif key == EventsBase.KEY_RIGHT:
                print "NEXT"
                self.next()
            elif key == EventsBase.KEY_UP:
                print "LOVE"
                self.love()
            elif key == EventsBase.KEY_DOWN:
                print "TIRED"
                self.tired()

    
    def update(self):
        # Process output from pianobar
        # Receive initial playlist
        if self.mode == PianobarController.OFF:
            return None, None, None
        
        pattern_list = self.pianobar.compile_pattern_list(['SONG: ', 'STATION: ', 'TIME: ', 'Receiving new playlist...'])
        
        song = None
        timing = None
        station = None

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
                    song=(title, artist, album)
                    self.current_song = song
                    self.update_display(self.SONG)
                elif x == 1:
                    x = self.pianobar.expect(' \| ')
                    if x == 0:
                        station = self.pianobar.before
                        self.current_station = station
                        self.update_display(self.STATION)
                elif x == 2:
                    # Time doesn't include newline - prints over itself.
                    x = self.pianobar.expect('\r', timeout=1)
                    if x == 0:
                        timing = self.pianobar.before
                elif x == 3:
                    x = self.pianobar.expect(' Ok.\r\n')
                    if x == 0:
                        print "got playlist OK."
            except pexpect.EOF:
                break;
            except pexpect.TIMEOUT:
                break;

        return song, timing, station
