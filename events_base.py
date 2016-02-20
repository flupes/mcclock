import Queue

class EventsBase(object):
    KEY_SELECT = 0
    KEY_LEFT = 1
    KEY_RIGHT = 2
    KEY_UP = 3
    KEY_DOWN = 4
    KEY_RESET = 5
    
    MODE = 0
    KEY = 1
    LIGHT = 2
    VOLUME = 3
    JOYSTICK = 4
    ROTARY = 5

    queue = Queue.Queue(32)
    volume = 5
    mode = 0

    def add_event(self, event):
        try:
            self.queue.put_nowait( event )
        except Queue.Full:
            print "event queue full: abnormal condition!"

