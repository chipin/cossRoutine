#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/dta
progname="dta_pre_active_karen.php"

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep ${progname} | grep "php"`
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
        rfg=`ps -ef | grep "${progname}" | grep "/bin/php"`
        if [ "$rfg" != "" ]; then
                echo "`date` INFO : ${progname} is already running ${rfg} "
        else
                /usr/bin/php ./${progname} 310  > /ap/home/coss/log/dta/dta_pre_act_karen.log 2>&1
                
                
                
		
		
                echo "`date` INFO :started DTA pre-activation..."
        fi
fi




		
