import Queue

class EventsBase(object):
    QUIT = 0
    LEFT = 1
    RIGHT = 2
    UP = 3
    DOWN = 4
    SELECT = 5
    VOLUME = 6
    USB_ON = 7
    USB_OFF = 8
    SHUTDOWN = 9

    queue = Queue.Queue(32)
    volume = 5

