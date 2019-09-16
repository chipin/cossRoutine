#!/bin/bash

if [ "$1" == "" ] || [ "$2" == "" ]; then
    echo "Usage: $0 CompanyNo CMMAC"
    exit
fi

. /ap/home/coss/.bash_profile

cd /ap/home/coss/bin/cmts2

./cm_measure.py $1 $2
