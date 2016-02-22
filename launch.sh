#!/bin/bash

today=`date +%Y-%m-%d_%H%M%S`
srcdir=/home/pi/devel/mcclock
log=${srcdir}/logs/mc_${today}.log
${srcdir}/klock.py > ${log} 2>&1 &
