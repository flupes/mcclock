import time
import datetime

# Hardcode some modules path to simplify
import sys
basedir='/home/pi/pkgs'
sys.path.append(basedir+'/Adafruit-Raspberry-Pi-Python-Code/Adafruit_LEDBackpack')

from Adafruit_7Segment import SevenSegment

class AlarmClock(object):

    def __init__(self):
        # Initialize the 7 segment display
        self.segment = SevenSegment(address=0x70)
        self.tformat = '12h'
        
        # duration a message is displayed on the 7 segments LED
        # before time display is resumed
        self.msg_duration = 0
        # time when a message start to be displayed instead of
        # the time on the 7 segments LED
        self.msg_timestamp = time.time()

        self.brightness_level = 12
        self.segment.disp.setBrightness(self.brightness_level)
        self.enabled = 0
        
    def message(self, msg, delay):
        for i in range(len(msg)) :
            self.segment.writeDigitRaw(i, msg[i])
            self.msg_timestamp = time.time()
            self.msg_duration = delay


    def shutdown(self):
        self.segment.writeDigitRaw(0, 0x3F)
        self.segment.writeDigitRaw(1, 0x71)
        self.segment.writeDigitRaw(3, 0x71)
        self.segment.writeDigitRaw(4, 0x40)
        self.segment.setColon(False)

    def set_brightness(self, level):
        if (level < 16) and (level >=0):
            self.brightness_level = level
            self.segment.disp.setBrightness(level)
            
    def update(self):
        t = time.time()
        if t > self.msg_timestamp + self.msg_duration :
            now = datetime.datetime.now()    
            hour = now.hour
            minute = now.minute
            second = now.second
            # Switch 24h / 12h format
            if self.tformat == '12h' and hour > 12 :
                hour = hour - 12
                dot = True
            else:
                dot = False
            # Set hours
            self.segment.writeDigit(0, int(hour / 10))     # Tens
            self.segment.writeDigit(1, hour % 10, dot)     # Ones
            # Set minutes
            self.segment.writeDigit(3, int(minute / 10))   # Tens
            # Ones and alarm enable (dot)
            self.segment.writeDigit(4, minute % 10, self.enabled)
            # Toggle color
            self.segment.setColon(second % 2)              # Toggle colon at 1Hz

            # # Check if alarm is necessary
            # global ringedToday
            # if GPIO.input(enablePin) == True :
            #     if not ringedToday :
            #         day = now.weekday()
            #         if now.time() > wakeup[day][0] :
            #             play_alarm(day)
            # # Update alarm state
            # global currentDay
            # if currentDay != now.day :
            #     currentDay = now.day
            #     ringedToday = False
