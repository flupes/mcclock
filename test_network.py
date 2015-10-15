#!/usr/bin/python

import time
import subprocess

host = 'www.google.com'
ping = '/bin/ping -c 1'
netup = False

for i in range(1, 10) :
    try:
        cmd = ping+" "+host
        print "calling: " + cmd
        ret = subprocess.check_call(cmd, shell=True)
        print "ping #" + str(i) + "succeded!"
        netup = True
    except:
        print "ping #" + str(i) + " failed..."
    if netup :
        break
    time.sleep(1)

if netup :
    print "Network is UP"
else :
    print "Network is DOWN"
