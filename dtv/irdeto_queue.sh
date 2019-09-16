#!/usr/bin/bash
. /ap/home/coss/.bash_profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/dtv
progname_ppv="irdeto_queue.py"

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep ${progname_ppv} | grep "python"`
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
        rfg=`ps -ef | grep "${progname_ppv}" | grep "python"`
        if [ "$rfg" != "" ]; then
                echo "`date` INFO : irdeto_queue.py is already running"
        else
                ./${progname_ppv} > /ap/home/coss/log/dtv/irdeto_queue.log 2>&1 &
                ./${progname_ppv} 106 > /ap/home/coss/log/dtv/irdeto_queue_106.log 2>&1 &
                ./${progname_ppv} 101 > /ap/home/coss/log/dtv/irdeto_queue_101.log 2>&1 &
                ./${progname_ppv} 103 > /ap/home/coss/log/dtv/irdeto_queue_103.log 2>&1 &
                ./${progname_ppv} 104 > /ap/home/coss/log/dtv/irdeto_queue_104.log 2>&1 &
                ./${progname_ppv} 300 > /ap/home/coss/log/dtv/irdeto_queue_300.log 2>&1 &
                ./${progname_ppv} 701 > /ap/home/coss/log/dtv/irdeto_queue_701.log 2>&1 &
                #./irdeto_queue1.py > /ap/home/coss/log/dtv/irdeto_queue_lab.log 2>&1 &
                echo "`date` INFO :started CA gateway sending queue sequential..."
        fi
fi
