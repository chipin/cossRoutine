#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
    echo "Usage: $0   start | stop | restart"
    exit
fi

homepath="/ap/home/coss"
progname="ca_queue_K.py"

#thismonth=`date '+%Y%m%d'`
sourceid=(16)

cd "${homepath}/bin/ca"
for sid in ${sourceid[@]}; do
    #logname="${homepath}/log/ca/ca_${sid}_${thismonth}.log"
    logname="${homepath}/log/ca/ca_${sid}.log"

    if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep -e "${progname} ${sid}$" | grep "python"`
        if [ "$rfg" != "" ]; then
            pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
            if [ "${pids}" != "" ]; then
                echo "${pids}" | while read pid
                do
                    echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${sid} stop #${pid}"
                    kill "${pid}"
                    sleep 3
                done
            fi
        fi
    fi

    if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep -e "${progname} ${sid}$" | grep "python"`
        if [ "$rfg" != "" ]; then
            echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${sid} start #PASS"
        else
            echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${sid} start"
            ./${progname} ${sid} >> ${logname} 2>&1 &
            sleep 3
        fi
    fi
done