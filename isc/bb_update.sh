#!/bin/bash
. /etc/profile

cd /ap/home/coss/bin/isc/
/usr/bin/php ./bb_update.php > /ap/home/coss/log/isc/bb_update.log
