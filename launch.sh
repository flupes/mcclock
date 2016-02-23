#!/bin/bash

srcdir=`dirname $0`
today=`date +%Y-%m-%d_%H%M%S`
log=${srcdir}/logs/mc_${today}.log
echo ${today} > ${log}
echo "starting MC clock as a service" >> ${log}

${srcdir}/klock.py >> ${log} 2>&1
