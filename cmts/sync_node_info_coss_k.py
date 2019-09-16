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
        con = pymssql.connect(host='CossMS_CG',user=cossdb.account,password=cossdb.passwd,database='cossdb')
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




        


# 3 DSTB
if mode == 'full':
  querysql = "select b.companyno,b.subsid,f.stbcmmac cmmac,b.custstatus,a.mscity,a.msdistrict,a.msregion,a.msroad,a.addrname, \
                    case when a.nodeno is not null and a.nodeno <> '' and a.nodeno <> '未設' then a.nodeno else 'ZZ999' end nodeno, \
                    case when a.linkid is not null and a.linkid <> '' and a.linkid <> '未設' then a.linkid else 'ZZ999-999999' end linkid, \
                    b.packagename,b.billitem,b.swversion,b.swversion2,b.singlesn,b.smartcard,b.chargename,b.singlesn2,b.chargename2, \
                    case when g.chargename is not null and g.chargename <> '' then 'Y' else 'N' end smod \
                    from ms0102 a with (nolock) \
                    inner join ms0200 b with (nolock) on b.companyno=a.companyno and b.custid=a.custid and substring(b.custstatus,1,1) in ('0','1','2','6','7','8','9','A','B') and substring(b.servicename,1,1) = '3' and b.singlesn is not null and b.singlesn <> '' \
                    inner join mi0130 f with (nolock) on f.companyno=b.companyno and f.singlesn=b.singlesn and f.stbcmmac is not null and f.stbcmmac <> '' \
                    left join ms0210 g with (nolock) on g.companyno=b.companyno and g.subsid=b.subsid and (substring(g.chargename,1,5) in ('77082','77152') or substring(g.chargename,1,6) in ('3C1010','3C101A')) \
                    where a.companyno='%s' and a.addrno='0' " % (so)
else:
  querysql = "select b.companyno,b.subsid,f.stbcmmac cmmac,b.custstatus,a.mscity,a.msdistrict,a.msregion,a.msroad,a.addrname, \
                    case when a.nodeno is not null and a.nodeno <> '' and a.nodeno <> '未設' then a.nodeno else 'ZZ999' end nodeno, \
                    case when a.linkid is not null and a.linkid <> '' and a.linkid <> '未設' then a.linkid else 'ZZ999-999999' end linkid, \
                    b.packagename,b.billitem,b.swversion,b.swversion2,b.singlesn,b.smartcard,b.chargename,b.singlesn2,b.chargename2, \
                    case when g.chargename is not null and g.chargename <> '' then 'Y' else 'N' end smod \
                    from ms0102 a with (nolock) \
                    inner join ms0200 b with (nolock) on b.companyno=a.companyno and b.custid=a.custid and substring(b.custstatus,1,1) in ('0','1','2','6','7','8','9','A','B') and substring(b.servicename,1,1) = '3' and b.singlesn is not null and b.singlesn <> '' \
                    left join ms0030 c with (nolock) on c.companyno=a.companyno and c.hpunicode=a.hpunicode \
                    left join ms0211 d with (nolock) on d.companyno=b.companyno and d.subsid=b.subsid and d.singlesn is not null and d.singlesn <> '' and d.stopyn <> 'Y' \
                    inner join mi0130 f with (nolock) on f.companyno=b.companyno and f.singlesn=b.singlesn and f.stbcmmac is not null and f.stbcmmac <> '' \
                    left join ms0210 g with (nolock) on g.companyno=b.companyno and g.subsid=b.subsid and (substring(g.chargename,1,5) in ('77082','77152') or substring(g.chargename,1,6) in ('3C1010','3C101A')) \
                    where a.companyno='%s' and a.addrno='0' and \
                    (b.createtime >= '%s' or b.updatetime >= '%s' or b.tiestart >= '%s' or b.instdate >= '%s' or b.stopdate >= '%s' or b.recoverdate >= '%s' or b.movedate >= '%s' or b.haltdate >= '%s' or b.discntdate >= '%s' or b.connectdate >= '%s' or b.haltendd >= '%s' or \
                    a.createtime >= '%s' or a.updatetime >= '%s' or c.createtime >= '%s' or c.updatetime >= '%s' or d.createtime >= '%s' or d.updatetime >= '%s' or d.instdate >= '%s') \
                    group by b.companyno,b.subsid,f.stbcmmac,b.custstatus,a.mscity,a.msdistrict,a.msregion,a.msroad,a.addrname,a.nodeno,a.linkid,b.packagename,b.billitem,b.swversion,b.swversion2,b.singlesn,b.smartcard,b.chargename,b.singlesn2,b.chargename2,g.chargename" % (so,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr,datestr)
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
            swversion = curarr[ii][13]
            if swversion is None:
                swversion = ''
            swversion2 = curarr[ii][14]
            if swversion2 is None:
                swversion2 = ''
            singlesn = curarr[ii][15]
            if singlesn is None:
                singlesn = ''
            smartcard = curarr[ii][16]
            if smartcard is None:
                smartcard = ''
            chargename = curarr[ii][17]
            if chargename is None:
                chargename = ''
            singlesn2 = curarr[ii][18]
            if singlesn2 is None:
                singlesn2 = ''
            chargename2 = curarr[ii][19]
            if chargename2 is None:
                chargename2 = ''
            smod = curarr[ii][20]
            if smod is None or smod == 'N':
                smod = ''

            if cmmac is not None:
                oraupdsql = "update cmmac set subsid='',custstatus='',city='',district='',region='',road='',addrname='',servicename='',node='',link='',billpkg='',billitem='',swversion='',swversion2='',singlesn='',smartcard='',chargename='',singlesn2='',chargename2='',smod='',coss_updtime=trunc(sysdate) where companyno='%s' and cmmac<>'%s' and subsid=%d" % (companyno, cmmac, subsid)
                print oraupdsql
                try:
                    oracon_upd.execone(oraupdsql)
                except Exception, detail:
                    print '%s,(%s,%d) -> %s' % (oraupdsql, companyno, subsid, detail)
                oraupdsql = "update cmmac set subsid='%d',custstatus='%s',city='%s',district='%s',region='%s',road='%s',addrname='%s',servicename='3 DSTB',node='%s',link='%s',billpkg='%s',billitem='%s',swversion='%s',swversion2='%s',singlesn='%s',smartcard='%s',chargename='%s',singlesn2='%s',chargename2='%s',smod='%s',coss_updtime=trunc(sysdate) where companyno='%s' and cmmac='%s'" % (subsid, custstatus, city, district, region, road, addrname, nodeno, link, billpkg, billitem, swversion, swversion2, singlesn, smartcard, chargename, singlesn2, chargename2, smod, companyno, cmmac)
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


if mode == 'full':
    oraupdsql = "update cmmac set subsid='',custstatus='',city='',district='',region='',road='',addrname='',servicename='',node='',link='',billpkg='',billitem='',swversion='',swversion2='',singlesn='',smartcard='',chargename='',singlesn2='',chargename2='',smod='',coss_updtime=trunc(sysdate) where companyno='%s' and coss_updtime < sysdate-8 and (subsid is not null or custstatus is not null) and substr(servicename,1,1) <= '9'" % (companyno)
    print oraupdsql
    try:
        oracon_upd.execone(oraupdsql)
    except Exception, detail:
        print '%s -> %s' % (oraupdsql, detail)


#querysql = "select companyno,nodeno,netid,chname,rulecmip,instplace,mscity,msdistrict,msregion,locateaddr from ms0020 with (nolock) where companyno='%s' and rulecmip <>''" % (so)
#tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
#print "[%s]" % (tme)
#print querysql
#cur.execute(querysql)
#node_arr = {}
#i = 0
#while 1:
#    curarr = cur.fetchmany(100)
#    i = i+1
#    if curarr:
#        xlen = len(curarr)
#        for ii in range(0, xlen):
#            companyno = curarr[ii][0]
#            nodeno = curarr[ii][1]
#            netid = curarr[ii][2]
#            chname = curarr[ii][3]
#            cmmac = curarr[ii][4]
#            instplace = curarr[ii][5]
#            r1 = curarr[ii][6]
#            r2 = curarr[ii][7]
#            r3 = curarr[ii][8]
#            if r3=='未設':
#                r3 = ''
#            r4 = curarr[ii][9]
#            if r4!='':
#                address = r1+r2+r3+r4
#            else:
#                address = r1+r2+r3
#            print companyno,nodeno,address
#            oraupdsql = "begin proc_upd_outdoor_cm('%s','%s','%s','%s','%s','%s','%s'); end;" % (companyno, cmmac, nodeno, netid, chname, instplace, address)
#            print oraupdsql
#            try:
#                oracon_upd.execone(oraupdsql)
#                oracon_upd.commit()
#            except Exception, detail:
#                print '%s,%s -> %s' % (companyno, cmmac, detail)
#    else:
#        break

#oracon_upd.commit()

if oracon_upd.db:
    oracon_upd.se_close()

con.close()

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] END\n" % (tme)
