#!/bin/bash


if [ "$1" == "" ]; then
    echo "Usage: $0   start | stop | restart"
    exit
fi
. /etc/profile

homepath="/ap/home/coss/"
progname="time_check_status_k.php"
thismonth=`date '+%Y%m%d'`

CompanyNo=(210 220 230 240 250 260 310 330 410 420 610 810 820 106 101 103 104 300 701)
#CompanyNo=(210)

cd "${homepath}/bin/isc"

for so in ${CompanyNo[@]}; do
	#logname="${homepath}/log/isc/time_check_status_${thismonth}.log"
	logname="${homepath}/log/isc/time_check_status_k_${thismonth}.log"
	
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
	        rfg=`ps -ef | grep "${progname}" | grep "python"`
	        if [ "$rfg" != "" ]; then
	                echo "`date` INFO : ${progname} is already running"
	        else
	                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start"
	                /usr/bin/php ./${progname} ${so} >> ${logname} 2>&1
	                #sleep 10
	        fi
	fi
done