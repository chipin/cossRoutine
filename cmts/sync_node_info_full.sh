#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/cmts
progname="sync_node_info_coss.py"
logname="/ap/home/coss/log/cmts/sync_node_info_full.log"

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
                ./${progname} 101 full > ${logname}
                ./${progname} 103 full >> ${logname}
                ./${progname} 104 full >> ${logname}
                ./${progname} 300 full >> ${logname}
                ./${progname} 701 full >> ${logname}
                ./${progname} 106 full >> ${logname}
                ./${progname} 210 full >> ${logname}
                ./${progname} 220 full >> ${logname}
                ./${progname} 230 full >> ${logname}
                ./${progname} 240 full >> ${logname}
                ./${progname} 250 full >> ${logname}
                ./${progname} 260 full >> ${logname}
                ./${progname} 310 full >> ${logname}
                ./${progname} 330 full >> ${logname}
                ./${progname} 410 full >> ${logname}
                ./${progname} 420 full >> ${logname}
                ./${progname} 610 full >> ${logname}
                ./${progname} 810 full >> ${logname}
                ./${progname} 820 full >> ${logname}
        fi
fi
