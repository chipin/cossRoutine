#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
    echo "Usage: $0   start | stop | restart"
    exit
fi

. /ap/home/coss/.bash_profile

homepath="/ap/home/coss"
progname="oems_check_status.py"
thismonth=`date '+%Y%m'`

logname="${homepath}/log/oems/oems_check_status_${thismonth}.log"

cd "${homepath}/bin/oems"

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep "${progname}" | grep "python"`
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
        ./${progname} >> ${logname}
    fi
fi
