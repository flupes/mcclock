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
import random

# Initialize the 7 segment display
segment = SevenSegment(address=0x70)

# Set the default brightness
segment.disp.setBrightness(4)

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

# Time and song to wake up for each day of the week (0=Monday)
wakeup = [
    (datetime.time(7,20), "Dragons.mp3"),
    (datetime.time(6,50), "Emeralds.mp3"),
    (datetime.time(7,20), "FallenKingdom.mp3"),
    (datetime.time(7,20), "MiningOres.mp3"),
    (datetime.time(7,25), "NewWorld.mp3"),
    (datetime.time(9,00), "Emeralds.mp3"),
    (datetime.time(23,38), "FallenKingdom.mp3")
    ]

ringed = False
currentDay = datetime.date.today().day

# Configure a VLC player
player = vlc.MediaPlayer()
player.audio_set_volume(30)

# List of songs
musicdir = '/home/pi/Music/Minecraft'
songs = glob.glob(musicdir+'/*.mp3')

# MediaListPlayer
mlplayer = vlc.MediaListPlayer()
mlplayer.set_media_player(player)

# keep hold on the enable pin
for p in buttons :
    if buttons[p] == "ENABLE" :
        enable_pin = p

# Callback when tactile switch is pressed
def button_callback(channel):
    if GPIO.input(enable_pin) == True and mlplayer.is_playing() == False :
        # Alarm mode
        brightness = segment.disp.getBrightness()
        if buttons[channel] == "UP" :
            if brightness < 15 :
                brightness = brightness + 1
                segment.disp.setBrightness(brightness)
            print("brightness="+str(brightness))
        elif buttons[channel] == "DOWN" :
            if brightness > 0 :
                brightness = brightness - 1
                segment.disp.setBrightness(brightness)
            print("brightness="+str(brightness))
    else :
        # Player mode
        if buttons[channel] == "SET" :
            set_button = channel
            set_time = time.time()
            if player.is_playing() :
                mlplayer.pause()
                print("pausing player")
            else :
                mlplayer.play()
                print("start to play song: "+player.get_media().get_mrl())
        elif buttons[channel] == "UP" :
            volume = player.audio_get_volume()
            if volume < 91 :
                volume = volume + 10
                player.audio_set_volume(volume)
                print("volume="+str(volume))
        elif buttons[channel] == "DOWN" :
            volume = player.audio_get_volume()
            if volume > 9 :
                volume = volume - 10
                player.audio_set_volume(volume)
            print("volume="+str(volume))
        elif buttons[channel] == "LEFT" :
            mlplayer.previous()
            print("move to previous song: "+player.get_media().get_mrl())
        elif buttons[channel] == "RIGHT" :
            mlplayer.next()
            print("move to next song: "+player.get_media().get_mrl())

# Callback when the toggle switch change state
def toggle_callback(channel):
    # It seems that 9 out of 10 times the pin still shows HIGH
    # when the toggle is put to ground...
    # We have extra resistors between the input and the switch to
    # be super careful. The side effect is that the voltage drops 
    # only at 0.3 V. Is it low enough?
    if GPIO.input(enable_pin) == True :
        mlplayer.stop()
        print("Alarm enabled -> stop playing song")
    else :
        mediaList = vlc.MediaList(songs)
        mlplayer.set_media_list(mediaList)
        print("Alarm disabled -> reset playing list to:")
        print(songs)

# Initialize the tactile switches inputs and callback
for pin in buttons:
    print("configure button "+buttons[pin]+" on pin "+str(pin))
    GPIO.setup(pin, GPIO.IN)
    if pin == enable_pin :
        GPIO.add_event_detect(pin, GPIO.BOTH, callback=toggle_callback, bouncetime=600)
    else :
        GPIO.add_event_detect(pin, GPIO.FALLING, callback=button_callback, bouncetime=300)

if GPIO.input(enable_pin) == False :
    mediaList = vlc.MediaList(songs)
    mlplayer.set_media_list(mediaList)

def play_alarm(day):
    s = musicdir+"/"+wakeup[day][1]
    pl = list(songs)
    pl.remove(s)
    random.shuffle(pl)
    pl.insert(0, s)
    print("play list for day "+str(day)+":")
    print(pl)
    mediaList = vlc.MediaList(pl)
    mlplayer.set_media_list(mediaList)
    mlplayer.play()
    global ringed
    ringed = True

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
    # Check if alarm is necessary
    global ringed
    if GPIO.input(enable_pin) == True :
        if not ringed :
            day = now.weekday()
            if now.time() > wakeup[day][0] :
                play_alarm(day)
    # Update alarm state
    global currentDay
    if currentDay != now.day :
        currentDay = now.day
        ringed = False

while True:
    update_clock()
    time.sleep(1)

