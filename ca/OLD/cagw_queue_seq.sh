#!/usr/bin/bash
. /opt/oracle/.profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /export/home/coss/bin/cagw
progname="cagw_queue_seq.py"

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
                echo "`date` INFO : cagw_queue_seq.py is already running"
        else
                ./${progname} > /export/home/coss/log/dtv/cagw_queue_16.log 2>&1 &
                echo "`date` INFO :started CA gateway sequencial IRD..."
        fi
fi

