#!/bin/bash

wifi=wlan0

state=`ip link show $wifi |grep "state DOWN"`

if [ -z "$state" ] ; then
    echo "bringing down $wifi"
    ifdown $wifi
fi
