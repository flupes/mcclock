#!/bin/bash

usbDevice=/sys/devices/platform/soc/20980000.usb/buspower

echo "stoping network services..."
/etc/init.d/networking stop

sleep 1

echo "powering usb bus down..."
echo "0x0" > $usbDevice

