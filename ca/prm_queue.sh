#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
    echo "Usage: $0   start | stop | restart"
    exit
fi

homepath="/ap/home/coss"
progname="prm_queue.py"
progname_seq="prm_send_queue.py"

#thismonth=`date '+%Y%m%d'`
sourceid=()
#thismonth=`date '+%Y%m'`
thismonth=`date '+%Y%m-%W'`
logname="${homepath}/log/ca/prm_5_${thismonth}.log"
logname_seq="${homepath}/log/ca/prm_17_${thismonth}.log"


cd "${homepath}/bin/ca"

# queue

#if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
#    rfg=`ps -ef | grep "${progname}" | grep "python"`
#    if [ "$rfg" != "" ]; then
#        pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
#        if [ "${pids}" != "" ]; then
#            echo "${pids}" | while read pid
#            do
#                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} stop #${pid}"
#                kill "${pid}"
#                sleep 3
#            done
#        fi
#    fi
#fi

#if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
#    rfg=`ps -ef | grep "${progname}" | grep "python"`
#    if [ "$rfg" != "" ]; then
#        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start #PASS"
#    else
#        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start"
#        ./${progname} >> ${logname} 2>&1 &
#        sleep 3
#    fi
#fi

#send_queue
if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep "${progname_seq}" | grep "python"`
    if [ "$rfg" != "" ]; then
        pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
        if [ "${pids}" != "" ]; then
            echo "${pids}" | while read pid
            do
                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname_seq} stop #${pid}"
                kill "${pid}"
                sleep 3
            done
        fi
    fi
fi

if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep "${progname_seq}" | grep "python"`
    if [ "$rfg" != "" ]; then
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname_seq} start #PASS"
    else
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname_seq} start"
        ./${progname_seq} >> ${logname_seq} 2>&1 &
        sleep 3
    fi
fi


