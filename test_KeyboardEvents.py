import time
from keyboard_events import KeyboardEvents

up = True

print "Starting test program"

ke = KeyboardEvents()

print "main thread looping"

while up:
    while ke.queue.empty() == False:
        e = ke.queue.get_nowait()

        if e == KeyboardEvents.QUIT:
            print "got QUIT"
            up = False
        elif e == KeyboardEvents.LEFT:
            print "LEFT"
        elif e == KeyboardEvents.RIGHT:
            print "RIGHT"
        elif e == KeyboardEvents.UP:
            print "UP"
        elif e == KeyboardEvents.DOWN:
            print "DOWN"
        elif e == KeyboardEvents.SELECT:
            print "SELECT"
        elif e == KeyboardEvents.SHUTDOWN:
            print "SHUTDOWN"

    time.sleep(1)

print "stopping event listener"
ke.stop()
    
print "Done."
