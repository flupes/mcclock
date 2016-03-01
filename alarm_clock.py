import time
import datetime
import random
import glob
import vlc

# Hardcode some modules path to simplify
import sys
basedir='/home/pi/pkgs'
sys.path.append(basedir+'/Adafruit-Raspberry-Pi-Python-Code/Adafruit_LEDBackpack')
from Adafruit_7Segment import SevenSegment

from utilities import set_hw_volume, get_hw_volume

from events_base import EventsBase

class AlarmClock(object):

    # Time and song to wake up for each day of the week (0=Monday)
    wakeup = [
        (datetime.time(7,20), "Dragons.mp3"),
        (datetime.time(7,20), "Emeralds.mp3"),
        (datetime.time(7,20), "FallenKingdom.mp3"),
        (datetime.time(7,20), "MiningOres.mp3"),
        (datetime.time(7,20), "NewWorld.mp3"),
        (datetime.time(9,00), "TakeBackTheNight.mp3"),
        (datetime.time(9,00), "CreepersGonnaCreep.mp3")
    ]

    # List of songs
    musicdir = '/home/pi/Music/AlarmClock'
    songs = glob.glob(musicdir+'/*.mp3')

    number_of_wakeup_songs = 5
    volume_rampup_time = 45
    current_sw_volume = 0

    wakeup_volume_limits = (6, 18)
        
    def __init__(self, i2c_lock):
        self.lock = i2c_lock
        # Initialize the 7 segment display
        self.segment = SevenSegment(address=0x70)
        self.tformat = '12h'
        
        # duration a message is displayed on the 7 segments LED
        # before time display is resumed
        self.msg_duration = 0
        # time when a message start to be displayed instead of
        # the time on the 7 segments LED
        self.msg_timestamp = time.time()

        self.brightness_level = 12
        self.segment.disp.setBrightness(self.brightness_level)

        self.alarm_enabled = False
        now = datetime.datetime.now()
        self.current_day = now.day
        if now.time() > self.wakeup[now.weekday()][0] :
            self.ringed_today = True
        else :
            self.ringed_today = False

        # Configure a VLC player
        self.player = vlc.MediaPlayer()

        # MediaListPlayer
        self.mlplayer = vlc.MediaListPlayer()
        self.mlplayer.set_media_player(self.player)
        self.alarm_start_time = None
        
    def message(self, msg, delay):
        self.lock.acquire()
        for i in range(len(msg)) :
            self.segment.writeDigitRaw(i, msg[i])
            self.msg_timestamp = time.time()
            self.msg_duration = delay
        self.lock.release()

    def shutdown(self):
        self.lock.acquire()
        self.segment.writeDigitRaw(0, 0x3F)
        self.segment.writeDigitRaw(1, 0x71)
        self.segment.writeDigitRaw(3, 0x71)
        self.segment.writeDigitRaw(4, 0x40)
        self.segment.setColon(False)
        self.lock.release()
        
    def set_brightness(self, level):
        self.lock.acquire()
        if (level < 16) and (level >=0):
            print "new lcd brightness =",level
            self.brightness_level = level
            self.segment.disp.setBrightness(level)
        self.lock.release()
        
    def play_alarm(self):
        # Pick 5 random songs from the list
        pl = list(self.songs)
        random.shuffle(pl)
        pl = pl[0:self.number_of_wakeup_songs]
        print("play list for day "+str(datetime.datetime.now().weekday())+":")
        print(pl)
        mediaList = vlc.MediaList(pl)
        self.mlplayer.set_media_list(mediaList)
        self.current_sw_volume = 0
        self.player.audio_set_volume(0)
        self.alarm_start_time = time.time()
        self.mlplayer.play()
                            
        return True

    def play(self):
        if not self.mlplayer.is_playing():
            self.mlplayer.play()

    def stop(self):
        if self.mlplayer.is_playing():
            self.mlplayer.stop()
            
    def enable(self, state):
        if self.alarm_enabled != state:
            self.alarm_enabled = state
            if state == True:
                self.mlplayer.stop()
                
    def set_music_dir(self, directory):
        song_list = glob.glob(directory+'/*.mp3')
        mediaList = vlc.MediaList(song_list)
        self.mlplayer.set_media_list(mediaList)

    def process_key(self, k):
        if k == EventsBase.KEY_SELECT:
            if self.player.is_playing() :
                self.mlplayer.pause()
                print("pausing player")
            else :
                self.mlplayer.play()
                print("start to play song: "+self.player.get_media().get_mrl())

        elif k == EventsBase.KEY_LEFT:
            self.mlplayer.previous()
            print("move to previous song: "+self.player.get_media().get_mrl())

        elif k == EventsBase.KEY_RIGHT:
            self.mlplayer.next()
            print("move to next song: "+self.player.get_media().get_mrl())

    def update(self):
        t = time.time()
        now = datetime.datetime.now()    
        if t > self.msg_timestamp + self.msg_duration :
            hour = now.hour
            minute = now.minute
            second = now.second
            # Switch 24h / 12h format
            if self.tformat == '12h' and hour > 12 :
                hour = hour - 12
                dot = True
            else:
                dot = False
            self.lock.acquire()
            # Set hours
            self.segment.writeDigit(0, int(hour / 10))     # Tens
            self.segment.writeDigit(1, hour % 10, dot)     # Ones
            # Set minutes
            self.segment.writeDigit(3, int(minute / 10))   # Tens
            # Ones and alarm enable (dot)
            self.segment.writeDigit(4, minute % 10, self.alarm_enabled)
            # Toggle colon
            self.segment.setColon(second % 2)              # Toggle colon at 1Hz
            self.lock.release()
            
        # Check if alarm is necessary
        alarm = False
        if self.alarm_enabled == True :
            if not self.ringed_today :
                if now.time() > self.wakeup[now.weekday()][0] :
                    alarm = True
                    low = self.wakeup_volume_limits[0]
                    high = self.wakeup_volume_limits[1]
                    vol = get_hw_volume()
                    if vol[0] < low:
                        set_hw_volume(low)
                    if vol[0] > high:
                        set_hw_volume(high)
                    self.play_alarm()
                    self.ringed_today = True

        # Ramp up volume if necessary
        if self.alarm_start_time is not None:
            if self.current_sw_volume < 90:
                elapsed = time.time()-self.alarm_start_time
                volume = int( round( 90 * elapsed / self.volume_rampup_time ) )
                if (volume - self.current_sw_volume) > 0:
                    self.player.audio_set_volume(volume)
                    self.current_sw_volume = volume
                    
        # Update alarm state for new day
        if self.current_day != now.day :
            self.current_day = now.day
            self.ringed_today = False

        return alarm

