#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
    echo "Usage: $0   start | stop | restart"
    exit
fi

homepath="/ap/home/coss"
progname="ping_svip_cm.py"
thismonth=`date '+%Y%m'`
#thismonth=`date '+%Y%m%d'`


cd "${homepath}/bin/oems"

logname="${homepath}/log/oems/ping_svip_cm_${thismonth}.log"

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
    ./${progname} >> ${logname} 2>&1 &
  fi
fi


