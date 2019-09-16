#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
    echo "Usage: $0   start | stop | restart"
    exit
fi

homepath="/ap/home/coss"
progname="invoice_sync.py"
thismonth=`date '+%Y%m'`
CompanyNo=(101 103 104 300 701 210 220 230 240 250 260 106 310 330 410 420 610 810 820)

cd "${homepath}/bin/invoice"
for so in ${CompanyNo[@]}; do
    logname="${homepath}/log/invoice/invoice_sync_${so}_${thismonth}.log"

    if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep "${progname} ${so}" | grep "python"`
        if [ "$rfg" != "" ]; then
            pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
            if [ "${pids}" != "" ]; then
                echo "${pids}" | while read pid
                do
                    echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} stop #${pid}"
                    kill "${pid}"
                done
            fi
        fi
    fi

    if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep "${progname} ${so}" | grep "python"`
        if [ "$rfg" != "" ]; then
            echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} start #PASS"
        else
            echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} start"
            ./${progname} ${so} >> ${logname} 2>&1
            sleep 1
        fi
    fi

done
