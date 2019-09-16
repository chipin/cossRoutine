#!/bin/bash
. /etc/profile

cd /ap/home/coss/bin/isc
/usr/bin/php ./dstb_updateinfo.php > /ap/home/coss/log/isc/dstb_updateinfo.log
