#!/bin/bash
. /etc/profile

homepath="/ap/home/coss"
progname="sms_2ways_expired3.py"
thismonth=`date '+%Y%m'`
logname="${homepath}/log/sms/sms_2ways_expired3_${thismonth}.log"

cd "${homepath}/bin/sms"
./${progname} >> ${logname} 2>&1 &