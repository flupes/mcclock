#!/usr/bin/python

# Hardcode some module path to simplify
import sys
basedir='/home/pi/code'
sys.path.append(basedir+'/Adafruit-Raspberry-Pi-Python-Code/Adafruit_LEDBackpack')
sys.path.append(basedir+'/pyvlc')

import vlc
import RPi.GPIO as GPIO
from Adafruit_7Segment import SevenSegment

import glob
import time
import datetime

# Initialize the 7 segment display
segment = SevenSegment(address=0x70)

# Set the default brightness
segment.disp.setBrightness(6)

# Use BMC numbering
GPIO.setmode(GPIO.BCM)

# 5 tactile switches mapping
buttons = {
    17 : "SET",
    22 : "LEFT",
    23 : "RIGHT",
    24 : "UP",
    27 : "DOWN",
    18 : "ENABLE",
}

# Configure a VLC player
player = vlc.MediaPlayer()
player.audio_set_volume(60)

# List of songs
musicdir = '/home/pi/Music/Minecraft'
songs = glob.glob(musicdir+'/*.mp3')
medialist = vlc.MediaList(songs)

# MediaListPlayer
mlplayer = vlc.MediaListPlayer()
mlplayer.set_media_player(player)
mlplayer.set_media_list(medialist)

pressed = { }
set_button = None
set_time = None

# keep hold on the enable pin
for p in buttons :
    if ( buttons[p] == "ENABLE" ) :
        enable_pin = p

# Detect two buttons pressed simultaneously
def check_set(pin, ts):
    # This does NOT work! (or rather the use of this function is wrong)
    if ( set_button != None ) :
        if ( GPIO.input(pin) == False ) :
            if ( (time.time()-ts) > 0.4 ) :
                return True
    return False

# Callback when tactile switch is released
def button_callback(channel):

    # global pressed
    # elapsed = 0.
    # longpress = None
    # if (GPIO.input(channel) == False):
    #     pressed[channel] = time.time()
    #     print "button pressed"
    # else:
    #     if ( pressed.has_key(channel) ):
    #         ts = time.time()
    #         elapsed = ts-pressed[channel]        
    #         print "elapsed =", elapsed
    #     else:
    #         print "no timestamp for pressed!"
    #     if ( elapsed > 0.4 ):
    #         longpress = True
    #     else:
    #         longpress = False

#    if (longpress): p='LONG'
#    else: p='SHORT'
#    print("Button "+buttons[channel]+"("+str(channel)+") "+p+" pressed")

    global set_button, set_time

    if ( GPIO.input(enable_pin) == True ) :
        # Alarm mode
        brightness = segment.disp.getBrightness()
        if ( buttons[channel] == "UP" ) :
            if ( brightness < 15 ) :
                brightness = brightness + 1
                segment.disp.setBrightness(brightness)
            print("brightness="+str(brightness))
        elif ( buttons[channel] == "DOWN" ) :
            print "current brightness =", brightness
            if ( brightness > 0 ) :
                brightness = brightness - 1
                print "decreased brightness =", brightness
                segment.disp.setBrightness(brightness)
            print("brightness="+str(brightness))
    else :
        # Player mode
        if ( buttons[channel] == "SET" ) :
            set_button = channel
            set_time = time.time()
            if ( player.is_playing() ) :
                mlplayer.pause()
            else :
                mlplayer.play()
                print(player.get_media().get_mrl())
        elif ( buttons[channel] == "UP" ) :
            volume = player.audio_get_volume()
            if ( volume < 91 ) :
                volume = volume + 10
                player.audio_set_volume(volume)
                print("volume="+str(volume))
        elif ( buttons[channel] == "DOWN" ) :
            volume = player.audio_get_volume()
            if ( volume > 9 ) :
                volume = volume - 10
                player.audio_set_volume(volume)
            print("volume="+str(volume))
        elif ( buttons[channel] == "LEFT" ) :
            mlplayer.previous()
            print(player.get_media().get_mrl())
        elif ( buttons[channel] == "RIGHT" ) :
            mlplayer.next()
            print(player.get_media().get_mrl())

# Initialize the tactile switches inputs and callback
for pin in buttons:
    print("configure button "+buttons[pin]+" on pin "+str(pin))
    GPIO.setup(pin, GPIO.IN)
    GPIO.add_event_detect(pin, GPIO.FALLING, callback=button_callback, bouncetime=250)
    
def update_clock():
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    second = now.second
    # Set hours
    segment.writeDigit(0, int(hour / 10))     # Tens
    segment.writeDigit(1, hour % 10)          # Ones
    # Set minutes
    segment.writeDigit(3, int(minute / 10))   # Tens
    segment.writeDigit(4, minute % 10)        # Ones
    # Toggle color
    segment.setColon(second % 2)              # Toggle colon at 1Hz
    # Wait one second

while True:
    update_clock()
    time.sleep(1)
