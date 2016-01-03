import os
import time
import threading

# Install readchar with:
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
            [i, o, e] = select([sys.stdin.fileno()], [], [], 3)
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
        self.volume = 10

    def monitor_events(self):
        while not self.terminate.isSet():
            c = getch()
            #c = readchar.readchar()
            if c == 'q':
                self.queue.put_nowait(self.QUIT)
            elif c == 'a':
                self.queue.put_nowait(self.LEFT)
            elif c == 'd':
                self.queue.put_nowait(self.RIGHT)
            elif c == 'w':
                self.queue.put_nowait(self.UP)
            elif c == 'x':
                self.queue.put_nowait(self.DOWN)
            elif c == 's':
                self.queue.put_nowait(self.SELECT)
            elif c == 'z':
                self.queue.put_nowait(self.SHUTDOWN)
            elif c== 'e' :
                self.volume = self.volume+1
                self.queue.put_nowait(self.VOLUME)
            elif c== 'c' :
                self.volume = self.volume-1
                self.queue.put_nowait(self.VOLUME)
            
    def stop(self):
        self.terminate.set()
        self.thread.join()
        print "keyboard listener stopped."
        
