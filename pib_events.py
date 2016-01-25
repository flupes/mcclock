import spidev
import time
import threading

import RPi.GPIO as GPIO

from events_base import EventsBase
from debouncer import Debouncer

class PibEvents(EventsBase):

    POT_CHANNEL = 0
    JOY_CHANNELS = [2, 3]
    SELECT_SWITCH_PIN = 17
    ROTARY_SWITCH_PINS = (22, 27)
    
    VOL_TOLERANCE = 2

    HIGH = 1
    LOW = 0

    # mode values correspond to the selector switch coding:
    # from most left to most right:
    # 3 -> 2 -> 0 -> 1
    MODE_ALARM = 3
    MODE_PLAYER = 1
    MODE_PANDORA = 0
    MODE_SPECIAL = 2
    
    mode_names = [ 'PANDORA', 'PLAYER', 'SPECIAL', 'ALARM' ]

    UPDATE_RATE = 20
    SELECT_DEBOUNCE_PERIOD = 0.1
    ROTARY_DEBOUNCE_PERIOD = 0.3
    ROTARY_STABLE_PERIOD = 1.2
            
    def __init__(self):
        # configure the digital pins
        GPIO.setmode(GPIO.BCM)
        self.select_switch = Debouncer(self.SELECT_SWITCH_PIN,
                                       int(self.SELECT_DEBOUNCE_PERIOD*self.UPDATE_RATE))
        self.select_state = self.select_switch.debounce()

        self.rotary_switch = []
        for i,p in enumerate(self.ROTARY_SWITCH_PINS):
            self.rotary_switch.append(Debouncer(p,
                                                int(self.ROTARY_DEBOUNCE_PERIOD*self.UPDATE_RATE)))
        self.rotary_state = self.read_rotary_selector()
        print "startup mode =", self.rotary_state
        self.rotary_new = self.rotary_state
        self.rotary_count = 0
        
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
        self.last_update = time.time()
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
        v = 0
        for s in range(0, len(self.ROTARY_SWITCH_PINS)):
            b = self.rotary_switch[s].debounce()
            v = v | ( b << s )
        return v
            
    def process_dinputs(self):
        b = self.read_rotary_selector()
        if b != self.rotary_new:
            self.rotary_new = b
            self.rotary_count = self.ROTARY_STABLE_PERIOD*self.UPDATE_RATE
        else:
            if self.rotary_count > 0:
                self.rotary_count = self.rotary_count - 1
            
        if (self.rotary_count == 0) and (self.rotary_new != self.rotary_state):
            self.rotary_state = self.rotary_new
            self.queue.put_nowait( (self.MODE, b) )
            
        s = self.select_switch.debounce()
        if self.select_state != s:
            self.select_state = s
            # event only on release
            if self.select_state == self.HIGH:
                self.queue.put_nowait( (self.KEY, self.KEY_SELECT) )
            
    def monitor_events(self):
        stat_period = 10
        missed_ticks = 0
        last_stat_time = time.time()
        while not self.terminate.isSet():

            self.process_volume_pot()
            self.process_joystick()
            self.process_dinputs()

            now = time.time()
            sleep_time = 1.0/self.UPDATE_RATE - now + self.last_update
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                missed_ticks = missed_ticks+1
            self.last_update = now
            if (now - last_stat_time) > stat_period:
                if missed_ticks > 0:
                    print "warning: pib_events cannot respect",self.UPDATE_RATE,"Hz:"
                    print missed_ticks,"updates were too slow over",stat_period,"s !"
                last_stat_time = now
                missed_ticks = 0
                
    def stop(self):
        self.terminate.set()
        self.thread.join()
        print "Pi-B events listener stopped."

