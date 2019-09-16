#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/cmts
progname="collect_cm111.py"

lognamet1="/ap/home/coss/log/cmts/collect_collect_cm111_TFM.log"
lognamet2="/ap/home/coss/log/cmts/collect_collect_cm111_KBRO1.log"
lognamet3="/ap/home/coss/log/cmts/collect_collect_cm111_KBRO2.log"
lognamet4="/ap/home/coss/log/cmts/collect_collect_cm111_CG.log"


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
                ./${progname} 103 > ${lognamet1} 2>&1 &
                ./${progname} 104 > ${lognamet1} 2>&1 &
                ./${progname} 300 > ${lognamek1} 2>&1 &
                ./${progname} 701 > ${lognamet1} 2>&1 &
                ./${progname} 210 > ${lognamet2} 2>&1 &
                ./${progname} 220 > ${lognamet2} 2>&1 &
                ./${progname} 230 > ${lognamet2} 2>&1 &
                ./${progname} 240 > ${lognamet2} 2>&1 &
                ./${progname} 250 > ${lognamet2} 2>&1 &
                ./${progname} 260 > ${lognamet2} 2>&1 &
                ./${progname} 310 > ${lognamet3} 2>&1 &
                ./${progname} 330 > ${lognamet3} 2>&1 &
                ./${progname} 410 > ${lognamet3} 2>&1 &
                ./${progname} 420 > ${lognamet3} 2>&1 &
                ./${progname} 610 > ${lognamet3} 2>&1 &
                ./${progname} 810 > ${lognamet3} 2>&1 &
                ./${progname} 820 > ${lognamet3} 2>&1 &
                ./${progname} 106 > ${lognamet4} 2>&1 &
        fi
fi
