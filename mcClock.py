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
import subprocess
import random

import threading
import Queue

# Initialize the 7 segment display
segment = SevenSegment(address=0x70)

# Set the default brightness
darkMode = False
manualBrightness = 8
segment.disp.setBrightness(manualBrightness)
print("Starting with LIGHT at "+time.strftime("%Y-%m-%d %H:%M:%S"))

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
modifierPin = 17
maxRealPin = max(buttons.keys())

# ON/OFF switch pin
enablePin = 18

# queue for the tactile switches events
events_queue = Queue.Queue(32)

# some constants for events (waiting to learn enums)
STATE_UP = 1
STATE_DOWN = 2
STATE_HOLD = 3
STATE_PENDING_SHORT_RELEASE = 4
STATE_PENDING_LONG_RELEASE = 5

EVENT_PRESSED = 3
EVENT_RELEASED_SHORT = 2
EVENT_RELEASED_LONG = 1

MODE_ALARM = 1
MODE_PLAYER = 2
MODE_SHUTDOWN = 3
MODE_WIFIUP = 4
MODE_WIFIDOWN = 5
MODE_PANDORA = 6
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

msg_timestamp = time.time()
msg_duration = 0

currentDay = now.day

# Configure a VLC player
player = vlc.MediaPlayer()
player.audio_set_volume(50)

# List of songs
musicdir = '/home/pi/Music/AlarmClock'
songs = glob.glob(musicdir+'/*.mp3')

# MediaListPlayer
mlplayer = vlc.MediaListPlayer()
mlplayer.set_media_player(player)


pianobarPlaying = False
pianobarProcess = 'nope'
pianobarStation = 3

def powerUsbBus(state):
    if state :
        msg = [0x01, 0xC1, 0x00, 0x3E, 0x73]
        print("Turning the USB bus ON")
        display_msg(msg, 6)
        powerUsbBusCmd = basedir + "/mcclock/usbBusUp.bash"
        cmdOutput = commands.getoutput(powerUsbBusCmd)
    else :
        msg = [0x01, 0xC1, 0x00, 0x3F, 0x3F]
        display_msg(msg, 6)
        print("Turning the USB bus OFF")
        powerUsbBusCmd = basedir + "/mcclock/usbBusDown.bash"
        cmdOutput = commands.getoutput(powerUsbBusCmd)

    print("Result from: "+powerUsbBusCmd+" -> "+cmdOutput)
    

def send_pianobar_cmd(s):
    #global clockMode
    global pianobarProcess

    #print "piano in send cmd:"
    #print pianobarProcess
    #print "clockMode = " + str(clockMode)
    ctrl = pianobarProcess.stdin
    try:
        ctrl.write(s)
    except:
        print "could not write to pianobar"
    #cmd = 'echo \'' + s + '\' >> /home/pi/.config/pianobar/scritps/ctl'
    #cmdOutput = commands.getoutput(cmd)


def monitor_pianobar(out):
    global pianobarPlaying

    up='Get stations... Ok.'
    for line in iter(out.readline, '') :
        print(line),
        if not pianobarPlaying :
            if up in line :
                pianobarPlaying = True
    print "monitor_pianobar : event received -> thread done"

def start_pianobar():
    global pianobarPlaying
    global pianobarProcess

    #powerUsbBus(True)
    # Launch pianobar as pi user (to use same config data, etc.) in background:
    print('spawning pianobar...')
    pianobarProcess = subprocess.Popen('sudo -u pi pianobar', shell=True,
                                       stdout=subprocess.PIPE,
                                       stdin=subprocess.PIPE)

    t = threading.Thread(name='monitor_piano', target=monitor_pianobar,
                         args=(pianobarProcess.stdout,))
    t.daemon = True
    t.start()

    for i in range(1, 30):
        if pianobarPlaying :
            break;
        time.sleep(1)
    if pianobarPlaying:
        send_pianobar_cmd('^')
        print "pianobar has been launched"
    else:
        print "pianobar did not start correctly"
        # make sure it dies completely
        subprocess.call('killall pianobar')
        clockMode = MODE_PLAYER
        display_msg([0x73, 0x38, 0x00, 0x77, 0x66], 9)
        print "back to PLAYER mode"


def stop_pianobar():
    global pianobarProcess
    global pianobarPlaying

    send_pianobar_cmd('q')
    #pianobarProcess.stdout.close()
    pianobarPlaying = False
    print "pianobar has been terminated"


def process_enable_switch():
    global clockMode
    if GPIO.input(enablePin) == True :
        if clockMode == MODE_PLAYER :
            mlplayer.stop()
        else:
            stop_pianobar()
        clockMode = MODE_ALARM
        print("Alarm enabled -> stop playing song (clockMode="+str(clockMode)+")")
    else :
        clockMode = MODE_PLAYER
        mediaList = vlc.MediaList(songs)
        mlplayer.set_media_list(mediaList)
        print("Alarm disabled -> reset playing list (clockMode="+str(clockMode)+")")


# process tactile events
def process_tactile_events():
    global manualBrightness
    global clockMode
    global pianobarPlaying
    global pianobarStation

    left_long = False
    right_long = False

    while events_queue.empty() == False :
        e = events_queue.get_nowait()
        pin = e[1]
        if pin > maxRealPin :
            b=buttons[modifierPin]+"+"+buttons[pin-modifierPin]
        else :
            b = buttons[pin]

        #print("process event for switch " + b + " -> " + str(e[0]) + " (mode=" + str(clockMode)+")")

        if clockMode == MODE_PLAYER :

            if b == "SET" and e[0] == EVENT_RELEASED_LONG :
                while events_queue.empty() == False :
                    e = events_queue.get_nowait()
                mlplayer.stop()
                clockMode = MODE_PANDORA
                display_msg([0x73, 0x77, 0x00, 0x37, 0x3F], 9)
                # start in a separate thread because powering up usb
                # + network could take time
                s = threading.Thread(name='startpiano', target=start_pianobar)
                s.start()

            elif b == "SET" and e[0] == EVENT_RELEASED_SHORT :
                if player.is_playing() :
                    mlplayer.pause()
                    print("pausing player")
                else :
                    mlplayer.play()
                    print("start to play song: "+player.get_media().get_mrl())

            elif b == "LEFT" and e[0] == EVENT_RELEASED_SHORT :
                mlplayer.previous()
                print("move to previous song: "+player.get_media().get_mrl())

            elif b == "RIGHT" and e[0] == EVENT_RELEASED_SHORT :
                mlplayer.next()
                print("move to next song: "+player.get_media().get_mrl())

            elif b == "UP" and e[0] == EVENT_RELEASED_SHORT :
                volume = player.audio_get_volume()
                if volume < 91 :
                    volume = volume + 10
                    player.audio_set_volume(volume)
                    print("volume="+str(volume))

            elif b == "DOWN" and e[0] == EVENT_RELEASED_SHORT :
                volume = player.audio_get_volume()
                if volume > 9 :
                    volume = volume - 10
                    player.audio_set_volume(volume)
                    print("volume="+str(volume))


        elif clockMode == MODE_PANDORA :

            if b == "SET" and e[0] == EVENT_RELEASED_LONG :
                while events_queue.empty() == False :
                    e = events_queue.get_nowait()
                if pianobarPlaying :
                    stop_pianobar()
                clockMode = MODE_PLAYER
                display_msg([0x73, 0x38, 0x00, 0x77, 0x66], 9)
                print "Switching to PLAYER mode"

            elif b == "SET" and e[0] == EVENT_RELEASED_SHORT :
                if pianobarPlaying == True :
                    send_pianobar_cmd('p')
                    pianobarPlaying = False
                    print("pause pianobar")
                else :
                    send_pianobar_cmd('P')
                    pianobarPlaying = True
                    print("resume pianobar")

            elif b == "LEFT" and e[0] == EVENT_RELEASED_SHORT :
                pianobarStation += 1
                if pianobarStation > 9 :
                    pianobarStation = 0
                send_pianobar_cmd('s'+str(pianobarStation)+'\n')
                print("pianobar new station: " + str(pianobarStation))

            elif b == "RIGHT" and e[0] == EVENT_RELEASED_SHORT :
                send_pianobar_cmd('n')
                print("pianobar next song")

            elif b == "UP" and e[0] == EVENT_RELEASED_SHORT :
                send_pianobar_cmd(')))')
                print("pianobar volume up")

            elif b == "DOWN" and e[0] == EVENT_RELEASED_SHORT :
                send_pianobar_cmd('(((')
                print("pianobar volume down")

                    
        elif clockMode == MODE_ALARM :

            if darkMode == False :
                if b == "UP" and e[0] == EVENT_RELEASED_SHORT :
                    if manualBrightness < 15 :
                        manualBrightness = manualBrightness + 1
                        segment.disp.setBrightness(manualBrightness)
                        print("brightness="+str(manualBrightness))

                elif b == "DOWN" and e[0] == EVENT_RELEASED_SHORT :
                    if manualBrightness > 0 :
                        manualBrightness = manualBrightness - 1
                        segment.disp.setBrightness(manualBrightness)
                        print("brightness="+str(manualBrightness))

            if b == "SET+DOWN" and e[0] == EVENT_RELEASED_LONG :
                powerUsbBus(False)

            elif b == "SET+UP" and e[0] == EVENT_RELEASED_LONG :
                powerUsbBus(True)

            elif b == "LEFT" and e[0] == EVENT_RELEASED_LONG :
                left_long = True

            elif b == "RIGHT" and e[0] == EVENT_RELEASED_LONG :
                right_long = True


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


def display_msg(msg, delay):
    global msg_timestamp
    global msg_duration
    for i in range(len(msg)) :
        segment.writeDigitRaw(i, msg[i])
    msg_timestamp = time.time()
    msg_duration = delay


def shutdown_clock():
    segment.writeDigitRaw(0, 0x3F)
    segment.writeDigitRaw(1, 0x71)
    segment.writeDigitRaw(3, 0x71)
    segment.writeDigitRaw(4, 0x40)
    segment.setColon(False)


def update_clock():
    t = time.time()
    if t > msg_timestamp + msg_duration :
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
    gpio_states = []
    back_counts = []
    toggle_counts = []
    button_states = []
    clocks = []
    modifier_time = time.time()
    long_press_delay = 2
    sync_press_delay = 0.4
    debounce = 4

    for pin in buttons :
        io_state = GPIO.input(pin)
        gpio_states.append( io_state )
        back_counts.append( 0 )
        toggle_counts.append( 0 )
        clocks.append( time.time() )
        if io_state == True :
            button_states.append(STATE_UP)
        else:
            button_states.append(STATE_DOWN)

    modifier_index = buttons.keys().index(modifierPin)

    while not e.isSet():
        b = 0

        current_time = time.time()

        # reset SET button state if delay to wait for another button release has expired
        if button_states[modifier_index] == STATE_PENDING_SHORT_RELEASE or button_states[modifier_index] == STATE_PENDING_LONG_RELEASE :
            # time for release another button expired
            if current_time - modifier_time > sync_press_delay :
                butto_states[modifier_index] = STATE_UP

        for pin in buttons :

            # go from DOWN to HOLD if enough time has passed
            delay = time.time() - clocks[b]
            if button_states[b] == STATE_DOWN and delay > long_press_delay :
                button_states[b] = STATE_HOLD

            # read the new state
            newstate = GPIO.input(pin)

            # detect edge using debouncer if io has changed
            if newstate != gpio_states[b] :
                if toggle_counts[b] == 0 :
                    back_counts[b] = 0

                if toggle_counts[b] == debounce :
                    gpio_states[b] = newstate
                    back_counts[b] = 0
                    toggle_counts[b] = 0
                    
                    if newstate == False :
                        clocks[b] = time.time()
                        button_states[b] = STATE_DOWN
                        try :
                            events_queue.put_nowait( (EVENT_PRESSED, pin) )
                        except :
                            print "Queue full : just skip event!"
                    else :

                        # manage the SET button (modifier) in a special case
                        if b == modifier_index : 
                            other_down = False
                            for i in range(0, len(gpio_states)) :
                                if i != modifier_index :
                                    if gpio_states[i] == False :
                                        other_down = True
                            if other_down == True :
                                modifier_time = current_time
                                if delay < long_press_delay :
                                    button_states[modifier_index] = STATE_PENDING_SHORT_RELEASE
                                else :
                                    button_states[modifier_index] = STATE_PENDING_LONG_RELEASE
                            else :
                                if button_states[modifier_index] != STATE_UP :
                                    if delay < long_press_delay :
                                        events_queue.put_nowait( (EVENT_RELEASED_SHORT, modifierPin) )
                                    else :
                                        events_queue.put_nowait( (EVENT_RELEASED_LONG, modifierPin) )
                                        button_states[modifier_index] = STATE_UP

                        else :
                            if delay < long_press_delay :
                                if button_states[modifier_index] == STATE_DOWN or button_states[modifier_index] == STATE_PENDING_SHORT_RELEASE :
                                    pinKey = modifierPin + pin
                                    button_states[modifier_index] = STATE_UP
                                else :
                                    pinKey = pin
                                events_queue.put_nowait( (EVENT_RELEASED_SHORT, pinKey) )
                            else :
                                if button_states[modifier_index] == STATE_HOLD or button_states[modifier_index] == STATE_PENDING_LONG_RELEASE :
                                    pinKey = modifierPin + pin
                                    button_states[modifier_index] = STATE_UP
                                else :
                                    pinKey = pin
                                events_queue.put_nowait( (EVENT_RELEASED_LONG, pinKey) )
                            button_states[b] = STATE_UP
                    
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
        time.sleep(0.01)
    # end not event

#
# Main Program
#

# Initialize the light sensor input
GPIO.setup(lightSensorPin, GPIO.IN)

# Initialize the tactile switches inputs and callback
GPIO.setup(enablePin, GPIO.IN)
for pin in buttons:
    GPIO.setup(pin, GPIO.IN)

process_enable_switch()


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
    display_msg([0x01, 0xC1, 0x00, 0x3E, 0x73], 5)


# start monitoring tactiles switches in a different thread
e = threading.Event()
t = threading.Thread(name='monitor', target=monitor_buttons, args=(e,))
#t.deamon = True
t.start()

# add an event detection on the enablePin
GPIO.add_event_detect(enablePin, GPIO.BOTH, callback=toggle_callback, bouncetime=100)

up = True
# Main loop (now run at 4Hz: does not seem to consume more CPU and allow a quicker
# detection of the enable button
while up:
    update_clock()
    check_lighting()
    if GPIO.event_detected(enablePin) :
        process_enable_switch()
    up = process_tactile_events()
    time.sleep(0.25)


shutdown_clock()

print "finishing mcClock."
e.set()

print "final event sent."
t.join()
print "Done."

delayedShutdown = "shutdown -t 3 -h +0 &"
commands.getoutput(delayedShutdown)

# If we had an exit condition, we could restore the USB bus power,
# which would reduce the risk of hot reboot...
#powerUsbBus(True)

