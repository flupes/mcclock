#!/usr/bin/python -u

import RPi.GPIO as GPIO

import threading
import time

buttons = {
    17 : "SET",
    24 : "LEFT",
    27 : "RIGHT",
    23 : "UP",
    22 : "DOWN",
}

enablePin = 18

GPIO.setmode(GPIO.BCM)


for pin in buttons:
    print("configure button "+buttons[pin]+" on pin "+str(pin))
    GPIO.setup(pin, GPIO.IN)

GPIO.setup(enablePin, GPIO.IN)
GPIO.add_event_detect(enablePin, GPIO.BOTH, bouncetime=300)


def monitor_buttons():
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
    while True:
        b = 0
        for pin in buttons :
            newstate = GPIO.input(pin)
            if newstate != states[b] :
                if toggle_counts[b] == 0 :
                    back_counts[b] = 0
                    
                if toggle_counts[b] == debounce :
                    print "Edge detected for channel " + str(pin)
                    states[b] = newstate
                    back_counts[b] = 0
                    toggle_counts[b] = 0
                    
                    if newstate == False :
                        clocks[b] = time.time()
                        print "     button pressed"
                    else :
                        delay = time.time() - clocks[pin]
                        if delay < 1 :
                            print "    button released after short press"
                        else :
                            print "    button released after long press"
                    
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
    # end while True

t = threading.Thread(target=monitor_buttons)
t.deamon = True
t.start()

while True:
    time.sleep(2)

