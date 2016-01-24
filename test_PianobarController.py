import time
import signal
from keyboard_events import KeyboardEvents
from pianobar_controller import PianobarController

up = True
ke = KeyboardEvents()
piano = PianobarController()

def clean_exit(signum, frame):
    signal.signal(signal.SIGINT, original_sigint)
    up = False
    print "caught Ctrl-C"

# setup ctrl-c handler
#original_sigint = signal.getsignal(signal.SIGINT)
#signal.signal(signal.SIGINT, clean_exit)

print "starting pianobar test application"

counter = 0
station_list = []
station_index = 1
current_station = None

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
                    piano.select_station(station_list[station_index][0])
                    piano.mode = PianobarController.PLAYING
                elif e[1] == KeyboardEvents.KEY_UP:
                    if station_index < len(station_list)-1:
                        station_index=station_index+1
                    print "current selection =",station_list[station_index][0],
                    print "->",station_list[station_index][1]
                elif e[1] == KeyboardEvents.KEY_DOWN:
                    if station_index > 0:
                        station_index=station_index-1
                    print "current selection =",station_list[station_index][0],
                    print "->",station_list[station_index][1]
            elif piano.mode != PianobarController.OFF:
                if e[1] == KeyboardEvents.KEY_LEFT:
                    # flush pending events to switch mode
                    while ke.queue.empty() == False:
                        ke.queue.get_nowait()
                    piano.mode = PianobarController.STATION
                    print "STATION"
                    station_list = piano.get_stations()
                    station_index = 0
                    for s in station_list:
                        if current_station == s[1]:
                            break;
                        station_index = station_index+1
                    if station_index == len(station_list):
                        print "current station not found in list!"
                        station_index = 1
                    print station_list
                    print "current station index is:", station_index
                elif e[1] == KeyboardEvents.KEY_SELECT:
                    if piano.mode == PianobarController.PLAYING:
                        print "PAUSE"
                        piano.pause()
                    elif piano.mode == PianobarController.PAUSED:
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

    song, timing, station = piano.update()

    if song is not None:
        print "got new song:",song[0],"by",song[1],"on",song[2]

    if timing is not None:
        counter = counter + 1
        if (counter % 10) == 0:
            print "timing:",timing

    if station is not None:
        current_station = station
        print "got new station:", station
    
    # wait a little bit before processing the next events
    time.sleep(0.2)

print "stop pianobar"
piano.stop()
    
print "stop keyboard listener"
ke.stop()

print "done."
