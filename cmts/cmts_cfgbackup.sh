#!/bin/bash
. /opt/oracle/.profile
BIN="/export/home/swallow/bin"
${BIN}/cmts_cfgbackup.py > ${BIN}/cmts_cfgbackup.log
