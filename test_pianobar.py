#!/usr/bin/python

import sys
import time
import threading
import subprocess

pianobarPlaying = False
pianobarProcess = None

def monitor_pianobar(piano):
    global pianobarPlaying

    print "pianobar output:"
    out = piano.stdout
    up='Get stations... Ok.'

    for line in iter(out.readline, ''):
        if not pianobarPlaying :
            if up in line :
                pianobarPlaying = True
        print(line),
    print "monitor terminated"

print "spawning pianobar..."
pianobarProcess = subprocess.Popen('pianobar', shell=True,
                                   stdout=subprocess.PIPE,
                                   stdin=subprocess.PIPE)

t = threading.Thread(name='piano', target=monitor_pianobar, args=(pianobarProcess,))
t.daemon = True
t.start()

print "state = " + str(pianobarPlaying)

ctrl = pianobarProcess.stdin

for i in range(1, 30) :
    if pianobarPlaying :
        break;
    time.sleep(1)

if pianobarPlaying:
    print "pianobar seems to be up :-)"

    time.sleep(12)
    print "decrease volume"
    ctrl.write('((((')

    time.sleep(6)
    print "select station 6"
    ctrl.write('s6\n')

    time.sleep(12)
    print "quit"
    ctrl.write('q')

    print "wait for monitor to join"
    t.join()
    print "main thread done."
else:
    print "pianobar did not come up correctly!"

