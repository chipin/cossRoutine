#!/bin/bash
. /ap/home/coss/.bash_profile

cd /ap/home/coss/bin/oems

progname="oems_node_alert.py"
logname="/ap/home/coss/log/oems_node_alert.log"

rfg=`ps -ef | grep "${progname}" | grep "python"`
if [ "$rfg" != "" ]; then
    echo "`date` INFO : ${progname} is already running"
else
    ./${progname} >> ${logname}
fi
