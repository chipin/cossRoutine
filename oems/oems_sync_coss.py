#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv) != 2:
    print "Usage: %s [KBRO|CG|TFM]" % (sys.argv[0])
    sys.exit(0)
else:
    so = sys.argv[1].upper()

if so == 'KBRO':
    con = pymssql.connect(host='kbroCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
elif so == 'TFM':
    con = pymssql.connect(host='TFMCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
elif so == 'CG':
    con = pymssql.connect(host='CossMS_CG',user=cossdb.account,password=cossdb.passwd,database='cossdb_cg')
else:
    print "Usage: %s [KBRO|CG|TFM]" % (sys.argv[0])
    sys.exit(0)

try:
    cur = con.cursor()
except:
    print "Exception: Unable to connect CossMS [%s]" % (so)
    sys.exit(0)


origsid = {}

querysql = "select sid from ms03012 with (nolock) where createtime >= getdate()-30"
cur.execute(querysql)
loop = 0
while 1:
    curarr = cur.fetchmany(100)
    if curarr:
        xlen = len(curarr)
        for ii in range(0, xlen):
            try:
                sid = int(curarr[ii][0])
                origsid[sid] = loop
            except Exception, msg:
                print msg
            loop = loop+1
    else:
        break

oracon = ORA('OEMS@KBRO_NMSDB')
orasql = "SELECT a.sid,to_char(a.create_date,'yyyy/mm/dd hh24:mi:ss') create_date, to_char((case when a.status=5029 then a.status_date else a.close_date end),'yyyy/mm/dd hh24:mi:ss') close_date, b.descr status FROM oems_tickets_main a,oems_mapping b where a.status=b.id and (status_date>=sysdate-1)"
print orasql
rs = oracon.execall(orasql)
xlp = 0
if rs is not None and len(rs) > 0:
    for a_row in rs:
        sid = int(a_row[0])
        create_date = a_row[1]
        close_date = a_row[2]
        if close_date is None:
            close_date = ''
        status = a_row[3]
        if sid is None:
            continue
        try:
            loop = origsid[sid]
            inssql = "update ms03012 set finishtime='%s',status='%s' where sid=%d" % (close_date, status, sid)
            inssql2 = "insert into ms03012(sid,createtime,finishtime,status) values(%d,'%s','%s','%s')" % (sid, create_date, close_date, status)
        except Exception, msg:
            #print str(msg)
            inssql = "insert into ms03012(sid,createtime,finishtime,status) values(%d,'%s','%s','%s')" % (sid, create_date, close_date, status)
            inssql2 = "update ms03012 set finishtime='%s',status='%s' where sid=%d" % (close_date, status, sid)
        print inssql
        try:
            cur.execute(inssql)
        except Exception, msg:
            print 'ERROR:',str(msg)
            print inssql2
            try:
                cur.execute(inssql2)
            except Exception, msg:
                print 'ERROR:',str(msg)
        xlp = xlp+1
        if (xlp%30)==0:
            con.commit()
    con.commit()

if oracon is not None:
    oracon.se_close()
con.close()
