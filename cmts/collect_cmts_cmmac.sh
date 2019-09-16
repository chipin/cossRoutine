#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/cmts
progname="collect_cmts_cmmac.py"

lognamet1="/ap/home/coss/log/cmts/collect_cmts_cmmac_TFM1.log"
lognamet2="/ap/home/coss/log/cmts/collect_cmts_cmmac_TFM2.log"
lognamek1="/ap/home/coss/log/cmts/collect_cmts_cmmac_KBRO1.log"
lognamek2="/ap/home/coss/log/cmts/collect_cmts_cmmac_KBRO2.log"
lognamek3="/ap/home/coss/log/cmts/collect_cmts_cmmac_KBRO3.log"
lognamek4="/ap/home/coss/log/cmts/collect_cmts_cmmac_KBRO4.log"

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
                ./${progname} TFM1 > ${lognamet1} 2>&1 &
                ./${progname} TFM2 > ${lognamet2} 2>&1 &
                ./${progname} KBRO1 > ${lognamek1} 2>&1 &
                ./${progname} KBRO2 > ${lognamek2} 2>&1 &
                ./${progname} KBRO3 > ${lognamek3} 2>&1 &
                ./${progname} KBRO4 > ${lognamek4} 2>&1 &
        fi
fi
