import os
import time
import threading

# Install readchar with: <-- not used anymore
# pip install readchar
# https://github.com/magmax/python-readchar
#import readchar

from events_base import EventsBase

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        from select import select
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            [i, o, e] = select([sys.stdin.fileno()], [], [], 2)
            if i: ch=sys.stdin.read(1)
            else: ch=''
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    
class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()


class KeyboardEvents(EventsBase):

    def __init__(self):
        print "launching keyboard listener thread"
        self.terminate = threading.Event()
        self.thread = threading.Thread(name='monitor', target=self.monitor_events)
        self.thread.start()
        self.volume = 8

    def monitor_events(self):
        while not self.terminate.isSet():
            c = getch()
            #c = readchar.readchar()
            if c == '0':
                self.queue.put_nowait( (self.KEY, self.KEY_RESET) )
            elif c == 'a':
                self.queue.put_nowait( (self.KEY, self.KEY_LEFT) )
            elif c == 'd':
                self.queue.put_nowait( (self.KEY, self.KEY_RIGHT) )
            elif c == 'w':
                self.queue.put_nowait( (self.KEY, self.KEY_UP) )
            elif c == 'x':
                self.queue.put_nowait( (self.KEY, self.KEY_DOWN) )
            elif c == 's':
                self.queue.put_nowait( (self.KEY, self.KEY_SELECT) )
            elif c == '1':
                self.queue.put_nowait( (self.MODE, 3) )
                self.mode = 3
            elif c == '2':
                self.queue.put_nowait( (self.MODE, 2) )
                self.mode = 2
            elif c == '3':
                self.queue.put_nowait( (self.MODE, 0) )
                self.mode = 0
            elif c == '4':
                self.queue.put_nowait( (self.MODE, 1) )
                self.mode = 1
            elif c== '+' :
                self.volume = self.volume+1
                if self.volume > 10:
                    self.volume = 10
                self.queue.put_nowait( (self.VOLUME, self.volume) )
            elif c== '-' :
                if self.volume < 0:
                    self.volume = 0
                self.volume = self.volume-1
                self.queue.put_nowait( (self.VOLUME, self.volume) )
            
    def stop(self):
        self.terminate.set()
        self.thread.join()
        print "keyboard listener stopped."
        
