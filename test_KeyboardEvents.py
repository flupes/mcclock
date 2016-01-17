import time
from keyboard_events import KeyboardEvents

up = True

print "Starting test program"

ke = KeyboardEvents()

print "main thread looping"

while up:
    while ke.queue.empty() == False:
        e = ke.queue.get_nowait()

        if e[0] == KeyboardEvents.KEY:
            if e[1] == KeyboardEvents.KEY_RESET:
                print "got RESET"
                up = False
            elif e[1] == KeyboardEvents.KEY_LEFT:
                print "LEFT"
            elif e[1] == KeyboardEvents.KEY_RIGHT:
                print "RIGHT"
            elif e[1] == KeyboardEvents.KEY_UP:
                print "UP"
            elif e[1] == KeyboardEvents.KEY_DOWN:
                print "DOWN"
            elif e[1] == KeyboardEvents.KEY_SELECT:
                print "SELECT"
                
        elif e[0] == KeyboardEvents.VOLUME:
            print "new volume level = "+str(e[1])

        elif e[0] == KeyboardEvents.MODE:
            print "new mode ->"+str(e[1])
            
    time.sleep(1)

print "stopping event listener"
ke.stop()
    
print "Done."
