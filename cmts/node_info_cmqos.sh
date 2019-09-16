#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/cmts
progname="node_info_cmqos.py"
logname="/ap/home/coss/log/cmts/node_info_cmqos.log"

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
                ./${progname} 101 > ${logname}
                ./${progname} 103 >> ${logname}
                ./${progname} 104 >> ${logname}
                ./${progname} 300 >> ${logname}
                ./${progname} 701 >> ${logname}
                ./${progname} 106 >> ${logname}
                ./${progname} 210 >> ${logname}
                ./${progname} 220 >> ${logname}
                ./${progname} 230 >> ${logname}
                ./${progname} 240 >> ${logname}
                ./${progname} 250 >> ${logname}
                ./${progname} 260 >> ${logname}
                ./${progname} 310 >> ${logname}
                ./${progname} 330 >> ${logname}
                ./${progname} 410 >> ${logname}
                ./${progname} 420 >> ${logname}
                ./${progname} 610 >> ${logname}
                ./${progname} 810 >> ${logname}
                ./${progname} 820 >> ${logname}
        fi
fi
