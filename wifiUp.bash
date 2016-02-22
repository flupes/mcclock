#!/bin/bash

wifi=wlan0
check_host="www.pandora.com"

state=`ip link show $wifi |grep "state UP"`

if [ -z "$state" ] ; then
    echo "bring up $wifi"
    ifup $wifi
fi

for i in `seq 1 20` ; do
    ping -c 1 $check_host > /dev/null
    ret=$?
    if [ $ret -eq 0 ] ; then
	echo "ping $check_host successfull"
	exit 0
    fi
    sleep 1
done

echo "failed to ping $check_host"
exit 1
