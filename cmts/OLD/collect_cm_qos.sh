#!/bin/bash

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

. /ap/home/coss/.bash_profile
cd /ap/home/coss/bin/cmts2

progname="collect_cm_qos.py"
logname="/ap/home/coss/log/cmts/collect_cm_qos.log"

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep "${progname}" | grep "python"`
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
                echo "`date` INFO : ${progname} is running now"
                ./${progname} > ${logname} 2>&1 &
        fi
fi
