import time
import math
import glob
import commands

import vlc

from pib_events import PibEvents
from utilities import set_hw_volume

up = True

pe = PibEvents()

# Configure a VLC player
player = vlc.MediaPlayer()
player.audio_set_volume(96)

# List of songs
musicdir = '/home/pi/Music/Various'
songs = glob.glob(musicdir+'/*.mp3')

# MediaListPlayer
mlplayer = vlc.MediaListPlayer()
mlplayer.set_media_player(player)

mediaList = vlc.MediaList(songs)
mlplayer.set_media_list(mediaList)

mlplayer.play()
playing = True

while up:
    while pe.queue.empty() == False:
        e = pe.queue.get_nowait()
        
        if e[0] == PibEvents.VOLUME:
            set_hw_volume(e[1])
            
        elif e[0] == PibEvents.JOYSTICK:
            print "joystick: axis",e[1],"->",e[2]

        elif e[0] == PibEvents.KEY:
            print "keypress:", e[1]
            if playing == True:
                mlplayer.pause()
                playing = False
            else:
                mlplayer.play()
                playing = True

        elif e[0] == PibEvents.MODE:
            print "new mode =", e[1]
            if e[1] == PibEvents.MODE_SPECIAL:
                up = False
            
    time.sleep(0.2)

pe.stop()

print "clean exit"
