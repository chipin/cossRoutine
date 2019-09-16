#!/bin/bash
. /etc/profile

# python curl2ncc.py
thismonth=`date '+%Y%m%d'`
homepath="/ap/home/coss"
progname="curl2ncc.py"
logname="${homepath}/log/cnr/ncc/curl2ncc_${thismonth}.log"

cd "${homepath}/bin/cnr/ncc"
./${progname} >> ${logname} 2>&1 &