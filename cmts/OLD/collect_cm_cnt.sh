#!/bin/bash
. /etc/oracle.sh

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /export/home/coss/bin/cmts
progname="collect_cm_cnt.py"

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep ${progname} | grep "python"`
        if [ "$rfg" != "" ]; then
                pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
                if [ "${pids}" != "" ]; then
                        echo "${pids}" | while read pid
                        do
                                echo "shutdown the process ${pid}"
                                kill "${pid}"
                        done
                fi
        fi
fi

if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep "${progname}" | grep "python"`
        if [ "$rfg" != "" ]; then
                echo "`date` INFO : collect_cm_cnt is already running"
        else
                ./${progname} 101 > /export/home/coss/log/collect_cm_cnt_101.log 2>&1 &
                ./${progname} 103 > /export/home/coss/log/collect_cm_cnt_103.log 2>&1 &
                ./${progname} 104 > /export/home/coss/log/collect_cm_cnt_104.log 2>&1 &
                ./${progname} 300 > /export/home/coss/log/collect_cm_cnt_300.log 2>&1 &
                ./${progname} 701 > /export/home/coss/log/collect_cm_cnt_701.log 2>&1 &
                echo "`date` INFO :started CMTS CM CNT SNMP polling..."
        fi
fi

