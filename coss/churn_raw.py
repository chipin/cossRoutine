#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv)<2:
    print "[Error]: Argument error."
    sys.exit(0)
else:
    p_so = sys.argv[1]
    if len(sys.argv)==4:
        p_bg = sys.argv[2]
        p_end = sys.argv[3]
    else:
        p_bg = ''
        p_end = ''

if p_so=='500':
    sosql = "'101','103','104','300','701'"
    db_host = "TFMCossMS"
elif p_so=='026':
    sosql = "'210','220','230','240','250','260','310','330','410','420','610','810','820'"
    db_host = "kbroCossMS"
elif p_so in ['101','103','104','300','701']:
    sosql = "'%s'" % (sys.argv[1])
    db_host = "TFMCossMS"
elif p_so in ['210','220','230','240','250','260','310','330','410','420','610','810','820']:
    sosql = "'%s'" % (sys.argv[1])
    db_host = "kbroCossMS"
elif p_so in ['106']:
    sosql = "'%s'" % (sys.argv[1])
    db_host = "CossMS_CG"
else:
    print "[Error]: Argument %s error." % (p_so)
    sys.exit(0)

yymmdd = time.strftime("%Y%m%d", time.localtime())
year = int(yymmdd[:4])
month = int(yymmdd[4:6])
day = int(yymmdd[6:8])
ydate = time.localtime(time.mktime((year,month,day,0,0,0,-1,-1,-1))-86400)
target_day = "%d/%.2d/%.2d" % (ydate[0], ydate[1], ydate[2])
ydate = time.localtime(time.mktime((year,month,day,0,0,0,-1,-1,-1)))
target_day_end = "%d/%.2d/%.2d" % (ydate[0], ydate[1], ydate[2])
ydate = time.localtime(time.mktime((year,month,day,12,0,0,-1,-1,-1))+86400)
sms_day = "%d/%.2d/%.2d %.2d:%.2d:%.2d" % (ydate[0], ydate[1], ydate[2], ydate[3], ydate[4], ydate[5])

if p_bg!='':
    target_day = p_bg
    target_day_end = p_end
print target_day,target_day_end

if p_so == '106':
  con = pymssql.connect(host=db_host,user=cossdb.account,password=cossdb.passwd,database='cossdb_cg')
else:
  con = pymssql.connect(host=db_host,user=cossdb.account,password=cossdb.passwd,database='cossdb')
cur = con.cursor()

oracon = ORA('coss@cnis')

# 0 復訊
# 1 裝機
# 2 復機
# 3 拆機
# 4 停機
# 5 維修
# 6 移機
# 7 移拆
# 9 停後復機
# A 加裝
# C 換機
# H 退拆設備
# S 促案變更

nowtime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s]: Sync beginning" % (nowtime)
loopsql="select a.companyno,a.custid,a.subsid,substring(b.workkind,1,1) typeid,convert(varchar(19),max(a.finishdate),20) finishtime,max(a.servicename),max(b.workcause),max(a.backcause),max(a.chargename) from ms0301 a with (nolock),ms0300 b with (nolock) where a.companyno=b.companyno and a.worksheet=b.worksheet and a.companyno in (%s) and a.opfintime between '%s 00:00:00' and '%s 23:59:59' and substring(b.workkind,1,1) in ('3','7','0','2') and substring(a.sheetstatus,1,1) in ('4') and substring(a.servicename,1,1) in ('2','5','7') group by a.companyno,a.custid,a.subsid,b.workkind" % (sosql, target_day, target_day_end)
print loopsql
for i in range(0, 3):
    try:
        cur.execute(loopsql)
        curarr = cur.fetchall()
        break
    except Exception, msg:
        con.close()
        con = None

        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+'] Error: Lost connection to ['+db_host+'], trying to reconnect. '+str(msg)

        if i == 2:
            sys.exit(0)
        else:
            time.sleep(60)

        con = pymssql.connect(host=db_host,user=cossdb.account,password=cossdb.passwd,database='cossdb')
        cur = con.cursor()
        continue
xlen = len(curarr)
print "Checking %d work tickets" % (xlen)
sys.stdout.flush()
i = 0
while i<xlen:
    so = curarr[i][0]
    custid = int(curarr[i][1])
    subsid = int(curarr[i][2])
    typeid = curarr[i][3]
    finishtime = curarr[i][4]
    servicename = curarr[i][5]
    workcause = curarr[i][6]
    backcause = curarr[i][7]
    chargename = curarr[i][8]
    if workcause is None:
        workcause = chargename
    if backcause is None:
        backcause = chargename

    SQL = "begin proc_upd_churn_raw('%s',%d,%d,to_date('%s','yyyy-mm-dd hh24:mi:ss'),'%s','%s','%s','%s'); end;" % (so, custid, subsid, finishtime, typeid, servicename, workcause, backcause)
    oracon.execone(SQL)
    sys.stdout.flush()
    i = i+1
    if (i%10)==0:
        oracon.commit()
oracon.commit()
oracon.se_close()
print ""
nowtime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s]: Sync OK" % (nowtime)
sys.exit(0)

oracon.se_close()
