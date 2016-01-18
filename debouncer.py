import time
import RPi.GPIO as GPIO

class Debouncer(object):
    def __init__(self, pin, count):
        self.pin = pin
        GPIO.setup(pin, GPIO.IN)
        time.sleep(0.04)
        self.state = GPIO.input(pin)
        if self.state == 0:
            self.integrator = 0
        else:
            self.integrator = count
        self.maximum = count

    def debounce(self):
        # Reworked my previous complex integrator using inspiration
        # from Kenneth A. Kuhn simpler C code found on:
        # http://hackaday.com/2010/11/09/debounce-code-one-post-to-rule-them-all/
        input = GPIO.input(self.pin)
        # integrate the signal
        if input == 0:
            if self.integrator > 0:
                self.integrator = self.integrator - 1
        elif self.integrator < self.maximum:
            self.integrator = self.integrator + 1
        # compute the filtered output
        if self.integrator == 0:
            self.state = 0
        elif self.integrator >= self.maximum:
            self.state = 1
            self.integrator = self.maximum # just to make sure
        return self.state
