#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
import threading
import MySQLdb
from oraclass import ORA
from pysnmpclass import snmpclass

os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'


if len(sys.argv)!=2:
    print 'Error: Argument error'
    sys.exit(0)
    
companyno = sys.argv[1]

print companyno
    
ora = ORA('nms@cnis')

if not ora.db:
    sys.exit(0)
    
try:
  localdb = MySQLdb.connect(host="123.193.108.12", user="kbrocmwifi", passwd="kbronagios", db="kbrocmwifi")
  localdbcur = localdb.cursor()
except Exception, msg:
  print msg
  nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
  print '['+nowdate+']: Unable to connect to server [MYSQL]'
  sys.exit(0)

cmmac_arr = {}

qrysql = "select companyno,ip,subsid,to_char(updatetime,'YYYY/MM/DD HH24:MI:SS') updatetime  from cmmac where swversion is not null and servicename = '2 CM'  and (swversion like '%%CDE%%' or swversion like '%%CCR%%') and swversion like '%%仲琦%%' and  subsid is not null  and companyno = '%s'" % (companyno)
print qrysql
rs1 = ora.execall(qrysql)
if rs1 is not None and len(rs1)>0:
  for aw in rs1:
    so = (int)(aw[0])
    ip = aw[1]
    subsid = (int)(aw[2])
    updatetime = aw[3]
    upd_sql = "replace into CM_WiFi_List (companyno,subsid,ip,updatetime) values (%d, %d,'%s','%s')" % (so,subsid,ip,updatetime)
    #print upd_sql
    try:
      localdbcur.execute(upd_sql)
      #pass
    except Exception, msg:
      nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
      print 'Exception: ['+nowdate+']'+str(msg)
      result = -1
      
if localdb is not None:
    localdb.close()
if ora is not None:
    ora.se_close()
sys.exit(0)
