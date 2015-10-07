#!/bin/bash

#
# USB bus power down and up test
#

lf=/tmp/usb.log
echo "test disabling usb (and thus network) bus" > ${lf}

msg()
{
    now=`date +'%Y-%m-%d %H:%M:%S'`
    echo ${now} ${1} | tee -a ${lf}
}

msg "going down"

./usbBusDown.sh | tee -a ${lf}

ps -aef | grep ntp >> $lf 2>&1

sleep 15

msg "going up"

./usbBusUp.sh | tee -a ${lf}

ps -aef |grep ntp >> $lf 2>&1
