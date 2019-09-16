#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/cmts
progname="collect_cmts_cmactive.py"

logname1="/ap/home/coss/log/cmts/collect_cmts_cmactive_TFM.log"
logname2="/ap/home/coss/log/cmts/collect_cmts_cmactive_KBRO1.log"
logname3="/ap/home/coss/log/cmts/collect_cmts_cmactive_KBRO2.log"

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
                ./${progname} TFM > ${logname1} 2>&1 &
                ./${progname} KBRO1 > ${logname2} 2>&1 &
                ./${progname} KBRO2 > ${logname3} 2>&1 &
        fi
fi
