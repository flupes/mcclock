#!/bin/bash

check_host="www.pandora.com"

network_available()
{
    for i in `seq 1 10` ; do
	sleep 1
	ping -c 1 $check_host > /dev/null
	ret=$?
	if [ $ret -eq 0 ] ; then
	    return 1
	fi
    done
    return 0
}

network_available
avail=$?

echo $avail

if [ $avail -eq 1 ] ; then
    echo "Can ping $check_host"
else
    echo "No connectivity to $check_host"
fi

