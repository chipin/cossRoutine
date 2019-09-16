#!/bin/bash
. /etc/profile

if [ "$1" == "" ]; then
        echo "Usage: $0   start | stop | restart"
        exit
fi

cd /ap/home/coss/bin/invoice
progname="tfm_invoice_status.py"

if [ "$1" == "stop" ] || [ "$1" == "restart" ]; then
        rfg=`ps -ef | grep "SYNCDATA" | grep "python"`
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
        rfg=`ps -ef | grep "SYNCDATA" | grep "python"`
        if [ "$rfg" != "" ]; then
                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start #PASS"
        else
                echo "`date '+%Y-%m-%d %H:%M:%S'`: ${progname} start"
                ./${progname} 101 SYNCDATA > /ap/home/coss/log/invoice/tfm_invoice_sync_101.log 2>&1
                ./${progname} 103 SYNCDATA > /ap/home/coss/log/invoice/tfm_invoice_sync_103.log 2>&1
                ./${progname} 104 SYNCDATA > /ap/home/coss/log/invoice/tfm_invoice_sync_104.log 2>&1
                ./${progname} 300 SYNCDATA > /ap/home/coss/log/invoice/tfm_invoice_sync_300.log 2>&1
                ./${progname} 701 SYNCDATA > /ap/home/coss/log/invoice/tfm_invoice_sync_701.log 2>&1
        fi
fi
