#!/bin/bash
. /etc/profile

cd /ap/home/coss/bin/isc/
/usr/bin/php ./fixip_check_status.php > /ap/home/coss/log/isc/fixip_check_status.log
