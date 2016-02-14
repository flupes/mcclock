#!/usr/bin/python -u 

import time

from pib_events import PibEvents
from char_display import CharDisplay
from alarm_clock import AlarmClock
from pianobar_controller import PianobarController

from utilities import is_wired, power_usb_bus, set_hw_volume

up = True

pe = PibEvents()
disp = CharDisplay()
clock = AlarmClock()
piano = PianobarController()

mode = pe.rotary_state
current_volume_level = 0

clock.message([0x01, 0xC1, 0x00, 0x3E, 0x73], 3)
clock.set_brightness(6)

time.sleep(1.0)
disp.lcd.home()
disp.lcd.message(" Klock Musical\nAlarm/Wifi Radio")
time.sleep(1.0)

def update_alarm_state(prev_mode, alarm):
    global clock
    if alarm == True:
        clock.enable(True)
    elif prev_mode == PibEvents.MODE_ALARM:
        clock.enable(False)
    # force display update since next action (like usb bus) could
    # take a long time
    clock.update() 

def update_pandora_state(prev_mode, pandora):
    global piano
    if pandora == True:
        piano.launch()
    elif prev_mode == PibEvents.MODE_PANDORA:
        piano.stop()
        disp.lcd.clear()        

def update_usb_power(new_mode, enable):
    global mode
    if new_mode != PibEvents.MODE_PLAYER:
        if enable == True:
            print "force USB bus ON and activate network"
            neton = power_usb_bus(True)
            if neton == True:
                print "network is up after powering usb"
            else:
                print "network did not come up after powering usb"
        else:
            print "ALARM mode -> shutdown network and disable USB bus"
            power_usb_bus(False)
            time.sleep(1.0)
    mode = new_mode
    
def switch_to_alarm(prev_mode):
    update_alarm_state(prev_mode, True)
    update_pandora_state(prev_mode, False)
    update_usb_power(PibEvents.MODE_ALARM, False)
    disp.enable(False)

def switch_to_player(prev_mode):
    update_alarm_state(prev_mode, False)
    update_pandora_state(prev_mode, False)
    update_usb_power(PibEvents.MODE_PLAYER, False)
    clock.set_music_dir(clock.musicdir)
    disp.enable(True)
    
def switch_to_pandora(prev_mode):
    update_alarm_state(prev_mode, False)
    update_pandora_state(prev_mode, True)
    update_usb_power(PibEvents.MODE_PANDORA, True)
    disp.enable(True)
    
def switch_to_special(prev_mode):
    update_alarm_state(prev_mode, False)
    update_pandora_state(prev_mode, False)
    update_usb_power(PibEvents.MODE_SPECIAL, True)
    disp.enable(True)

def process_player_key(k):
    if k == PibEvents.KEY_SELECT:
        if player.is_playing() :
            clock.mlplayer.pause()
            print("pausing player")
        else :
            clock.mlplayer.play()
            print("start to play song: "+player.get_media().get_mrl())

    elif k == PibEvents.KEY_LEFT:
        clock.mlplayer.previous()
        print("move to previous song: "+player.get_media().get_mrl())

    elif k == PibEvents.KEY_RIGHT:
        clock.mlplayer.next()
        print("move to next song: "+player.get_media().get_mrl())


while up:
    while pe.queue.empty() == False:
        e = pe.queue.get_nowait()

        # process mode events in any mode
        if e[0] == PibEvents.MODE:
            mode = e[1]
            print "new mode =", mode
            if disp.state == False:
                disp.enable(True)
            disp.timed_msg(1, PibEvents.mode_names[mode], 5)

            if mode == PibEvents.MODE_ALARM:
                switch_to_alarm(mode)
            elif mode == PibEvents.MODE_PLAYER:
                switch_to_player(mode)    
            elif mode == PibEvents.MODE_PANDORA:
                switch_to_pandora(mode)
            elif mode == PibEvents.MODE_SPECIAL:
                switch_to_special(mode)

        if e[0] == PibEvents.VOLUME:
            current_volume_level = set_hw_volume(e[1])
            
        elif e[0] == PibEvents.KEY:
            print "detected keypress:", e[1]
            if mode == PibEvents.MODE_ALARM:
                print "skip key events in alarm mode"
            elif mode == PibEvents.MODE_PLAYER:
                player_process_key(e[1])
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
        song, timing, station = piano.update()
        if station is not None:
            disp.static_msg(1, station, 1)
        if song is not None:
            disp.scroll_msg(2, song[0]+" | "+song[1], 0.3)
        
    disp.update()
    time.sleep(0.2)

pe.stop()
disp.enable(False)
clock.segment.disp.clear()
clock.set_brightness(0)

time.sleep(1)

print "clean exit"
