#!/usr/bin/python

import sys
import time
import threading
import subprocess

pianobarPlaying = False
pianobarProcess = None

def monitor_pianobar(piano):
    global pianobarPlaying

    pianobarPlaying = True
    
    print "pianobar output:"
    out = piano.stdout

    for line in iter(out.readline, 'b'):
        print(line)
    out.close()

print "spawning pianobar..."
pianobarProcess = subprocess.Popen('pianobar', shell=True,
                                   stdout=subprocess.PIPE,
                                   stdin=subprocess.PIPE)

t = threading.Thread(name='piano', target=monitor_pianobar, args=(pianobarProcess,))
t.daemon = True
t.start()

print "state = " + str(pianobarPlaying)

ctrl = pianobarProcess.stdin

time.sleep(12)
print "increase volume"
ctrl.write('))')

time.sleep(6)
print "select station 6"
ctrl.write('s6\n')

time.sleep(12)
print "quit"
ctrl.write('q')

time.sleep(6)
