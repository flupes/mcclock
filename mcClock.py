#!/usr/bin/python -u 

# Hardcode some module path to simplify
import sys
basedir='/home/pi/code'
sys.path.append(basedir+'/Adafruit-Raspberry-Pi-Python-Code/Adafruit_LEDBackpack')
sys.path.append(basedir+'/pyvlc')

import vlc

import RPi.GPIO as GPIO
from Adafruit_7Segment import SevenSegment

# Test with the more recent RPIO instead of GPIO...
# Unfortunately 1) it clashes with GPIO used by Adafruit, 
# and 2) the hope of having better callbacks (return state as well 
# as channel) did not concretize. The returned state is corrupted
# most of the time (what I am doing wrong?)!
# import RPIO

import glob
import time
import datetime
import commands
import random

# Initialize the 7 segment display
segment = SevenSegment(address=0x70)

# Set the default brightness
darkMode = False
manualBrightness = 8
segment.disp.setBrightness(manualBrightness)

# Use BMC numbering
GPIO.setmode(GPIO.BCM)

# 5 tactile switches mapping
buttons = {
    17 : "SET",
    24 : "LEFT",
    27 : "RIGHT",
    23 : "UP",
    22 : "DOWN",
    18 : "ENABLE",
}

lightSensorPin = 25

# Time and song to wake up for each day of the week (0=Monday)
wakeup = [
    (datetime.time(7,40), "Dragons.mp3"),
    (datetime.time(7,40), "Emeralds.mp3"),
    (datetime.time(7,40), "FallenKingdom.mp3"),
    (datetime.time(7,40), "MiningOres.mp3"),
    (datetime.time(7,40), "NewWorld.mp3"),
    (datetime.time(9,00), "TakeBackTheNight.mp3"),
    (datetime.time(9,00), "CreepersGonnaCreep.mp3")
    ]

tformat='12h'

now = datetime.datetime.now()
if now.time() > wakeup[now.weekday()][0] :
    ringedToday = True
else :
    ringedToday = False

currentDay = now.day
newEnableState = False

# Configure a VLC player
player = vlc.MediaPlayer()
player.audio_set_volume(50)

# List of songs
musicdir = '/home/pi/Music/Minecraft'
songs = glob.glob(musicdir+'/*.mp3')

# MediaListPlayer
mlplayer = vlc.MediaListPlayer()
mlplayer.set_media_player(player)

# keep hold on the enable pin
enablePin = None
for p in buttons :
    if buttons[p] == "ENABLE" :
        enablePin = p

# Identify if a network cable is plugged or not
netCablePlugged = True
checkCableCmd = 'ip link show | grep eth0'
cmdOutput = commands.getoutput(checkCableCmd)
try:
    foundAt = cmdOutput.index('LOWER_UP')
except ValueError:
    print "cable unplugged"
    netCablePlugged = False
else:
    print "cable plugged"

def powerUsbBus(state):
    if state :
        flag = '0x1'
        print("Turning the USB bus ON")
    else :
        flag = '0x0'
        print("Turning the USB bus OFF")
    powerUsbBusCmd = 'echo ' + flag + ' > /sys/devices/platform/bcm2708_usb/buspower'
    cmdOutput = commands.getoutput(powerUsbBusCmd)    
    print("Result from: "+powerUsbBusCmd+" -> "+cmdOutput)
    
# Callback when tactile switch is pressed
def button_callback(channel):
    global darkMode
    global manualBrightness
    if GPIO.input(enablePin) == True and mlplayer.is_playing() == False :
        # Alarm mode
        # This is a function added to the library, let's not use it
        #brightness = segment.disp.getBrightness()
        if darkMode == False :
            # Only control brightness when not in the dark
            if buttons[channel] == "UP" :
                if manualBrightness < 15 :
                    manualBrightness = manualBrightness + 1
                    segment.disp.setBrightness(manualBrightness)
                    print("brightness="+str(manualBrightness))
            elif buttons[channel] == "DOWN" :
                if manualBrightness > 0 :
                    manualBrightness = manualBrightness - 1
                    segment.disp.setBrightness(manualBrightness)
                    print("brightness="+str(manualBrightness))
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

def toggle_enabled():
    if GPIO.input(enablePin) == True :
        mlplayer.stop()
        print("Alarm enabled -> stop playing song")
    else :
        mediaList = vlc.MediaList(songs)
        mlplayer.set_media_list(mediaList)
        print("Alarm disabled -> reset playing list to:")
        print(songs)

# Callback when the toggle switch change state
def toggle_callback(channel):
    print("enablePin = " + str(enablePin) + " -> " + str(GPIO.input(enablePin)))
    # For some reason, the imput state is wrong in this callback: it renders
    # the callback useless to toggle alarm versus player mode since 9 times
    # out of 10 the state returned is True not matter what the real state is...
    # Let's then just check periodically the state in the main loop
    # toggle_enable()
    global newEnableState
    newEnableState = True

# Initialize the tactile switches inputs and callback
for pin in buttons:
    print("configure button "+buttons[pin]+" on pin "+str(pin))
    GPIO.setup(pin, GPIO.IN)
    if pin == enablePin :
        # RPIO.add_interrupt_callback(pin, edge='both', callback=toggle_callback, \
            # debounce_timeout_ms=400)
        GPIO.add_event_detect(pin, GPIO.BOTH, callback=toggle_callback, bouncetime=400)
    else :
        # RPIO.add_interrupt_callback(pin, edge='falling', callback=button_callback, \
            # debounce_timeout_ms=200)
        GPIO.add_event_detect(pin, GPIO.FALLING, callback=button_callback, bouncetime=200)

if GPIO.input(enablePin) == False :
    mediaList = vlc.MediaList(songs)
    mlplayer.set_media_list(mediaList)

if not netCablePlugged and GPIO.input(enablePin) :
    # We allow ourself to power off the USB bus (and network)
    # to minimize power
    print("Will use low power mode by turning OFF the USB bus when not required")
    powerUsbBus(False)
else:
    print("Will use regular power mode (USB bus on)")

# Initialize the light sensor input
GPIO.setup(lightSensorPin, GPIO.IN)

def play_alarm(day):
    wakeupSongs = []
    pl = list(songs)
    for d in wakeup:
        s = musicdir+"/"+d[1]
        wakeupSongs.append(s)
        pl.remove(s)
    random.shuffle(pl)
    pl.insert(0, wakeupSongs[day])
    print("play list for day "+str(day)+":")
    print(pl)
    mediaList = vlc.MediaList(pl)
    mlplayer.set_media_list(mediaList)
    mlplayer.play()
    global ringedToday
    ringedToday = True

def update_clock():
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    second = now.second
    # Switch 24h / 12h format
    if tformat == '12h' and hour > 12 :
        hour = hour - 12
        dot = True
    else:
        dot = False
    # Set hours
    segment.writeDigit(0, int(hour / 10))     # Tens
    segment.writeDigit(1, hour % 10, dot)     # Ones
    # Set minutes
    segment.writeDigit(3, int(minute / 10))   # Tens
    # Ones and alarm enable (dot)
    segment.writeDigit(4, minute % 10, GPIO.input(enablePin))
    # Toggle color
    segment.setColon(second % 2)              # Toggle colon at 1Hz
    # Check if alarm is necessary
    global ringedToday
    if GPIO.input(enablePin) == True :
        if not ringedToday :
            day = now.weekday()
            if now.time() > wakeup[day][0] :
                play_alarm(day)
    # Update alarm state
    global currentDay
    if currentDay != now.day :
        currentDay = now.day
        ringedToday = False

def check_lighting():
    global darkMode
    if GPIO.input(lightSensorPin) == True:
        print("DARK")
        if darkMode == False:
            segment.disp.setBrightness(0)
            darkMode = True
    else:
        print("LIGHT")
        if darkMode == True:
            segment.disp.setBrightness(manualBrightness)
            darkMode = False

# Main loop (now run at 2Hz: does not seem to consume more CPU and allow a quicker
# detection of the enable button
while True:
    update_clock()
    check_lighting()
    if newEnableState:
        newEnableState = False
        toggle_enabled()
    time.sleep(0.5)

# If we had an exit condition, we could restore the USB bus power,
# which would reduce the risk of hot reboot...
powerUsbBus(True)

