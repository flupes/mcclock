import spidev
import time
import threading

import RPi.GPIO as GPIO

from events_base import EventsBase

class PibEvents(EventsBase):

    POT_CHANNEL = 0
    JOY_CHANNELS = [2, 3]
    SEL_PIN = 17
    ROT_PINS = (22, 27)
    
    VOL_TOLERANCE = 4

    HIGH = 1
    LOW = 0
    
    def __init__(self):
        # configure the digital pins
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.SEL_PIN, GPIO.IN)
        self.select_switch = self.HIGH
        GPIO.setup(self.ROT_PINS[0], GPIO.IN)
        GPIO.setup(self.ROT_PINS[1], GPIO.IN)
        self.rotary_selector = self.read_rotary_selector()
        print "startup mode =", self.rotary_selector
        
        # initialize the inputs
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)

        self.volume = 0
        self.joystick = [0, 0]
        self.keys = [
            [EventsBase.KEY_LEFT, 0, -1, self.LOW],
            [EventsBase.KEY_RIGHT, 0, 1, self.LOW],
            [EventsBase.KEY_UP, 1, 1, self.LOW],
            [EventsBase.KEY_DOWN, 1, -1, self.LOW]
        ]
        self.mid_pot = [512, 512]
        self.calibrate_joystick()

        print "starting Pi-B events listener"
        self.terminate = threading.Event()
        self.thread = threading.Thread(name='monitor', target=self.monitor_events)
        self.thread.start()

    # read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
    def readadc(self, adcnum):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
	r = self.spi.xfer2([1,(8+adcnum)<<4,0])
	adcout = ((r[1]&3) << 8) + r[2]
	return adcout

    def process_volume_pot(self):
        # read potentiometer
        pot = self.readadc(self.POT_CHANNEL)
        # scale to 0-100
        vol = int(round(pot / 10.24))
        # queue if significant changes
        if abs(self.volume-vol) > self.VOL_TOLERANCE:
            self.volume = vol
            self.queue.put_nowait( (self.VOLUME, self.volume) )

    def calibrate_joystick(self):
        samples=6
        pot_x = 0
        pot_y = 0
        time.sleep(0.1)
        for i in range(0,samples):
            pot_x = pot_x+self.readadc(self.JOY_CHANNELS[0])
            pot_y = pot_y+self.readadc(self.JOY_CHANNELS[1])
            time.sleep(0.05)
        self.mid_pot[0] = pot_x/samples
        self.mid_pot[1] = pot_y/samples
        print "joystick calibration:",self.mid_pot[0], self.mid_pot[1]
            
    def process_joystick(self):
        for i, ch in enumerate(self.JOY_CHANNELS):
            val = self.readadc(ch)
            # normalize in (-100, 100)
            if val < self.mid_pot[i]:
                axis = 100*(val-self.mid_pot[i])/self.mid_pot[i]
            else:
                axis = 100*(val-self.mid_pot[i])/(1023-self.mid_pot[i])
            if abs(axis-self.joystick[i])>2:
                self.joystick[i] = axis
                self.queue.put_nowait( (self.JOYSTICK, i, axis) )

        for k in self.keys:
            current_state = k[3]
            factor = k[2]
            channel = k[1]
            if current_state == self.LOW:
                if self.joystick[channel]*factor > 30:
                    k[3] = self.HIGH
            else: # current HIGH state
                if self.joystick[channel]*factor < 10:
                    k[3] = self.LOW
                    self.queue.put_nowait( (self.KEY, k[0]) )

    def read_rotary_selector(self):
        s = 0
        v = 0
        for p in self.ROT_PINS:
            b = GPIO.input(p)
            v = v | ( b << s )
            s = s + 1
        return v
    
    def process_dinputs(self):
        b = self.read_rotary_selector()
        if self.rotary_selector != b:
            self.rotary_selector = b
            self.queue.put_nowait( (self.MODE, b) )
                    
    def monitor_events(self):
        while not self.terminate.isSet():

            self.process_volume_pot()
            self.process_joystick()
            self.process_dinputs()
            
            time.sleep(0.04)
            
    def stop(self):
        self.terminate.set()
        self.thread.join()
        print "Pi-B events listener stopped."

