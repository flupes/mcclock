#!/bin/bash

#
# USB bus power enable/disable test
#
# Test power consumption when disabling the USB bus 
# (which in turn kill the network interface), and
# verify that there is still power at the connector
# level (by powering up usb powered speaker;-)
#
# Lorenzo Flueckiger - May 2014
#

# If from a remote shell, make sure to launch in the 
# background since the connection will be lost

lf=/tmp/usb.log
echo "test disabling usb (and thus network) bus" > ${lf}

msg()
{
    now=`date +'%Y-%m-%d %H:%M:%S'`
    echo ${now} ${1} | tee -a ${lf}
}

msg "disable network"
ifdown eth0
sleep 1

msg "power off usb"
echo "0x0" > /sys/devices/platform/bcm2708_usb/buspower

msg "sleep for 15s"
sleep 15

msg "play some musing"
# Use an existing file to play
omxplayer /home/pi/Music/Various/Recusa.mp3 --pos 100 --vol -2000

msg "sleep for 15s again"
sleep 15

msg "power usb bus on"
echo "0x1" > /sys/devices/platform/bcm2708_usb/buspower

sleep 1
msg "restore networking"
ifup eth0

