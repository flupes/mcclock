#!/usr/bin/python -u 

import math
import time
import commands
import random
import vlc

from pib_events import PibEvents
from char_display import CharDisplay
from alarm_clock import AlarmClock

basedir='/home/pi/code'
up = True

pe = PibEvents()
disp = CharDisplay()
clock = AlarmClock()

def isWired():
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
    return netCablePlugged

def powerUsbBus(desired_state):    
    # Turn on of off the usb bus and network
    # Return true if network connectivity is ok after powering on,
    # false otherwise, or none when powering down (no feedback)
    # Only perform function if board is not wired!
    global basedir

    if desired_state :
        print("Turning the USB bus ON")
        powerUsbBusCmd = basedir + "/mcclock/usbBusUp.bash"
        result = commands.getstatusoutput(powerUsbBusCmd)
        cmdOutput = result[1]
        if int(result[0]) == 0:
            network_state = True
            print("network connectivity ok")
        else:
            network_state = False
            print("no network connectivity")
    else :
        wired = isWired()
        # (wired is considered debug mode, we do not want the usb bus
        # to go down, certainly after startup...)
        network_state = None
        if not wired:
            print("Turning the USB bus OFF")
            powerUsbBusCmd = basedir + "/mcclock/usbBusDown.bash"
            cmdOutput = commands.getoutput(powerUsbBusCmd)
            print("Result from: "+powerUsbBusCmd+" -> "+cmdOutput)
    return network_state


def set_volume(input):
    global vol_level
    vol_level = input
    if input < 1.0:
        vol = 0
    else:
        vol = round(50.0*math.log10(0.96*input))
    print "pot returned:",input,"-> volume=",vol
    cmd = 'amixer cset numid=3 '+str(vol)+'%'
    ret = commands.getstatusoutput(cmd)
    if ret[0] != 0:
        print "command [",cmd,"]failed"

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
                print "ALARM mode -> shutdown network and disable USB bus"
                powerUsbBus(False)
                time.sleep(3.0)
                disp.enable(False)
            else:
                if (mode==PibEvents.MODE_PANDORA) or (mode==PibEvents.MODE_SPECIAL):
                    print "PANDORA or SPECIAL mode -> ",
                    print "force USB bus ON and activate network"
                    neton = powerUsbBus(True)
                    if neton == True:
                        print "network is up after powering usb"
                    else:
                        print "network did not come up after powering usb"

        if e[0] == PibEvents.VOLUME:
            set_volume(e[1])
            
        elif e[0] == PibEvents.KEY:
            print "keypress:", e[1]
            if (mode==PibEvents.MODE_SPECIAL) and (e[1]==PibEvents.KEY_DOWN):
                up = False


    disp.update()
    time.sleep(0.2)

pe.stop()
disp.enable(False)

time.sleep(1)

print "clean exit"
