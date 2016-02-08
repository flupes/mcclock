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
	self.custom_chars()
        self.static_msg(1, "Hello", 6)
        self.static_msg(2, "World", 6)

    def custom_chars(self):
	# great generator at: http://www.quinapalus.com/hd44780udg.html
	# 0: play
	self.lcd.create_char(0, [24,28,30,31,30,28,24,0])
	# 1: pause
	self.lcd.create_char(1, [27,27,27,27,27,27,27,0])
        # 2: left_empty
	self.lcd.create_char(2, [31,16,16,16,16,16,31,0])
	# 3: left_half
	self.lcd.create_char(3, [31,16,28,28,28,16,31,0])
	# 4: left_full
	self.lcd.create_char(4, [31,16,31,31,31,16,31,0])
	# 5: right_empty
	self.lcd.create_char(5, [31,1,1,1,1,1,31,0])
	# 6: right_half
	self.lcd.create_char(6, [31,1,25,25,25,1,31,0])
	# 7: right_full
	self.lcd.create_char(7, [31,1,31,31,31,1,31,0])

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
        
    def static_msg(self, line, msg, pos, flush=False):
        if (line>0) and (line<=self.NUMBER_LINES):
            line = line -1
            pos = pos - 1
            if flush:
                remaining = self.NUMBER_CHARS-pos-len(msg)+1
                if remaining > 0:
                    for i in range(0,remaining):
                        msg = msg+' '
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
                    self.lcd.set_cursor(0, l)
                    self.lcd.message("                        ")
                    self.__draw__(l)
            if self.periods[l] > 0:
                if now > (self.timestamps[l]):
                    self.timestamps[l] = now+self.periods[l]
                    self.indices[l] = self.indices[l] + 1
                    if self.indices[l] >= len(self.lines[l]):
                        self.indices[l] = 0
                    self.__draw__(l)
                    
                        
