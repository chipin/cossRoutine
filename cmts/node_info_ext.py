#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv)!=2:
    print 'Error: Argument error'
    sys.exit(0)

so = sys.argv[1]

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print '['+nowdate+'] START'

try:
    if so=='106':
        con = pymssql.connect(host='CossMS_CG',user=cossdb.account,password=cossdb.passwd,database='cossdb_cg')
    elif so in ['101','103','104','300','701']:
        con = pymssql.connect(host='TFMCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')
    else:
        con = pymssql.connect(host='kbroCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')
    cur = con.cursor()
except Exception, errmesg:
    print 'Error:',errmesg
    sys.exit(0)

oracon_upd = ORA('nms@cnis')
if not oracon_upd.db:
    sys.exit(0)

oracon_nmscm = ORA('nms_cm@kbro_nmsdb')
if not oracon_nmscm.db:
    sys.exit(0)

oracon_oems = ORA('oems@kbro_nmsdb')
if not oracon_oems.db:
    sys.exit(0)

oraupdsql = "update node_info set coss_catv=0,coss_bb=0,cti_catv=0,cti_bb=0,qty_churn=0,oems_plan=0,oems_burst=0 where companyno='%s'" % (so)
print oraupdsql
try:
    oracon_upd.execone(oraupdsql)
    oracon_upd.commit()
except Exception, detail:
    print '%s,%s -> %s' % (companyno, nodeno, detail)

###  COSS Dispatching ticket
querysql = "select a.companyno,a.nodeno,c.servicename,count(distinct c.worksheet) cnt from ms0102 a with (nolock),ms0300 b with (nolock),ms0301 c with (nolock) where a.companyno='%s' and a.nodeno is not null and a.nodeno<>'' and a.companyno=b.companyno and a.custid=b.custid and substring(b.workkind,1,1) in ('5') and a.nodeno<>'未設' and b.companyno=c.companyno and b.worksheet=c.worksheet and b.createtime>=getdate()-8 group by a.companyno,a.nodeno,c.servicename" % (so)
tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s]" % (tme)
print querysql
cur.execute(querysql)
node_arr = {}
i = 0
while 1:
    curarr = cur.fetchmany(100)
    i = i+1
    if curarr:
        xlen = len(curarr)
        for ii in range(0, xlen):
            companyno = curarr[ii][0]
            nodeno = curarr[ii][1]
            servicename = curarr[ii][2]
            cnt = curarr[ii][3]
            print companyno,nodeno,servicename,cnt
            oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','%s','%d','COSS'); end;" % (companyno, nodeno, servicename, cnt)
            print oraupdsql
            try:
                oracon_upd.execone(oraupdsql)
                oracon_upd.commit()
            except Exception, detail:
                print '%s,%s -> %s' % (companyno, nodeno, detail)
    else:
        break
#oracon_upd.commit()

###  CTI call
if so not in ['101','103','104','300','701']:
    oraqrysql = "select so,node,servicename,count(cti_ID) from cti.V_CTI_TICKET_FAULT where calldate between to_char(sysdate-7,'yyyymmdd') and to_char(sysdate-1,'yyyymmdd') and so='%s' and node is not null group by so,node,servicename" % (so)
    tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print "[%s]" % (tme)
    print oraqrysql
    rs = oracon_nmscm.execall(oraqrysql)
    if rs != None and len(rs) > 0:
        for a_row in rs:
            companyno = a_row[0]
            nodeno = a_row[1]
            servicename = a_row[2]
            cnt = int(a_row[3])
            print companyno,nodeno,servicename,cnt
            oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','%s','%d','CTI'); end;" % (companyno, nodeno, servicename, cnt)
            print oraupdsql
            try:
                oracon_upd.execone(oraupdsql)
                oracon_upd.commit()
            except Exception, detail:
                print '%s,%s -> %s' % (companyno, nodeno, detail)
    #oracon_upd.commit()

###  COSS churn
querysql = "select a.companyno,a.nodeno,c.servicename,count(distinct c.worksheet) cnt from ms0102 a with (nolock),ms0300 b with (nolock),ms0301 c with (nolock) where a.companyno='%s' and a.nodeno is not null and a.nodeno<>'' and a.companyno=b.companyno and a.custid=b.custid and substring(b.workkind,1,1) in ('3') and a.nodeno<>'未設' and b.companyno=c.companyno and b.worksheet=c.worksheet and b.finishdate>=getdate()-8 and c.backcause in ('163 連線慢','162 常斷線','178 遊戲速度太慢') group by a.companyno,a.nodeno,c.servicename" % (so)
tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s]" % (tme)
print querysql
cur.execute(querysql)
node_arr = {}
i = 0
while 1:
    curarr = cur.fetchmany(100)
    i = i+1
    if curarr:
        xlen = len(curarr)
        for ii in range(0, xlen):
            companyno = curarr[ii][0]
            nodeno = curarr[ii][1]
            servicename = curarr[ii][2]
            cnt = curarr[ii][3]
            print companyno,nodeno,servicename,cnt
            oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','%s','%d','CHURN'); end;" % (companyno, nodeno, servicename, cnt)
            print oraupdsql
            try:
                oracon_upd.execone(oraupdsql)
                oracon_upd.commit()
            except Exception, detail:
                print '%s,%s -> %s' % (companyno, nodeno, detail)
    else:
        break
#oracon_upd.commit()

###  OEMS tickets
oraqrysql = "select so,node,normal_flag,count(sid) cnt from v_impact_ticket_info where to_char(close_date,'yyyymmdd') between to_char(sysdate-31,'yyyymmdd') and to_char(sysdate-1,'yyyymmdd') and so='%s' and node is not null group by so,node,normal_flag" % (so)
tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s]" % (tme)
print oraqrysql
rs = oracon_oems.execall(oraqrysql)
if rs != None and len(rs) > 0:
    for a_row in rs:
        companyno = a_row[0]
        nodeno = a_row[1]
        normal_flag = a_row[2]
        cnt = int(a_row[3])
        print companyno,nodeno,normal_flag,cnt
        oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','%s','%d','OEMS'); end;" % (companyno, nodeno, normal_flag, cnt)
        print oraupdsql
        try:
            oracon_upd.execone(oraupdsql)
            oracon_upd.commit()
        except Exception, detail:
            print '%s,%s -> %s' % (companyno, nodeno, detail)
#oracon_upd.commit()

if oracon_upd.db:
    oracon_upd.se_close()
if oracon_nmscm.db:
    oracon_nmscm.se_close()
if oracon_oems.db:
    oracon_oems.se_close()

con.close()

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] END\n" % (nowdate)
