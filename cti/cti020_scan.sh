#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
    echo "Usage: $0   start | stop | restart"
    exit
fi

cd /ap/home/coss/bin/cti
progname="cti020_scan.py"

today=`date +%Y%m%d`
logfileK="/ap/home/coss/log/cti/cti020_scan_K_${today}.log"
logfileT="/ap/home/coss/log/cti/cti020_scan_T_${today}.log"
logfileC="/ap/home/coss/log/cti/cti020_scan_C_${today}.log"

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep ${progname} | grep "python"`
    if [ "$rfg" != "" ]; then
        pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
        if [ "${pids}" != "" ]; then
            echo "${pids}" | while read pid
            do
                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} stop #${pid}"
                kill "${pid}"
            done
        fi
    fi
fi

if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep "${progname}" | grep "python"`
    if [ "$rfg" != "" ]; then
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start #PASS"
    else
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start"
        ./${progname} KBRO >> ${logfileK} 2>&1 &
        ./${progname} TFM >> ${logfileT} 2>&1 &
        ./${progname} CG >> ${logfileC} 2>&1 &
    fi
fi
