#!/usr/bin/bash
. /ap/home/coss/.bash_profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/cti
progname="icare_ticket.py"

month=`date +%Y%m`
logfile="/ap/home/coss/log/cti/icare_ticket_${month}.log"

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
                echo "`date` INFO :started CTI010 ..."
                ./${progname} TFM >> ${logfile} 2>&1
        fi
fi
