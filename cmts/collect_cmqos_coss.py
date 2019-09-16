#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv) != 2:
    print 'ERROR: Argument error'
    sys.exit(0)

mso = sys.argv[1].upper()
dd = time.strftime("%Y%m", time.localtime())

logfile = '/ap/home/coss/log/cmts/collect_cmqos_measure_' + mso + '_' + dd + '.log'

try:
    if mso == 'CG':
        con = pymssql.connect(host='CossMS_CG',user=cossdb.account,password=cossdb.passwd,database='cossdb_cg')
        complist = "'106'"
    elif mso == 'TFM':
        con = pymssql.connect(host='TFMCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')
        complist = "'101','103','104','300','701'"
    else:
        con = pymssql.connect(host='kbroCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')
        complist = "'210','220','230','240','250','260','310','330','410','420','610','810','820'"
    cur = con.cursor()
except Exception, errmesg:
    print 'ERROR: ',errmesg
    sys.exit(0)

ora_nms = ORA('nms@cnis')
if not ora_nms.db:
    print 'ERROR: Unable to connect to server [CNIS]'
    sys.exit(0)

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] START" % (tme)

#and convert(varchar,a.finishdate,112)='%s'
qrysql = "select a.companyno,a.worksheet,a.servicename,a.subsid,a.singlesn,a.smartcard, \
case when b.nodeno is not null and b.nodeno <> '' and b.nodeno <> '未設' then b.nodeno else 'ZZ999' end nodeno, \
case when b.linkid is not null and b.linkid <> '' and b.linkid <> '未設' then b.linkid else 'ZZ999-999999' end linkid, \
b.mscitya,b.msdistricta,b.msroada,right(b.instaddrname,len(b.instaddrname)-charindex(' ',b.instaddrname)) addrname \
from ms0301 a with (nolock) inner join ms0300 b with (nolock) on b.companyno=a.companyno and b.worksheet=a.worksheet \
where a.companyno in (%s) and substring(a.sheetstatus,1,1) in ('3','4') and substring(b.workkind,1,1) not in ('3','4','7','H') \
and substring(a.servicename,1,1) in ('2','9') and len(a.singlesn) = 12 and a.opfintime >= getdate()-(6.0/24)" % (complist)
print qrysql
cur.execute(qrysql)
i = 0
havemac = {}
while 1:
    curarr = cur.fetchmany(100)
    i = i+1
    if curarr:
        xlen = len(curarr)
        j = 0
        for ii in range(0, xlen):
            j = j+1

            companyno = curarr[ii][0]
            worksheet = curarr[ii][1]
            servicename = curarr[ii][2]
            subsid = curarr[ii][3]
            singlesn = curarr[ii][4]
            smartcard = curarr[ii][5]
            nodeno = curarr[ii][6]
            linkid = curarr[ii][7]
            city = curarr[ii][8]
            district = curarr[ii][9]
            road = curarr[ii][10]
            addrname = curarr[ii][11]
            cmmac = curarr[ii][4]

            if cmmac in havemac:
                continue
            else:
                print i,j,'>',companyno,worksheet,subsid,cmmac

            oraupdsql1 = "update cmmac set subsid='',custstatus='',city='',district='',region='',road='',addrname='',servicename='',node='',link='',billpkg='',billitem='',swversion='',swversion2='',singlesn='',smartcard='',chargename='',singlesn2='',chargename2='',smod='',coss_updtime=trunc(sysdate) where companyno='%s' and cmmac<>'%s' and subsid='%s'" % (companyno, cmmac, subsid)
            oraupdsql2 = "update cmmac set subsid='%s',city='%s',district='%s',road='%s',addrname='%s',servicename='%s',node='%s',link='%s',singlesn='%s',smartcard='%s',coss_updtime=trunc(sysdate) where companyno='%s' and cmmac='%s'" % (subsid, city, district, road, addrname, servicename, nodeno, linkid, singlesn, smartcard, companyno, cmmac)
            print oraupdsql1
            print oraupdsql2
            try:
                ora_nms.execone(oraupdsql1)
                ora_nms.execone(oraupdsql2)
                ora_nms.commit()
            except Exception, detail:
                print detail

            if mso == 'TFM':
                execmd = "ssh nms@tfm-qos 'bin/nms/cm_measure.sh %s %s' >> %s" % (companyno,cmmac,logfile)
            else:
                execmd = "ssh nms@ntp-qos 'bin/nms/cm_measure.sh %s %s' >> %s" % (companyno,cmmac,logfile)
            os.system(execmd)

            havemac[cmmac] = 1
    else:
        break

if mso == 'TFM':
    qrysql = "select a.companyno,a.worksheet,a.servicename,a.subsid,a.singlesn,a.smartcard, \
case when b.nodeno is not null and b.nodeno <> '' and b.nodeno <> '未設' then b.nodeno else 'ZZ999' end nodeno, \
case when b.linkid is not null and b.linkid <> '' and b.linkid <> '未設' then b.linkid else 'ZZ999-999999' end linkid, \
b.mscitya,b.msdistricta,b.msroada,right(b.instaddrname,len(b.instaddrname)-charindex(' ',b.instaddrname)) addrname,f.stb_cm_mac \
from ms0301 a with (nolock) inner join ms0300 b with (nolock) on b.companyno=a.companyno and b.worksheet=a.worksheet \
inner join nwis0020 f with (nolock) on (f.companyno=a.companyno or f.companyno is null) and f.singlesn=a.singlesn and f.mtkind='STB' and len(f.stb_cm_mac) = 12 \
where a.companyno in (%s) and substring(a.sheetstatus,1,1) in ('3','4') and substring(b.workkind,1,1) not in ('3','4','7','H') \
and substring(a.servicename,1,1) in ('3') and a.singlesn is not null and a.singlesn <> '' and a.opfintime >= getdate()-(6.0/24)" % (complist)
else:
    qrysql = "select a.companyno,a.worksheet,a.servicename,a.subsid,a.singlesn,a.smartcard, \
case when b.nodeno is not null and b.nodeno <> '' and b.nodeno <> '未設' then b.nodeno else 'ZZ999' end nodeno, \
case when b.linkid is not null and b.linkid <> '' and b.linkid <> '未設' then b.linkid else 'ZZ999-999999' end linkid, \
b.mscitya,b.msdistricta,b.msroada,right(b.instaddrname,len(b.instaddrname)-charindex(' ',b.instaddrname)) addrname,f.stbcmmac \
from ms0301 a with (nolock) inner join ms0300 b with (nolock) on b.companyno=a.companyno and b.worksheet=a.worksheet \
inner join mi0130 f with (nolock) on f.companyno=a.companyno and f.singlesn=a.singlesn and len(f.stbcmmac) = 12 \
where a.companyno in (%s) and substring(a.sheetstatus,1,1) in ('3','4') and substring(b.workkind,1,1) not in ('3','4','7','H') \
and substring(a.servicename,1,1) in ('3') and a.singlesn is not null and a.singlesn <> '' and a.opfintime >= getdate()-(6.0/24)" % (complist)
print qrysql
cur.execute(qrysql)
i = 0
havesn = {}
while 1:
    curarr = cur.fetchmany(100)
    i = i+1
    if curarr:
        xlen = len(curarr)
        j = 0
        for ii in range(0, xlen):
            j = j+1

            companyno = curarr[ii][0]
            worksheet = curarr[ii][1]
            servicename = curarr[ii][2]
            subsid = curarr[ii][3]
            singlesn = curarr[ii][4]
            smartcard = curarr[ii][5]
            nodeno = curarr[ii][6]
            linkid = curarr[ii][7]
            city = curarr[ii][8]
            district = curarr[ii][9]
            road = curarr[ii][10]
            addrname = curarr[ii][11]
            cmmac = curarr[ii][12]

            if singlesn in havesn:
                continue
            else:
                print i,j,'>',companyno,worksheet,subsid,singlesn,cmmac

            oraupdsql1 = "update cmmac set subsid='',custstatus='',city='',district='',region='',road='',addrname='',servicename='',node='',link='',billpkg='',billitem='',swversion='',swversion2='',singlesn='',smartcard='',chargename='',singlesn2='',chargename2='',smod='',coss_updtime=trunc(sysdate) where companyno='%s' and cmmac<>'%s' and subsid='%s'" % (companyno, cmmac, subsid)
            oraupdsql2 = "update cmmac set subsid='%s',city='%s',district='%s',road='%s',addrname='%s',servicename='%s',node='%s',link='%s',singlesn='%s',smartcard='%s',coss_updtime=trunc(sysdate) where companyno='%s' and cmmac='%s'" % (subsid, city, district, road, addrname, servicename, nodeno, linkid, singlesn, smartcard, companyno, cmmac)
            print oraupdsql1
            print oraupdsql2
            try:
                ora_nms.execone(oraupdsql1)
                ora_nms.execone(oraupdsql2)
                ora_nms.commit()
            except Exception, detail:
                print detail

            if mso == 'TFM':
                execmd = "ssh nms@tfm-qos 'bin/nms/cm_measure.sh %s %s' >> %s" % (companyno,cmmac,logfile)
            else:
                execmd = "ssh nms@ntp-qos 'bin/nms/cm_measure.sh %s %s' >> %s" % (companyno,cmmac,logfile)
            os.system(execmd)

            havesn[singlesn] = 1
    else:
        break

con.close()

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] END" % (tme)
