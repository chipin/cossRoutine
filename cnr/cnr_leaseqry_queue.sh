#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi
#./cnr_leaseqry_queue.sh start
#ps -ef |grep 'cnr_leaseqry_queue'
progname="cnr_leaseqry_queue.py"
thismonth=`date '+%Y%m'`
CompanyNo=(EJ0_CPNR_001 GS0_CCNR_001 MD1_CCNR_001 UI0_CCNR_001 PL0_CCNR_001 CG_CNR1_001 YMS_CPNR_001 NTP_CPNR_001 KP_CPNR_001 DA_CNR1_001 WS_CNR1_001 UC_CPNR_001 TC_CNR1_001 CT_CNR1_001 NTY_CNR1_001 FM_CNR1_001 FM-HL_CNR1_001 NCC_CNR1_001 NT_CNR1_001 KS_CNR1_001 PN_CNR1_001)

cd /ap/home/coss/bin/cnr
for so in ${CompanyNo[@]}; do
    logname="/ap/home/coss/log/cnr/${so}_cnr_leaseqry_queue_${thismonth}.log"

    if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep "${progname} ${so}" | grep "python"`
        if [ "$rfg" != "" ]; then
            pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
            if [ "${pids}" != "" ]; then
                echo "${pids}" | while read pid
                do
                    echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} stop #${pid}"
                    kill "${pid}"
                done
            fi
        fi
    fi

    if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep "${progname} ${so}" | grep "python"`
        if [ "$rfg" != "" ]; then
            echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} start #PASS"
        else
            echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} start"
            ./${progname} ${so} >> ${logname} 2>&1 &
            sleep 1
        fi
    fi
done