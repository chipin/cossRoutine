#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
import threading
import MySQLdb

localdb = ''
if localdb is not None:
   #localdb.close()
   localdb = None
localdb = MySQLdb.connect(host="172.16.13.151", user="root", passwd="Kbro654Tfm", db="ecnis")
localdbcur = localdb.cursor()
print localdbcur
if localdbcur is not None:
  print 'OK'
else:
  nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
  print '['+nowdate+']: Unable to connect to server [MYSQL]'
  time.sleep(60)

SQL = "select companyno,mac,ip,updatetime from COSS_FIXIP where companyno='220' limit 10";
localdbcur.execute(SQL)
results = localdbcur.fetchall()

for record in results:
  companyno = record[0]
  mac = record[1]
  ip  = record[2]
  update = record[3]

  print "%s,%s,%s" %(companyno,mac,ip)




