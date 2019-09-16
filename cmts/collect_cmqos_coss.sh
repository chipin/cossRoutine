#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/cmts

progname="collect_cmqos_coss.py"

#today=`date '+%Y%m%d'`
today=`date '+%Y%m'`
logname1="/ap/home/coss/log/cmts/collect_cmqos_coss_TFM_${today}.log"
logname2="/ap/home/coss/log/cmts/collect_cmqos_coss_KBRO_${today}.log"
logname3="/ap/home/coss/log/cmts/collect_cmqos_coss_CG_${today}.log"

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
                ./${progname} KBRO > ${logname2} 2>&1 &
                ./${progname} CG > ${logname3} 2>&1 &
        fi
fi
