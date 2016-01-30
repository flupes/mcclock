#!/usr/bin/python -u 

import time
import commands
import random
import vlc

from pib_events import PibEvents
from char_display import CharDisplay
from alarm_clock import AlarmClock

from utilities import is_wired, power_usb_bus, set_hw_volume

up = True

pe = PibEvents()
disp = CharDisplay()
clock = AlarmClock()


mode = pe.rotary_state
vol_level = 0
clock.set_brightness(6)

time.sleep(1.0)
disp.lcd.home()
disp.lcd.message(" Klock Musical\nAlarm/Wifi Radio")
time.sleep(1.0)

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
                clock.alarm_enabled = True
                clock.update() # force updating the display since powering down
                               # takes some time
                print "ALARM mode -> shutdown network and disable USB bus"
                power_usb_bus(False)
                time.sleep(3.0)
                disp.enable(False)
            else:
                clock.alarm_enabled = False
                clock.update() # force updating lcd display
                if (mode==PibEvents.MODE_PANDORA) or (mode==PibEvents.MODE_SPECIAL):
                    print "PANDORA or SPECIAL mode -> ",
                    print "force USB bus ON and activate network"
                    neton = power_usb_bus(True)
                    if neton == True:
                        print "network is up after powering usb"
                    else:
                        print "network did not come up after powering usb"

        if e[0] == PibEvents.VOLUME:
            vol_level = set_hw_volume(e[1])
            
        elif e[0] == PibEvents.KEY:
            print "keypress:", e[1]
            if (mode==PibEvents.MODE_SPECIAL) and (e[1]==PibEvents.KEY_DOWN):
                # special condition to exit
                up = False

    clock.update()
    disp.update()
    time.sleep(0.2)

pe.stop()
disp.enable(False)
clock.segment.disp.clear()
clock.set_brightness(0)

time.sleep(1)

print "clean exit"
