#!/usr/bin/python

import RPi.GPIO as GPIO
from Adafruit_7Segment import SevenSegment
import time
import datetime

# Initialize the 7 segment display
segment = SevenSegment(address=0x70)

# Set the default brightness
brightness=8
segment.disp.setBrightness(brightness)

# Use BMC numbering
GPIO.setmode(GPIO.BCM)

# 5 tactile switches mapping
buttons = {
    17 : "SET",
    22 : "LEFT",
    23 : "RIGHT",
    24 : "UP",
    27 : "DOWN",
}

# Callback when tactile switch is released
def button_callback(channel):
    print("Button "+buttons[channel]+"("+str(channel)+") RELEASED")
    global brightness
    if ( buttons[channel] == "UP" ) :
        if ( brightness < 15 ) :
            brightness = brightness + 1
            segment.disp.setBrightness(brightness)
    elif ( buttons[channel] == "DOWN" ) :
        if ( brightness > 0 ) :
            brightness = brightness - 1
            segment.disp.setBrightness(brightness)
    print("brightness="+str(brightness))

# Initialize the tactile switches inputs and callback
for pin in buttons:
    print("configure button "+buttons[pin]+" on pin "+str(pin))
    GPIO.setup(pin, GPIO.IN)
    GPIO.add_event_detect(pin, GPIO.RISING, callback=button_callback, bouncetime=250)
    
def update_clock():
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    second = now.second
    # Set hours
    segment.writeDigit(0, int(hour / 10))     # Tens
    segment.writeDigit(1, hour % 10)          # Ones
    # Set minutes
    segment.writeDigit(3, int(minute / 10))   # Tens
    segment.writeDigit(4, minute % 10)        # Ones
    # Toggle color
    segment.setColon(second % 2)              # Toggle colon at 1Hz
    # Wait one second

while True:
    update_clock()
    time.sleep(1)
