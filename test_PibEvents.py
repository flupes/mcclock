import time
import threading
from pib_events import PibEvents

up = True

lock = threading.Lock()
pe = PibEvents(lock)

pe.launch()

while up:
    while pe.queue.empty() == False:
        e = pe.queue.get_nowait()
        
        if e[0] == PibEvents.VOLUME:
            print "volume =",str(e[1])
            
        elif e[0] == PibEvents.JOYSTICK:
            print "joystick: axis",e[1],"->",e[2]

        elif e[0] == PibEvents.KEY:
            print "keypress:", e[1]

        elif e[0] == PibEvents.MODE:
            print "new mode =", e[1]

        elif e[0] == PibEvents.LIGHT:
            print "new light =", e[1]
            
    time.sleep(0.2)

pe.stop()

print "clean exit"
