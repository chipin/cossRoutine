#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/coss
progname="churn_raw.py"

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep ${progname} | grep "python"`
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
                ./${progname} 210 > /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 220 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 230 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 240 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 250 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 260 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 106 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 310 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 330 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 410 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 420 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 610 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 810 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 820 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 101 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 103 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 104 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 300 >> /ap/home/coss/log/coss/churn_check.log 2>&1
                ./${progname} 701 >> /ap/home/coss/log/coss/churn_check.log 2>&1
        fi
fi
