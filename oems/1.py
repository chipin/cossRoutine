#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

con = pymssql.connect(host='TFMCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
con2 = pymssql.connect(host='TFMCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')

cur = con.cursor()
cur2 = con2.cursor()


query = "select companyno from cdcompany"
print query
cur.execute(query)
while 1:
    curarr = cur.fetchmany(3)
    if curarr:
        xlen = len(curarr)
        print xlen
        for ii in range(0, xlen):
            companyno = curarr[ii][0]
            print companyno

            query2 = "select top 3 companyno,chargename from ms0040 with (nolock) where companyno='%s'" % (companyno)
            print query2
            cur2.execute(query2)
            xarr = cur2.fetchall()
            for ms_row in xarr:
                chargename = ms_row[1]
                print chargename

    else:
        break

p_subsid_arr = []
p_subsid_str = ''

con3 = pymssql.connect(host='TFMCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
cur3 = con3.cursor()

query3 = "select distinct A.companyno,A.subsid,A.servicename,B.nodeno,B.linkid from ms0200 A with (nolock) inner join ms0102 B with (nolock) on A.custid = B.custid and A.companyno=B.companyno where A.companyno='701' and substring(A.servicename,1,1) in ('2','3','9') and substring(A.custstatus,1,1) not in ('3','4','5') and len(A.singlesn) > 0 and B.addrno = 0 and B.nodeno='PY139' and B.linkid like 'PY139-31%'"
print query3
cur3.execute(query3);
qry3arr = cur3.fetchall()
for qry3row in qry3arr:
    p_subsid = str(qry3row[1])
    p_subsid_arr.append(p_subsid)

print p_subsid_arr

if p_subsid_arr is not None and len(p_subsid_arr) > 0:
    p_subsid_str = "','".join(p_subsid_arr)

print p_subsid_str
