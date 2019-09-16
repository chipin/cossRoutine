#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

# python cnr_cmd_fixedip.py CT_CNR1_001 master fixedip
# python cnr_cmd_fixedip.py CT_CNR1_001 slave  fixedip
homepath="/ap/home/coss"
progname="cnr_cmd_fixedip.py"
thismonth=`date '+%Y%m%d'`
CompanyNo=(GS0_CCNR_001 MD1_CCNR_001 UI0_CCNR_001 PL0_CCNR_001 DA_CNR1_001 WS_CNR1_001 TC_CNR1_001 CG_CNR1_001 CT_CNR1_001 NTY_CNR1_001 FM_CNR1_001 NCC_CNR1_001 NT_CNR1_001 KS_CNR1_001 FM-HL_CNR1_001)

cd "${homepath}/bin/cnr"
for so in ${CompanyNo[@]}; do
    logname1="${homepath}/log/cnr/new/${so}_cnr_cmd_fixedip_master_${thismonth}.log"
    logname2="${homepath}/log/cnr/new/${so}_cnr_cmd_fixedip_slave_${thismonth}.log"

    if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        # master fixedip
        rfg=`ps -ef | grep "${progname} ${so} master fixedip" | grep "python"`
        if [ "$rfg" != "" ]; then
            pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
            if [ "${pids}" != "" ]; then
                echo "${pids}" | while read pid
                do
                    echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} master fixedip stop #${pid}"
                    kill "${pid}"
                done
            fi
        fi
        # slave fixedip
        rfg=`ps -ef | grep "${progname} ${so} slave fixedip" | grep "python"`
        if [ "$rfg" != "" ]; then
            pids=`echo "${rfg}" | awk -F" " '{ print $2 }'`
            if [ "${pids}" != "" ]; then
                echo "${pids}" | while read pid
                do
                    echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} slave fixedip stop #${pid}"
                    kill "${pid}"
                done
            fi
        fi
    fi

    if [ "$1" == "start" ] || [ "$1" == "restart" ]; then
        # master fixedip
        rfg=`ps -ef | grep "${progname} ${so} master fixedip" | grep "python"`
        if [ "$rfg" != "" ]; then
            echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} master fixedip start #PASS"
        else
            echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} master fixedip start"
            ./${progname} ${so} master fixedip >> ${logname1} 2>&1 &
            sleep 1
        fi
        # slave fixedip
        rfg=`ps -ef | grep "${progname} ${so} slave fixedip" | grep "python"`
        if [ "$rfg" != "" ]; then
            echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} slave fixedip start #PASS"
        else
            echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} ${so} slave fixedip start"
            ./${progname} ${so} slave fixedip >> ${logname2} 2>&1 &
            sleep 1
        fi
    fi

done
