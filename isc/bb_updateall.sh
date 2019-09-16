#!/usr/bin/bash
. /ap/home/coss/.bash_profile

cd /ap/home/coss/bin/isc/
/usr/local/bin/php ./bb_updateall.php > /ap/home/coss/log/isc/bb_updateall.log
