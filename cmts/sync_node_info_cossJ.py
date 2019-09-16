#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv) > 3 or len(sys.argv) < 2:
    print 'Error: Argument error'
    sys.exit(0)

so = mode = ''
so = sys.argv[1]

if len(sys.argv) == 3:
    if len(sys.argv[2]) > 0:
        mode = sys.argv[2].lower()
        if mode != 'full':
            mode = ''

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] START" % (tme)

someday = time.localtime(time.time()-3*24*60*60)
datestr = "%s-%02d-%02d 00:00:00" % (someday[0],someday[1],someday[2])
someday = time.localtime(time.time())
today   = "%s%02d%02d" % (someday[0],someday[1],someday[2])

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

# 2 CM
if mode == 'full':
    querysql = "select b.companyno,b.subsid,b.singlesn cmmac,b.custstatus,a.mscity,a.msdistrict,a.msregion,a.msroad,a.addrname, \
                case when a.nodeno is not null and a.nodeno <> '' and a.nodeno <> '未設' then a.nodeno else 'ZZ999' end nodeno, \
                case when a.linkid is not null and a.linkid <> '' and a.linkid <> '未設' then a.linkid else 'ZZ999-999999' end linkid, \
                b.packagename,b.billitem,z.actdate,z.oldpackage,z.oldcharge,z.newpackage,z.newcharge,b.swversion,b.swversion2,b.singlesn,b.smartcard,b.chargename,b.singlesn2,b.chargename2 \
                from ms0102 a with (nolock) \
                inner join ms0200 b with (nolock) on b.companyno=a.companyno and b.custid=a.custid and substring(b.custstatus,1,1) in ('0','1','2','6','7','8','9','A','B') and substring(b.servicename,1,1) in ('2','F') and b.singlesn is not null and b.singlesn <> '' \
                left join ( \
                  select x.companyno,x.subsid,x.msflag,convert(varchar(8),x.startdate,112) startdate,case when x.actdate is not null and x.actdate <> '' then convert(varchar(8),x.actdate,112) else convert(varchar(8),x.startdate,112) end actdate,x.oldpackage,x.oldcharge,x.newpackage,x.newcharge \
                  from ms0216 x with (nolock) \
                  inner join ( \
                    select m.companyno,m.subsid,max(m.recvno) recvno from ms0216 m with (nolock) \
                    inner join ms0200 n with (nolock) on n.companyno=m.companyno and n.subsid=m.subsid and substring(n.custstatus,1,1) in ('0','1','2','6','7','8','9','A','B') and substring(n.servicename,1,1) in ('2','F') and n.singlesn is not null and n.singlesn <> '' \
                    where m.companyno='%s' group by m.companyno,m.subsid \
                  ) y on y.companyno=x.companyno and y.subsid=x.subsid and y.recvno=x.recvno \
                  where x.companyno='%s' and x.msflag in ('1 正常','3 原價升級') \
                ) z on z.companyno=b.companyno and z.subsid=b.subsid \
                where a.companyno='%s' and a.addrno='0' and a.custid ='10017991'" % (so,so,so)
else:
    querysql = "select b.companyno,b.subsid,b.singlesn cmmac,b.custstatus,a.mscity,a.msdistrict,a.msregion,a.msroad,a.addrname, \
                case when a.nodeno is not null and a.nodeno <> '' and a.nodeno <> '未設' then a.nodeno else 'ZZ999' end nodeno, \
                case when a.linkid is not null and a.linkid <> '' and a.linkid <> '未設' then a.linkid else 'ZZ999-999999' end linkid, \
                b.packagename,b.billitem,z.actdate,z.oldpackage,z.oldcharge,z.newpackage,z.newcharge,b.swversion,b.swversion2,b.singlesn,b.smartcard,b.chargename,b.singlesn2,b.chargename2 \
                from ms0102 a with (nolock) \
                inner join ms0200 b with (nolock) on b.companyno=a.companyno and b.custid=a.custid and substring(b.custstatus,1,1) in ('0','1','2','6','7','8','9','A','B') and substring(b.servicename,1,1) in ('2','F') and b.singlesn is not null and b.singlesn <> '' \
                left join ms0030 c with (nolock) on c.companyno=a.companyno and c.hpunicode=a.hpunicode \
                left join ms0211 d with (nolock) on d.companyno=b.companyno and d.subsid=b.subsid and d.singlesn is not null and d.singlesn <> '' and d.stopyn <> 'Y' \
                left join ( \
                  select x.companyno,x.subsid,x.msflag,convert(varchar(8),x.startdate,112) startdate,case when x.actdate is not null and x.actdate <> '' then convert(varchar(8),x.actdate,112) else convert(varchar(8),x.startdate,112) end actdate,x.oldpackage,x.oldcharge,x.newpackage,x.newcharge,x.actdate actdate2 \
                  from ms0216 x with (nolock) \
                  inner join ( \
                    select m.companyno,m.subsid,max(m.recvno) recvno from ms0216 m with (nolock) \
                    inner join ms0200 n with (nolock) on n.companyno=m.companyno and n.subsid=m.subsid and substring(n.custstatus,1,1) in ('0','1','2','6','7','8','9','A','B') and substring(n.servicename,1,1) in ('2','F') and n.singlesn is not null and n.singlesn <> '' \
                    where m.companyno='%s' and m.actdate >= '%s' group by m.companyno,m.subsid \
                  ) y on y.companyno=x.companyno and y.subsid=x.subsid and y.recvno=x.recvno \
                  where x.companyno='%s' and x.msflag in ('1 正常','3 原價升級') \
                ) z on z.companyno=b.companyno and z.subsid=b.subsid \
                where a.companyno='%s' and a.addrno='0' and a.custid ='10017991' and \
                (b.createtime >= '%s' or b.updatetime >= '%s' or b.tiestart >= '%s' or b.instdate >= '%s' or b.stopdate >= '%s' or b.recoverdate >= '%s' or b.movedate >= '%s' or b.haltdate >= '%s' or b.discntdate >= '%s' or b.connectdate >= '%s' or b.haltendd >= '%s' or \
                a.createtime >= '%s' or a.updatetime >= '%s' or c.createtime >= '%s' or c.updatetime >= '%s' or d.createtime >= '%s' or d.updatetime >= '%s' or d.instdate >= '%s' or z.actdate2 >= '%s') \
                group by b.companyno,b.subsid,b.singlesn,b.custstatus,a.mscity,a.msdistrict,a.msregion,a.msroad,a.addrname,a.nodeno,a.linkid,b.packagename,b.billitem,z.actdate,z.oldpackage,z.oldcharge,z.newpackage,z.newcharge,b.swversion,b.swversion2,b.singlesn,b.smartcard,b.chargename,b.singlesn2,b.chargename2" % (so,datestr,so,so,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr)
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
            subsid = int(curarr[ii][1])
            cmmac = curarr[ii][2]
            custstatus = curarr[ii][3]
            city = curarr[ii][4]
            district = curarr[ii][5]
            region = curarr[ii][6]
            if region == '未設':
                region = ''
            road = curarr[ii][7]
            addrname = curarr[ii][8]
            nodeno = curarr[ii][9]
            link = curarr[ii][10]
            billpkg = curarr[ii][11]
            billitem = curarr[ii][12]
            actdate = curarr[ii][13]
            oldpkg = curarr[ii][14]
            oldbill = curarr[ii][15]
            newpkg = curarr[ii][16]
            newbill = curarr[ii][17]
            swversion = curarr[ii][18]
            if swversion is None:
                swversion = ''
            swversion2 = curarr[ii][19]
            if swversion2 is None:
                swversion2 = ''
            singlesn = curarr[ii][20]
            if singlesn is None:
                singlesn = ''
            smartcard = curarr[ii][21]
            if smartcard is None:
                smartcard = ''
            chargename = curarr[ii][22]
            if chargename is None:
                chargename = ''
            singlesn2 = curarr[ii][23]
            if singlesn2 is None:
                singlesn2 = ''
            chargename2 = curarr[ii][24]
            if chargename2 is None:
                chargename2 = ''

            if billitem is not None and oldbill is not None and newpkg is not None and newbill is not None:
                if billpkg == oldpkg and billitem == oldbill: # 促案變更未過帳(現行方案=舊方案,現行收費=舊收費)
                    if today >= actdate: # 已生效
                        print 'new: ',oldpkg,oldbill,actdate,newpkg,newbill
                        billpkg = newpkg
                        billitem = newbill
                elif billpkg == newpkg and billitem == newbill: # 促案變更已過帳(現行方案=新方案,現行收費=新收費)
                    if actdate > today: # 未生效
                        print 'old: ',oldpkg,oldbill,actdate,newpkg,newbill
                        billpkg = oldpkg
                        billitem = oldbill

            if cmmac is not None:
                oraupdsql = "update cmmac set subsid='',custstatus='',city='',district='',region='',road='',addrname='',servicename='',node='',link='',billpkg='',billitem='',swversion='',swversion2='',singlesn='',smartcard='',chargename='',singlesn2='',chargename2='',smod='',coss_updtime=trunc(sysdate) where companyno='%s' and cmmac<>'%s' and subsid=%d" % (companyno, cmmac, subsid)
                print oraupdsql
                try:
                    oracon_upd.execone(oraupdsql)
                except Exception, detail:
                    print '%s,(%s,%d) -> %s' % (oraupdsql, companyno, subsid, detail)
                oraupdsql = "update cmmac set subsid='%d',custstatus='%s',city='%s',district='%s',region='%s',road='%s',addrname='%s',servicename='2 CM',node='%s',link='%s',billpkg='%s',billitem='%s',swversion='%s',swversion2='%s',singlesn='%s',smartcard='%s',chargename='%s',singlesn2='%s',chargename2='%s',smod='',coss_updtime=trunc(sysdate) where companyno='%s' and cmmac='%s'" % (subsid, custstatus, city, district, region, road, addrname, nodeno, link, billpkg, billitem, swversion, swversion2, singlesn, smartcard, chargename, singlesn2, chargename2, companyno, cmmac)
                print oraupdsql
                try:
                    oracon_upd.execone(oraupdsql)
                except Exception, detail:
                    print '%s,(%s,%d) -> %s' % (oraupdsql, companyno, subsid, detail)
                oracon_upd.commit()

                #oraupdsql = "begin coss.proc_repair_cm_status('%s',%d,'%s','%s'); end;" % (companyno, subsid, cmmac, billitem)
                #print oraupdsql
                #try:
                #    oracon_upd.execone(oraupdsql)
                #except Exception, detail:
                #    print '%s,(%s,%d) -> %s' % (oraupdsql, companyno, subsid, detail)
                #oracon_upd.commit()
    else:
        break
        
if oracon_upd.db:
    oracon_upd.se_close()

con.close()

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] END\n" % (tme)
