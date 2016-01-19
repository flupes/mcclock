import time
import signal
import datetime

from alarm_clock import AlarmClock

clock = AlarmClock()
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
