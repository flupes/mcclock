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
    curr_states = {}
    prev_states = {}
    counts = {}
    clocks = {}
    for pin in buttons :
        curr_states[pin] = GPIO.input(pin)
        prev_states[pin] = curr_states[pin]
        counts[pin] = 0
        clocks[pin] = time.time()
    debounce = 5
    while True:
        for pin in buttons :
            newstate = GPIO.input(pin)
            if newstate != curr_states[pin] :
                if counts[pin] == debounce :
                    print "Edge detected for channel " + str(pin)
                    curr_states[pin] = newstate
                    if newstate == False :
                        clocks[pin] = time.time()
                        print "     button pressed"
                    else :
                        delay = time.time() - clocks[pin]
                        if delay < 1 :
                            print "    button released after short press"
                        else :
                            print "    button released after long press"
                    counts[pin] = 0
                else : 
                    counts[pin] += 1
        time.sleep(0.01)

t = threading.Thread(target=monitor_buttons)
t.deamon = True
t.start()

while True:
    time.sleep(2)

