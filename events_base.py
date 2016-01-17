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
    VOLUME = 2
    LIGHT = 3

    queue = Queue.Queue(16)
    volume = 5
    mode = 0
