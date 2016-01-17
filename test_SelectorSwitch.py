import time
import RPi.GPIO as GPIO

selector_pins = {22, 27}

# Use BMC numbering
GPIO.setmode(GPIO.BCM)

for pin in selector_pins:
    print "enable input on:", pin
    GPIO.setup(pin, GPIO.IN)


while True:
    s = 0;
    v = 0;
    for p in selector_pins:
        b = GPIO.input(p);
        print b,
        v = v | ( b << s )
        s = s + 1

    print v

    time.sleep(0.1)

