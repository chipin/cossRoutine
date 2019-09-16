#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/cnr
progname="get_scope_iprange_k.py"
logname="/ap/home/coss/log/cnr/get_scope_iprangek.log"

echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start"
./${progname} 240 > ${logname} 2>&1
./${progname} 260 >> ${logname} 2>&1
./${progname} 310 >> ${logname} 2>&1
./${progname} 330 >> ${logname} 2>&1
./${progname} 410 >> ${logname} 2>&1
./${progname} 420 >> ${logname} 2>&1
./${progname} 610 >> ${logname} 2>&1
./${progname} 810 >> ${logname} 2>&1
./${progname} 106 >> ${logname} 2>&1
./${progname} 103 >> ${logname} 2>&1
./${progname} 104 >> ${logname} 2>&1
./${progname} 300 >> ${logname} 2>&1
./${progname} 701 >> ${logname} 2>&1

