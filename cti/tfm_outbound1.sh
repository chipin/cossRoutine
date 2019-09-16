#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
    echo "Usage: $0 [start | stop | restart]"
    exit
fi

cd /ap/home/coss/bin/cti

progname="tfm_outbound1.php"
m1=`date +%Y%m%d`
logfile="/ap/home/coss/log/cti/tfm_outbound1_${m1}.log"

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep ${progname} | grep -v "grep"`
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
    rfg=`ps -ef | grep ${progname} | grep -v "grep"`
    if [ "$rfg" != "" ]; then
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start #PASS"
    else
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start"
        /usr/bin/php ./${progname} >> ${logfile} 2>&1 &
    fi
fi
