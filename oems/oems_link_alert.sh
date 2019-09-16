#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
    echo "Usage: $0   start | stop | restart"
    exit
fi

homepath="/ap/home/coss"
progname="oems_link_alert.py"
thismonth=`date '+%Y%m'`

logname1="${homepath}/log/oems/oems_link_alert_TFM_${thismonth}.log"
logname2="${homepath}/log/oems/oems_link_alert_KBRO_${thismonth}.log"
logname3="${homepath}/log/oems/oems_link_alert_CG_${thismonth}.log"

cd "${homepath}/bin/oems"

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
        ./${progname} TFM >> ${logname1}
        ./${progname} KBRO >> ${logname2}
        ./${progname} CG >> ${logname3}
    fi
fi
