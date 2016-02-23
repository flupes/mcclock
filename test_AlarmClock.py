import time
import signal
import datetime
import threading

from alarm_clock import AlarmClock
from utilities import set_hw_volume

lock = threading.Lock()
clock = AlarmClock(lock)
up = True

def clean_exit(signum, frame):
    global up
    signal.signal(signal.SIGINT, original_sigint)
    up = False

original_sigint = signal.getsignal(signal.SIGINT)
signal.signal(signal.SIGINT, clean_exit)

now = datetime.datetime.now()
clock.wakeup[now.weekday()] = ( datetime.time(now.hour, now.minute+1), "song.mp3" )
clock.alarm_enabled = True
clock.ringed_today = False
clock.number_of_wakeup_songs = 2
clock.volume_rampup_time = 20

set_hw_volume(5)

clock.message([0x01, 0xC1, 0x00, 0x3E, 0x73], 3)

time.sleep(2)
clock.set_brightness(6)

while up:
    alarm = clock.update()
    if alarm == True:
        print "WAKE UP!"
    time.sleep(0.2)

clock.shutdown()
time.sleep(0.2)
