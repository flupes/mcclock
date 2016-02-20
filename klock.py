#!/usr/bin/python -u 
import time
import threading

from pib_events import PibEvents
from char_display import CharDisplay
from alarm_clock import AlarmClock
from pianobar_controller import PianobarController

from utilities import is_wired, power_usb_bus, set_hw_volume

import Adafruit_CharLCD as LCD

up = True

pe = PibEvents()
chlcd = CharDisplay()
clock = AlarmClock()
piano = PianobarController(chlcd)

#mode = pe.rotary_state
exit_mode = [ None, None, None, None ]
enter_mode = [ None, None, None, None ]
mode = None
current_volume_level = 0

clock.message([0x01, 0xC1, 0x00, 0x3E, 0x73], 3)
clock.set_brightness(6)

time.sleep(0.2)
chlcd.lcd.home()
chlcd.lcd.message(" Klock Musical\nAlarm/Wifi Radio")
time.sleep(0.3)

def monitor_reset(char_lcd):
    global reset_terminate
    up = True
    count = 3
    print "staring to monitor SELECT button of Adafruit Char LCD"
    while not reset_terminate.isSet() and up:
        if char_lcd.is_pressed(LCD.SELECT):
            count = count - 1
        else:
            count = 3
        if count < 0:
            up = False
        time.sleep(1.0)
        
    print "detected reset signal!"
    cmd = "sudo shutdown -h now"
    res = commands.getstatusoutput(cmd)
    # should never get there...
    print cmd,"->",res

reset_terminate = threading.Event()
reset_thread = threading.Thread(name='reset', target=monitor_reset, args=[chlcd.lcd])
reset_thread.start()

def update_usb_power(enable):
    if enable == True:
        print "force USB bus ON and activate network"
        neton = power_usb_bus(True)
        if neton == True:
            print "network is up after powering usb"
        else:
            print "network did not come up after powering usb"
    else:
        print "shutdown network and disable USB bus"
        power_usb_bus(False)
        time.sleep(1.0)

def enter_alarm():
    print "entering alarm mode"
    clock.enable(True)
    clock.update()
    update_usb_power(False)
    chlcd.enable(False)

def exit_alarm():
    print "leaving alarm mode"
    clock.enable(False)
    clock.update()
    
def enter_player():
    print "entering player mode"
    update_usb_power(False)
    chlcd.enable(True)
    clock.set_music_dir(clock.musicdir)
    
def exit_player():
    print "leaving player mode"
    clock.stop()

def enter_pandora():
    print "entering pandora mode"
    update_usb_power(True)
    chlcd.enable(True)
    piano.launch()
    
def exit_pandora():
    print "leaving pandora mode"
    piano.stop()
    chlcd.clear()
    
def enter_special():
    print "entering special mode"
    # we want network in special mode to enable debugging
    update_usb_power(True)
    
def exit_special():
    print "leaving special mode"
    
enter_mode[PibEvents.MODE_ALARM] = enter_alarm
enter_mode[PibEvents.MODE_PLAYER] = enter_player
enter_mode[PibEvents.MODE_PANDORA] = enter_pandora
enter_mode[PibEvents.MODE_SPECIAL] = enter_special
           
exit_mode[PibEvents.MODE_ALARM] = exit_alarm
exit_mode[PibEvents.MODE_PLAYER] = exit_player
exit_mode[PibEvents.MODE_PANDORA] = exit_pandora
exit_mode[PibEvents.MODE_SPECIAL] = exit_special
           
while up:
    while pe.queue.empty() == False:
        e = pe.queue.get_nowait()

        # process mode events in any mode
        if e[0] == PibEvents.MODE:
            # exit old mode
            if mode is not None:
                print "old mode =", mode
                exit_mode[mode]()

            # entering new mode
            mode = e[1]
            print "new mode =", mode
            enter_mode[mode]()

        elif e[0] == PibEvents.ROTARY:
            chlcd.timed_msg(1, PibEvents.mode_names[e[1]], 2)

        elif e[0] == PibEvents.VOLUME:
            current_volume_level = set_hw_volume(e[1])
        
        elif e[0] == PibEvents.KEY:
            print "detected keypress:", e[1]
            if mode == PibEvents.MODE_ALARM:
                print "skip key events in alarm mode"
            elif mode == PibEvents.MODE_PLAYER:
                clock.process_key(e[1])
            elif mode == PibEvents.MODE_PANDORA:
                piano.process_key(e[1])
            elif mode==PibEvents.MODE_SPECIAL:
                if e[1]==PibEvents.KEY_DOWN:
                    # special condition to exit
                    up = False

    alarm = clock.update()
    if alarm == True:
        print "WAKEUP!"

    if mode == PibEvents.MODE_PANDORA:
        piano.update()
        
    chlcd.update()
    time.sleep(0.2)

print "wait for reset monitor thread to terminate"
reset_terminate.set()
reset_thread.join()

print "stopping other hardware"
pe.stop()
chlcd.enable(False)
clock.segment.disp.clear()
clock.set_brightness(0)

time.sleep(0.5)

print "clean exit"
