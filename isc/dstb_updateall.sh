#!/usr/bin/bash
. /ap/home/coss/.bash_profile

cd /ap/home/coss/log/isc
/usr/local/bin/php ./dstb_updateall.php > ./dstb_updateall.log
