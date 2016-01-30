import os
import re
import time
import pexpect

from events_base import EventsBase

class PianobarController(object):
    OFF = 0
    PLAYING = 1
    PAUSED = 2
    STATION = 3

    PIANOBAR_CMD = os.environ['HOME']+'/devel/pianobar/pianobar'
    
    def __init__(self):
        self.mode = PianobarController.OFF
        self.pianobar = None

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
        print lines
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

    def process_key(self, key):
        if self.mode == PianobarController.STATION:
            if key == KeyboardEvents.KEY_SELECT:
                self.select_station(station_list[station_index][0])
                self.mode = PianobarController.PLAYING
            elif key == KeyboardEvents.KEY_UP:
                if station_index < len(station_list)-1:
                    station_index=station_index+1
                print "current selection =",station_list[station_index][0],
                print "->",station_list[station_index][1]
            elif key == KeyboardEvents.KEY_DOWN:
                if station_index > 0:
                    station_index=station_index-1
                print "current selection =",station_list[station_index][0],
                print "->",station_list[station_index][1]
        elif self.mode != PianobarController.OFF:
            if key == KeyboardEvents.KEY_LEFT:
                self.mode = PianobarController.STATION
                print "STATION"
                station_list = self.get_stations()
                station_index = 0
                for s in station_list:
                    if current_station == s[1]:
                        break;
                    station_index = station_index+1
                if station_index == len(station_list):
                    print "current station not found in list!"
                    station_index = 1
                print station_list
                print "current station index is:", station_index
            elif key == KeyboardEvents.KEY_SELECT:
                if self.mode == PianobarController.PLAYING:
                    print "PAUSE"
                    self.pause()
                elif self.mode == PianobarController.PAUSED:
                    print "PLAY"
                    self.play()
            elif key == KeyboardEvents.KEY_RIGHT:
                print "NEXT"
                self.next()
            elif key == KeyboardEvents.KEY_UP:
                print "LOVE"
                self.love()
            elif key == KeyboardEvents.KEY_DOWN:
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
                elif x == 1:
                    x = self.pianobar.expect(' \| ')
                    if x == 0:
                        station = self.pianobar.before
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
