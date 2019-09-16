#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
    echo "Usage: $0   start | stop | restart"
    exit
fi

homepath="/ap/home/coss"
progname1="sms_queue.py"
progname2="sms_queue_invoice.py"
thismonth=`date '+%Y%m'`
logname1="${homepath}/log/sms/sms_queue_${thismonth}.log"
logname2="${homepath}/log/sms/sms_queue_invoice_${thismonth}.log"

cd "${homepath}/bin/sms"

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep "${progname1}" | grep "python"`
    if [ "$rfg" != "" ]; then
        pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
        if [ "${pids}" != "" ]; then
            echo "${pids}" | while read pid
            do
                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname1} stop #${pid}"
                kill "${pid}"
            done
        fi
    fi
fi

if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep "${progname1}" | grep "python"`
    if [ "$rfg" != "" ]; then
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname1} start #PASS"
    else
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname1} start"
        ./${progname1} >> ${logname1} 2>&1 &
    fi
fi

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep "${progname2}" | grep "python"`
    if [ "$rfg" != "" ]; then
        pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
        if [ "${pids}" != "" ]; then
            echo "${pids}" | while read pid
            do
                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname2} stop #${pid}"
                kill "${pid}"
            done
        fi
    fi
fi

if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep "${progname2}" | grep "python"`
    if [ "$rfg" != "" ]; then
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname2} start #PASS"
    else
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname2} start"
        ./${progname2} >> ${logname2} 2>&1 &
    fi
fi
