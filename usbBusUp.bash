#!/bin/bash

usbDevice=/sys/devices/platform/soc/20980000.usb/buspower
check_host="www.pandora.com"

state=`cut -d " " -f 4 $usbDevice`

if [ $state == "0x1" ] ; then
    echo "usb bus is already up!"
else
    echo "powering up usb bus..."
    echo "0x1" > $usbDevice
    sleep 1
fi

echo "starting network services..."
/etc/init.d/networking start

for i in `seq 1 12` ; do
    sleep 1
    ping -c 1 $check_host > /dev/null
    ret=$?
    if [ $ret -eq 0 ] ; then
	echo "ping $check_host successfull"
	exit 0
    fi
done
echo "failed to ping $check_host"
exit 1

