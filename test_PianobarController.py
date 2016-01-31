import time
import signal
from keyboard_events import KeyboardEvents
from pianobar_controller import PianobarController

up = True
ke = KeyboardEvents()
piano = PianobarController()

piano.PIANOBAR_CMD = os.environ['HOME']+'/devel/pianobar/pianobar'

def clean_exit(signum, frame):
    signal.signal(signal.SIGINT, original_sigint)
    up = False
    print "caught Ctrl-C"

# setup ctrl-c handler
#original_sigint = signal.getsignal(signal.SIGINT)
#signal.signal(signal.SIGINT, clean_exit)

print "starting pianobar test application"
print "3 = quit / 2 = launch / 1 = stop"
print "wasdx keys for control"
print "+/- for volume"

counter = 0

# main loop
while up:

    # Process input events
    while ke.queue.empty() == False:
        e = ke.queue.get_nowait()

        if e[0] == KeyboardEvents.VOLUME:
            print "VOLUME -> " + str(e[1])

        if e[0] == KeyboardEvents.MODE:
            if e[1] == 3:
                print "new mode -> STOP"                
                piano.stop()
            elif e[1] == 2:
                print "new mode -> LAUNCH"
                piano.launch()
            elif e[1] == 0:
                print "new mode -> QUIT"
                up = False
            
        if e[0] == KeyboardEvents.KEY:
            piano.process_key(e[1])
    
    song, timing, station = piano.update()

    if song is not None:
        print "got new song:",song[0],"by",song[1],"on",song[2]

    if timing is not None:
        counter = counter + 1
        if (counter % 10) == 0:
            print "timing:",timing

    if station is not None:
        print "got new station:", station
    
    # wait a little bit before processing the next events
    time.sleep(0.2)

print "stop pianobar"
piano.stop()
    
print "stop keyboard listener"
ke.stop()

print "done."
