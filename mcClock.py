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

import threading
import Queue

# Initialize the 7 segment display
segment = SevenSegment(address=0x70)

# Set the default brightness
darkMode = False
manualBrightness = 8
segment.disp.setBrightness(manualBrightness)
print("Stating with LIGHT at "+time.strftime("%Y-%m-%d %H:%M:%S"))

# Use BMC numbering
GPIO.setmode(GPIO.BCM)

# 5 tactile switches mapping
buttons = {
    17 : "SET",
    24 : "LEFT",
    27 : "RIGHT",
    23 : "UP",
    22 : "DOWN",
}

# ON/OFF switch pin
enablePin = 18

# queue for the tactile switches events
events_queue = Queue.Queue(32)
# some constants for events (waiting to learn enums)
PRESSED = 1
RELEASED_SHORT = 2
RELEASED_LONG = 3

MODE_ALARM = 1
MODE_PLAYER = 2
MODE_SHUTDOWN = 3
MODE_WIFIUP = 4
MODE_WIFIDOWN = 5
clockMode = MODE_ALARM

# input of the light sensor
lightSensorPin = 25

# Play each day of the week a predetermined song or not
classicSongMode = False

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

tformat='12h'

now = datetime.datetime.now()
if now.time() > wakeup[now.weekday()][0] :
    ringedToday = True
else :
    ringedToday = False

currentDay = now.day

# Configure a VLC player
player = vlc.MediaPlayer()
player.audio_set_volume(50)

# List of songs
musicdir = '/home/pi/Music/AlarmClockHipHop'
songs = glob.glob(musicdir+'/*.mp3')

# MediaListPlayer
mlplayer = vlc.MediaListPlayer()
mlplayer.set_media_player(player)


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
    

def process_enable_switch():
    global clockMode
    if GPIO.input(enablePin) == True :
        clockMode = MODE_ALARM
        mlplayer.stop()
        print("Alarm enabled -> stop playing song (clockMode="+str(clockMode)+")")
    else :
        clockMode = MODE_PLAYER
        mediaList = vlc.MediaList(songs)
        mlplayer.set_media_list(mediaList)
        print("Alarm disabled -> reset playing list (clockMode="+str(clockMode)+")")


# process tactile events
def process_tactile_events():
    global manualBrightness

    left_long = False
    right_long = False

    while events_queue.empty() == False :
        e = events_queue.get_nowait()
        b = buttons[e[0]]

        print("process event for switch " + b + " -> " + str(e[1]) + " (mode=" + str(clockMode)+")")

        if b == "SET" and e[1] == PRESSED :
            if clockMode == MODE_PLAYER :
                if player.is_playing() :
                    mlplayer.pause()
                    print("pausing player")
                else :
                    mlplayer.play()
                    print("start to play song: "+player.get_media().get_mrl())

        elif b == "LEFT" and e[1] == PRESSED :
            if clockMode == MODE_PLAYER :
                mlplayer.previous()
                print("move to previous song: "+player.get_media().get_mrl())

        elif b == "RIGHT" and e[1] == PRESSED :
            if clockMode == MODE_PLAYER :
                mlplayer.next()
                print("move to next song: "+player.get_media().get_mrl())

        elif b == "UP" and e[1] == PRESSED :
            if clockMode == MODE_ALARM and darkMode == False :
                if manualBrightness < 15 :
                    manualBrightness = manualBrightness + 1
                    segment.disp.setBrightness(manualBrightness)
                    print("brightness="+str(manualBrightness))
            elif clockMode == MODE_PLAYER :
                volume = player.audio_get_volume()
                if volume < 91 :
                    volume = volume + 10
                    player.audio_set_volume(volume)
                    print("volume="+str(volume))

        elif b == "DOWN" and e[1] == PRESSED :
            if clockMode == MODE_ALARM and darkMode == False :
                if manualBrightness > 0 :
                    manualBrightness = manualBrightness - 1
                    segment.disp.setBrightness(manualBrightness)
                    print("brightness="+str(manualBrightness))
            elif clockMode == MODE_PLAYER :
                volume = player.audio_get_volume()
                if volume > 9 :
                    volume = volume - 10
                    player.audio_set_volume(volume)
                    print("volume="+str(volume))

        elif b == "LEFT" and e[1] == RELEASED_LONG :
            if clockMode == MODE_ALARM :
                left_long = True

        elif b == "RIGHT" and e[1] == RELEASED_LONG :
            if clockMode == MODE_ALARM :
                right_long = True

        # Debug mode
        #if buttons[channel] == "SET" :
        #    print("Try the alarm...")
        #    ringedToday = False
        #    play_alarm(1)

    if left_long and right_long :
        return False
    else :
        return True


# Callback when the toggle switch change state : not used!
def toggle_callback(channel):
    print("enablePin = " + str(enablePin) + " -> " + str(GPIO.input(enablePin)))
    # For some reason, the imput state is wrong in this callback: it renders
    # the callback useless to toggle alarm versus player mode since 9 times
    # out of 10 the state returned is True not matter what the real state is...
    # Let's then just check periodically the state in the main loop
    # toggle_enable()


# Initialize the light sensor input
GPIO.setup(lightSensorPin, GPIO.IN)

# Initialize the tactile switches inputs and callback
GPIO.setup(enablePin, GPIO.IN)
for pin in buttons:
    GPIO.setup(pin, GPIO.IN)

process_enable_switch()

# Get in low power mode if no ethernet cable and alarm mode
if not netCablePlugged and clockMode == MODE_ALARM :
    # We allow ourself to power off the USB bus (and network)
    # to minimize power
    print("Will use low power mode by turning OFF the USB bus when not required")
    powerUsbBus(False)
    # Turn off the display too
    cmdOutput = commands.getoutput("tvservice -o")    
    print("turning off tvservice returned:  "+cmdOutput)
else:
    print("Will use regular power mode (USB bus on)")


def play_alarm(day):
    if classicSongMode :
        # Version with defined songs for each day
        wakeupSongs = []
        pl = list(songs)
        for d in wakeup:
            s = musicdir+"/"+d[1]
            wakeupSongs.append(s)
            pl.remove(s)
        random.shuffle(pl)
        pl.insert(0, wakeupSongs[day])
    else :
        # Pick 5 random songs from the list
        pl = list(songs)
        random.shuffle(pl)
        pl = pl[0:5]
    print("classic play list for day "+str(day)+":")
    print(pl)
    mediaList = vlc.MediaList(pl)
    mlplayer.set_media_list(mediaList)
    mlplayer.play()
    global ringedToday
    ringedToday = True


def shutdown_clock():
    segment.writeDigitRaw(0, 0x3F)
    segment.writeDigitRaw(1, 0x71)
    segment.writeDigitRaw(3, 0x71)
    segment.writeDigitRaw(4, 0x40)
    segment.setColon(False)

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
        if darkMode == False:
            segment.disp.setBrightness(0)
            darkMode = True
            print(time.strftime("%Y-%m-%d %H:%M:%S")+" -> DARK")
    else:
        if darkMode == True:
            segment.disp.setBrightness(manualBrightness)
            darkMode = False
            print(time.strftime("%Y-%m-%d %H:%M:%S")+" -> LIGHT")


def monitor_buttons(e):
    states = []
    back_counts = []
    toggle_counts = []
    clocks = []
    for pin in buttons :
        states.append( GPIO.input(pin) )
        back_counts.append( 0 )
        toggle_counts.append( 0 )
        clocks.append( time.time() )
    debounce = 4
    while not e.isSet():
        b = 0
        for pin in buttons :
            newstate = GPIO.input(pin)
            if newstate != states[b] :
                if toggle_counts[b] == 0 :
                    back_counts[b] = 0
                    
                if toggle_counts[b] == debounce :
                    states[b] = newstate
                    back_counts[b] = 0
                    toggle_counts[b] = 0
                    
                    if newstate == False :
                        clocks[b] = time.time()
                        try :
                            events_queue.put_nowait( (pin, PRESSED) )
                        except :
                            print "Queue full : just skip event!"
                    else :
                        delay = time.time() - clocks[b]
                        if delay < 3 :
                            events_queue.put_nowait( (pin, RELEASED_SHORT) )
                        else :
                            events_queue.put_nowait( (pin, RELEASED_LONG) )
                    
                else : 
                    toggle_counts[b] += 1
            else :
                if toggle_counts[b] > 0 :
                    if back_counts[b] < debounce : 
                        back_counts[b] += 1

            if back_counts[b] == debounce :
                toggle_counts[b] = 0
                
            b += 1
        # end for pin
        e.wait(0.01)
        #time.sleep(0.01)
    # end while True

#
# Main Program
#

# start monitoring tactiles switches in a different thread
e = threading.Event()
t = threading.Thread(name='monitor', target=monitor_buttons, args=(e,))
#t.deamon = True
t.start()

# add an event detection on the enablePin
GPIO.add_event_detect(enablePin, GPIO.BOTH, callback=toggle_callback, bouncetime=100)

up = True
# Main loop (now run at 2Hz: does not seem to consume more CPU and allow a quicker
# detection of the enable button
while up:
    update_clock()
    check_lighting()
    if GPIO.event_detected(enablePin) :
        process_enable_switch()
    up = process_tactile_events()
    time.sleep(0.5)


shutdown_clock()

print "finishing mcClock."
e.set()

print "final event sent."
t.join()
print "Done."

# If we had an exit condition, we could restore the USB bus power,
# which would reduce the risk of hot reboot...
#powerUsbBus(True)

