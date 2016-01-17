import time
import signal
from keyboard_events import KeyboardEvents
from pianobar_controller import PianobarController

up = True
ke = KeyboardEvents()
piano = PianobarController(ke, 0)

def clean_exit(signum, frame):
    signal.signal(signal.SIGINT, original_sigint)
    up = False
    print "caught Ctrl-C"

# setup ctrl-c handler
#original_sigint = signal.getsignal(signal.SIGINT)
#signal.signal(signal.SIGINT, clean_exit)

print "starting pianobar test application"

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
            if piano.mode == PianobarController.STATION:
                if e[1] == KeyboardEvents.KEY_SELECT:
                    print "select station not implemented yet"
                    piano.play()
                elif e[1] == KeyboardEvents.KEY_UP:
                    print "prev station not implemented yet"
                elif e[1] == KeyboardEvents.KEY_DOWN:
                    print "next station not implemented yet"
            elif piano.mode != PianobarController.OFF:
                if e[1] == KeyboardEvents.KEY_LEFT:
                    # flush pending events to switch mode
                    while ke.queue.empty() == False:
                        ke.queue.get_nowait()
                    piano.mode = PianobarController.STATION
                    print "STATION"
                elif e[1] == KeyboardEvents.KEY_SELECT:
                    if self.mode == PianobarController.PLAYING:
                        print "PAUSE"
                        piano.pause()
                    elif self.mode == PianobarController.PAUSED:
                        print "PLAY"
                        piano.play()
                elif e[1] == KeyboardEvents.KEY_RIGHT:
                    print "NEXT"
                    piano.next()
                elif e[1] == KeyboardEvents.KEY_UP:
                    print "LOVE"
                    piano.love()
                elif e[1] == KeyboardEvents.KEY_DOWN:
                    print "TIRED"
                    piano.tired()

    piano.update()
    # wait a little bit before processing the next events
    time.sleep(0.2)

print "stop pianobar"
piano.stop()
    
print "stop keyboard listener"
ke.stop()

print "done."
