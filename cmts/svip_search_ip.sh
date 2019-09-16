#!/bin/bash
cd /ap/home/coss/bin/cmts
thismonth=`date '+%Y%m'`
logname="/ap/home/coss/log/cmts/svip_search_ip_${thismonth}.log"
./svip_search_ip.py SVIP>> ${logname}