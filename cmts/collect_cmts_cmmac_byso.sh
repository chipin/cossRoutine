#!/bin/bash
. /etc/profile

if ["$1" == ""]; then
        echo "Usage: $0   start|stop|restart	companyno"
        exit
fi

cd /ap/home/coss/bin/cmts
progname="collect_cmts_cmmac_byso.py"

lognamet1="/ap/home/coss/log/cmts/collect_cmts_cmmac_byso.log"

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
                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start $2 #PASS"
        else
                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start $2 "
                ./${progname} "$2" > ${lognamet1} 2>&1 &
        fi
fi
