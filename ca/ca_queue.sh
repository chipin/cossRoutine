#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
    echo "Usage: $0   start | stop | restart"
    exit
fi

homepath="/ap/home/coss"
progname="ca_queue.py"
progname_seq="ca_queue_seq.py"
progname_icc="ca_sync_icc.py"
#thismonth=`date '+%Y%m%d'`
sourceid=(5 6 7 8 9 10 11 12 13 14 15)

logname_seq="${homepath}/log/ca/ca_19.log"
logname_icc="${homepath}/log/ca/ca_20.log"

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

# SEQ
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

# DTA create ICCNO
if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep "${progname_icc}" | grep "python"`
    if [ "$rfg" != "" ]; then
        pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
        if [ "${pids}" != "" ]; then
            echo "${pids}" | while read pid
            do
                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname_icc} stop #${pid}"
                kill "${pid}"
                sleep 3
            done
        fi
    fi
fi

if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
    rfg=`ps -ef | grep "${progname_icc}" | grep "python"`
    if [ "$rfg" != "" ]; then
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname_icc} start #PASS"
    else
        echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname_icc} start"
        ./${progname_icc} >> ${logname_icc} 2>&1 &
        sleep 3
    fi
fi
