import time

import Adafruit_CharLCD as LCD

class CharDisplay(object):
    # Note: line and pos arguments are given from 1 to number_of_lines
    # end internally converted to 0..number_of_lines

    NUMBER_LINES = 2
    NUMBER_CHARS = 16
    
    lines = ["" for x in range(NUMBER_LINES)]
    tempmsgs = ["tmp" for x in range(NUMBER_LINES)]
    periods = [0 for x in range(NUMBER_LINES)]
    timestamps = [0 for x in range(NUMBER_LINES)]
    expirations = [0 for x in range(NUMBER_LINES)]
    positions = [0 for x in range(NUMBER_LINES)]
    indices = [0 for x in range(NUMBER_LINES)]
    #indices = [[0 for x in range(2)] for y in range(NUMBER_LINES)]
    state = None
    color = [ 1, 1, 0 ]
    
    def __init__(self):
        self.lcd = LCD.Adafruit_CharLCDPlate()
        self.enable(True)
        self.static_msg(1, "Hello", 6)
        self.static_msg(2, "World", 6)

    def scroll_msg(self, line, msg, period):
        if (line>0) and (line<=self.NUMBER_LINES):
            line = line - 1
            self.lines[line] = msg + '   '
            self.periods[line] = period
            self.timestamps[line] = time.time() + period*(self.NUMBER_CHARS/2)
            self.indices[line] = 0
            if len(msg) <= self.NUMBER_CHARS:
                # no scrolling for short messages!
                self.periods[line] = 0
                print "scrolling message does not need to scroll!"
            self.__draw__(line)
        
    def static_msg(self, line, msg, pos):
        if (line>0) and (line<=self.NUMBER_LINES):
            line = line -1
            pos = pos - 1
            self.lines[line] = msg
            self.periods[line] = 0
            self.positions[line] = pos
            self.__draw__(line)

    def timed_msg(self, line, msg, duration):
        if (line>0) and (line<=self.NUMBER_LINES):
            line = line - 1
            msg = msg + "                        "
            self.tempmsgs[line] = msg[0:self.NUMBER_CHARS]            
            self.expirations[line] = time.time()+duration
            self.__draw__(line)
            
    def __draw__(self, l):
        if self.expirations[l] > 0:
            self.lcd.set_cursor(0, l)
            self.lcd.message(self.tempmsgs[l])
        elif self.periods[l] == 0:
            self.lcd.set_cursor(self.positions[l], l)
            self.lcd.message(self.lines[l])
        else:
            self.lcd.set_cursor(0, l)
            s = len(self.lines[l])
            p = self.indices[l]
            w = s-p-self.NUMBER_CHARS
            if w >= 0:
                self.lcd.message((self.lines[l])[p:p+self.NUMBER_CHARS])
            else:
                self.lcd.message( (self.lines[l])[p:s]+(self.lines[l])[0:-w] )

    def enable(self, state):
        if self.state != state:
            self.state = state
            if state:
                self.lcd.enable_display(True)
                self.lcd.clear()
                self.lcd.set_color(self.color[0], self.color[1], self.color[2])
            else:
                self.lcd.clear()
                self.lcd.set_color(0, 0, 0)
                self.lcd.enable_display(False)
                
    def update(self):
        # tick the display to allow dynamic effects
        now = time.time()
        for l in range(0, self.NUMBER_LINES):
            if self.expirations[l] > 0:
                if now > (self.expirations[l]):
                    self.expirations[l] = 0
                    self.__draw__(l)
            if self.periods[l] > 0:
                if now > (self.timestamps[l]):
                    self.timestamps[l] = now+self.periods[l]
                    self.indices[l] = self.indices[l] + 1
                    if self.indices[l] >= len(self.lines[l]):
                        self.indices[l] = 0
                    self.__draw__(l)
                    
                        
