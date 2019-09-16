#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
import cossdb,pymssql
from oraclass import ORA
from pysnmpclass import snmpclass

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

con = pymssql.connect(host='TFMCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')

cur = con.cursor()

so = []

query = "select companyno from cdcompany"
print query
cur.execute(query)
while 1:
    curarr = cur.fetchmany(3)
    if curarr:
        xlen = len(curarr)
        #print xlen
        for ii in range(0, xlen):
            companyno = curarr[ii][0]
            print companyno
            so.append(companyno)

    else:
        break

print so

if so is not None and len(so) > 0:
    so_str = "','".join(so)
    if so_str is not None and len(so_str) > 0:
        so_str = "'%s'" % (so_str)
        print so_str


so2 = []
so2.append('101')
so2_str = "','".join(so2)
print so2_str

agent = snmpclass(version='v1',ptimeout=3,pretries=3,debug=0)
rets = agent.snmpget(['10.222.251.11', '-c', 'NMS_Snmp', '.1.3.6.1.2.1.10.127.1.3.3.1.9.3948688'])
print rets
if rets is not None and rets[0][1]!='':
    online = int(rets[0][1])
else:
    online = -1
print online


p_online_cm = float(11)
p_total_cm = float(92)
print round(p_online_cm*100/p_total_cm,2)
print round(100-(p_online_cm*100/p_total_cm),2)
