#!/bin/bash

if [ "$1" == "" ]; then
    echo "Usage: $0   start | stop | restart"
    exit
fi

. /etc/profile

homepath="/ap/home/coss/"
progname="time_redirect_k.php"
thismonth=`date '+%Y%m'`

cd "${homepath}/bin/isc"

logname="${homepath}/log/isc/time_redirect_k_${thismonth}.log"

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep ${progname} | grep "python"`
        if [ "$rfg" != "" ]; then
                pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
                if [ "${pids}" != "" ]; then
                        echo "${pids}" | while read pid
                        do
                                echo "shutdown the process ${pid}"
                                kill "${pid}"
                        done
                fi
        fi
fi

if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep "${progname}" | grep "python"`
        if [ "$rfg" != "" ]; then
                echo "`date` INFO : ${progname} is already running"
        else
                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start"
                /usr/bin/php ./${progname} >> ${logname} 2>&1
                #sleep 10
        fi
fi
