#!/usr/bin/python -u

import RPi.GPIO as GPIO

import time

import threading
import Queue


buttons = {
    17 : "SET",
    24 : "LEFT",
    27 : "RIGHT",
    23 : "UP",
    22 : "DOWN",
}
modifierPin = 17
maxRealPin = max(buttons.keys())

enablePin = 18

#events_queue = Queue.PriorityQueue(32)
events_queue = Queue.Queue(32)

GPIO.setmode(GPIO.BCM)

for pin in buttons:
    print("configure button "+buttons[pin]+" on pin "+str(pin))
    GPIO.setup(pin, GPIO.IN)

GPIO.setup(enablePin, GPIO.IN)
GPIO.add_event_detect(enablePin, GPIO.BOTH, bouncetime=100)

STATE_UP = 1
STATE_DOWN = 2
STATE_HOLD = 3
STATE_PENDING_SHORT_RELEASE = 4
STATE_PENDING_LONG_RELEASE = 5

EVENT_PRESSED = 3
EVENT_RELEASED_SHORT = 2
EVENT_RELEASED_LONG = 1

def monitor_buttons():
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

    while True:
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
                    print "Edge detected for channel " + str(pin)
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
                        print "     button pressed"
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
                                        print "   modifier released after short press"
                                    else :
                                        events_queue.put_nowait( (EVENT_RELEASED_LONG, modifierPin) )
                                        print "   modifier released after long press"
                                        button_states[modifier_index] = STATE_UP

                        else :
                            if delay < long_press_delay :
                                if button_states[modifier_index] == STATE_DOWN or button_states[modifier_index] == STATE_PENDING_SHORT_RELEASE :
                                    pinKey = modifierPin + pin
                                    button_states[modifier_index] = STATE_UP
                                else :
                                    pinKey = pin
                                events_queue.put_nowait( (EVENT_RELEASED_SHORT, pinKey) )
                                print "    button released after short press"
                            else :
                                if button_states[modifier_index] == STATE_HOLD or button_states[modifier_index] == STATE_PENDING_LONG_RELEASE :
                                    pinKey = modifierPin + pin
                                    button_states[modifier_index] = STATE_UP
                                else :
                                    pinKey = pin
                                events_queue.put_nowait( (EVENT_RELEASED_LONG, pinKey) )
                                print "    button released after long press"
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
    # end while True

t = threading.Thread(target=monitor_buttons)
t.deamon = True
t.start()

while True:
    print "main trhead events:"
    if GPIO.event_detected(enablePin) :
        state = GPIO.input(enablePin)
        if state : 
            print "Switch ON"
        else :
            print "Switch OFF"

    while events_queue.empty() != True :
        e = events_queue.get_nowait()
        print "   channel=" + str(e[1]) + " -> " + str(e[0])
    time.sleep(2)

