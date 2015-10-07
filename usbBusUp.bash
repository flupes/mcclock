#!/bin/bash

usbDevice=/sys/devices/platform/soc/20980000.usb/buspower

echo "powering up usb bus..."
echo "0x1" > $usbDevice

sleep 1

echo "starting network services..."
/etc/init.d/networking start
