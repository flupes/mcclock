#!/bin/bash

usbDevice=/sys/devices/platform/soc/20980000.usb/buspower

state=`cut -d " " -f 4 $usbDevice`

if [ $state == "0x1" ] ; then
    echo "usb bus is already up!"
else
    echo "powering up usb bus..."
    echo "0x1" > $usbDevice
    sleep 5
fi

echo "starting network services..."
/etc/init.d/networking start
