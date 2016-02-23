import spidev
import time
import threading

import RPi.GPIO as GPIO

from events_base import EventsBase
from debouncer import Debouncer

class PibEvents(EventsBase):

    POT_CHANNEL = 0
    JOY_CHANNELS = [2, 3]
    LIGHT_CHANNEL = 5
    SELECT_SWITCH_PIN = 17
    ROTARY_SWITCH_PINS = (22, 27)
    VOL_TOLERANCE = 2
    
    HIGH = 1
    LOW = 0

    # mode values correspond to the selector switch coding:
    # from most left to most right:
    # 3 -> 1 -> 0 -> 2
    MODE_ALARM = 3
    MODE_PLAYER = 1
    MODE_PANDORA = 2
    MODE_SPECIAL = 0

    mode_names = [ 'SPECIAL', 'PLAYER', 'PANDORA', 'ALARM' ]

    UPDATE_RATE = 40.0
    SELECT_DEBOUNCE_PERIOD = 0.2
    ROTARY_DEBOUNCE_PERIOD = 0.3
    ROTARY_STABLE_PERIOD = 1.2
            
    def __init__(self, i2c_lock):
        self.lock = i2c_lock
        # configure the digital pins
        GPIO.setmode(GPIO.BCM)
        self.select_switch = Debouncer(self.SELECT_SWITCH_PIN,
                                       int(self.SELECT_DEBOUNCE_PERIOD*self.UPDATE_RATE))
        self.select_state = self.select_switch.debounce()

        self.rotary_switch = []
        for i,p in enumerate(self.ROTARY_SWITCH_PINS):
            self.rotary_switch.append(Debouncer(p,
                                                int(self.ROTARY_DEBOUNCE_PERIOD*self.UPDATE_RATE)))
#        self.rotary_state = self.read_rotary_selector()
#        print "startup mode =", self.rotary_state
#        self.rotary_new = self.rotary_state
        # force to generate one mode event at startup
        self.rotary_state = -1
        self.rotary_new = -1
        self.rotary_count = 0
        
        # initialize the inputs
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)

        self.volume = 0
        self.joystick = [0, 0]
        self.light = 0
        
        # key properties:
        # code, axis_num, axis_dir, state, to_high_threshold, to_low_threshold
        self.keys = [
            [EventsBase.KEY_LEFT, 0, -1, self.LOW, 35, 10],
            [EventsBase.KEY_RIGHT, 0, 1, self.LOW, 35, 10],
            [EventsBase.KEY_UP, 1, 1, self.LOW, 70, 10],
            [EventsBase.KEY_DOWN, 1, -1, self.LOW, 70, 10]
        ]
        self.mid_pot = [512, 512]
        self.calibrate_joystick()

    def launch(self):
        """Start monitoring events.
        The launch is not part of the constructor to avoid having a thread
        accessing the hardware before all the constructors that are not
        protected by locks"""
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
            self.add_event( (self.VOLUME, self.volume) )

    def process_light_sensor(self):
        sense = int (self.readadc(self.LIGHT_CHANNEL) / 64)
        if abs(self.light - sense) > 2:
            self.light = sense
            self.add_event( (self.LIGHT, self.light) )
            
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
                self.add_event( (self.JOYSTICK, i, axis) )

        for k in self.keys:
            current_state = k[3]
            factor = k[2]
            channel = k[1]
            low_threshold = k[5]
            high_threshold = k[4]
            if current_state == self.LOW:
                if self.joystick[channel]*factor > high_threshold:
                    k[3] = self.HIGH
            else: # current HIGH state
                if self.joystick[channel]*factor < low_threshold:
                    k[3] = self.LOW
                    self.add_event( (self.KEY, k[0]) )

    def read_rotary_selector(self):
        v = 0
        for s in range(0, len(self.ROTARY_SWITCH_PINS)):
            b = self.rotary_switch[s].debounce()
            v = v | ( b << s )
        return v
            
    def process_dinputs(self):
        b = self.read_rotary_selector()
        if b != self.rotary_new:
            self.add_event( (self.ROTARY, b) )
            self.rotary_new = b
            self.rotary_count = int(self.ROTARY_STABLE_PERIOD*self.UPDATE_RATE)
        else:
            if self.rotary_count > 0:
                self.rotary_count = self.rotary_count - 1
            
        if (self.rotary_count <= 0) and (self.rotary_new != self.rotary_state):
            self.rotary_state = self.rotary_new
            self.add_event( (self.MODE, b) )
            
        s = self.select_switch.debounce()
        if self.select_state != s:
            self.select_state = s
            # event only on release
            if self.select_state == self.HIGH:
                self.add_event( (self.KEY, self.KEY_SELECT) )
                
    def monitor_events(self):
        stat_period = 10
        missed_ticks = 0
        worked_ticks = 0
        
        last_stat_time = time.time()
        
        while not self.terminate.isSet():
            
            start = time.time()
            self.lock.acquire()
            self.process_volume_pot()
            self.process_joystick()
            self.process_light_sensor()
            self.process_dinputs()
            self.lock.release()
            worked_ticks = worked_ticks + 1
            stop = time.time()
            
            sleep_time = 1.0/self.UPDATE_RATE - stop + start
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                missed_ticks = missed_ticks+1
            
            if (stop - last_stat_time) > stat_period:
                #print "ticked",worked_ticks,"in",stat_period,"at",self.UPDATE_RATE,"Hz"
                worked_ticks = 0
                if missed_ticks > 0:
                    print "warning: pib_events cannot respect",self.UPDATE_RATE,"Hz:"
                    print missed_ticks,"updates were too slow over",stat_period,"s !"
                last_stat_time = stop
                missed_ticks = 0
                
    def stop(self):
        self.terminate.set()
        self.thread.join()
        print "Pi-B events listener stopped."

