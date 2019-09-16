#!/usr/bin/bash
. /opt/oracle/.profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/sms
sms_queue_noc="sms_queue_noc.py"

# sms_queue_noc
if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep ${sms_queue_noc} | grep "python"`
        if [ "$rfg" != "" ]; then
                pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
                if [ "${pids}" != "" ]; then
                        echo "${pids}" | while read pid
                        do
                                echo "`date '+%Y-%m-%d %H:%M:%S'` : ${sms_queue_noc} killed ${pid}"
                                kill "${pid}"
                        done
                fi
        fi
fi

if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep "${sms_queue_noc}" | grep "python"`
        if [ "$rfg" != "" ]; then
                echo "`date '+%Y-%m-%d %H:%M:%S'` : ${sms_queue_noc} is already running"
        else
                echo "`date '+%Y-%m-%d %H:%M:%S'` : ${sms_queue_noc} is running now"
                ./${sms_queue_noc} > /ap/home/coss/log/sms/sms_queue_noc.log 2>&1 &
        fi
fi
