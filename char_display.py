import time

import Adafruit_CharLCD as LCD

class CharDisplay(object):

    NUMBER_LINES = 2
    NUMBER_CHARS = 16
    
    lines = list(xrange(NUMBER_LINES))
    periods = list(xrange(NUMBER_LINES))
    timestamps = list(xrange(NUMBER_LINES))
    positions = list(xrange(NUMBER_LINES))
    indices = list(xrange(NUMBER_LINES))
    #indices = [[0 for x in range(2)] for y in range(NUMBER_LINES)]
        
    def __init__(self):
        self.lcd = LCD.Adafruit_CharLCDPlate()
        self.lcd.clear()
        self.static_msg(0, "Hello", 5)
        self.static_msg(1, "World", 5)

    def scroll_msg(self, line, msg, period):
        if line < self.NUMBER_LINES:
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
        if line < self.NUMBER_LINES:
            self.lines[line] = msg
            self.periods[line] = 0
            self.positions[line] = pos
            sz = len(msg)+pos
            if sz > self.NUMBER_CHARS:
                self.indices[line] = self.NUMBER_CHARS+1
            else:
                self.indices[line] = sz+1
            self.__draw__(line)

    def __draw__(self, l):
        if self.periods[l] == 0:
            self.lcd.set_cursor(self.positions[l], l)
            self.lcd.message((self.lines[l])[0:self.indices[l]])
        else:
            self.lcd.set_cursor(0, l)
            s = len(self.lines[l])
            p = self.indices[l]
            w = s-p-self.NUMBER_CHARS
            if w >= 0:
                self.lcd.message((self.lines[l])[p:p+self.NUMBER_CHARS])
            else:
                self.lcd.message( (self.lines[l])[p:s]+(self.lines[l])[0:-w] )
                
    def update(self):
        # tick the display to allow dynamic effects
        now = time.time()
        for l in range(0, self.NUMBER_LINES):
            if self.periods[l] > 0:
                if now > (self.timestamps[l]):
                    self.timestamps[l] = now+self.periods[l]
                    self.indices[l] = self.indices[l] + 1
                    if self.indices[l] >= len(self.lines[l]):
                        self.indices[l] = 0
                    self.__draw__(l)
                    
                        
