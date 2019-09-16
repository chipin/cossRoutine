#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] START" % (tme)

someday = time.localtime(time.time()-3*24*60*60)
datestr = "%s-%02d-%02d 00:00:00" % (someday[0],someday[1],someday[2])
someday = time.localtime(time.time())
today   = "%s%02d%02d" % (someday[0],someday[1],someday[2])

oracon = ORA('nms@cnis')
if not oracon.db:
		print 'nms conn fail'
		sys.exit(0)

oracon2 = ORA('coss@cnis')
if not oracon2.db:
		print 'coss conn fail'
		sys.exit(0)

#NMS 讀取CMMAC table 重複訂編的資料
oraqrysql = "SELECT COMPANYNO,SUBSID FROM CMMAC GROUP BY COMPANYNO,SUBSID HAVING count(*)>1"
rs = oracon.execall(oraqrysql)
if rs is not None and len(rs) > 0:
	for a_row in rs:
  		if a_row[1] <> None:
  				subsid = int(a_row[1])
  				so = a_row[0]
  		else:
  				subsid=None
  				so =a_row[0]
			#訂編非空白才繼續處理
  		if subsid <> None:
    			print '%s,%s' % (subsid,so)
    			try:
    					if so=='106':
    							con = pymssql.connect(host='CossMS_CG',user=cossdb.account,password=cossdb.passwd,database='cossdb_cg')
    					elif so in ['101','103','104','300','701']:
    							con = pymssql.connect(host='TFMCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')
    					else:
    							con = pymssql.connect(host='kbroCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')
    					cur = con.cursor()
    					#去震江讀訂編的設備編號與服務別
    					querysql = "select a.singlesn,a.servicename,a.custid from ms0200 a with (nolock) where a.subsid= '%s' and a.companyno ='%s' and a.singlesn <> '' " %(subsid,so)
    					#print querysql
    					cur.execute(querysql)
    					workarr = cur.fetchall()
    					n=0
    					for wrk in workarr:
    					    devid = wrk[0]
    					    devser = wrk[1]
    					    custid = wrk[2]
    					    n=n+1
    					    if n > 0 : 
    					    		break
    					#服務別為DSTB時需另外讀CMMAC
    					if devser=='3 DSTB':
    							#台媒去讀CA_STB
    							if so in ['101','103','104','300','701']:
    									oraqrysql2 = "SELECT CMMAC FROM CA_STB WHERE SO= '%s' and STBNO= '%s' "% (so,devid)
    									rs2 = oracon2.execall(oraqrysql2)
    									if rs2 is not None and len(rs2) > 0:
    										for a_row2 in rs2:
    												devid= a_row2[0]
    									#print "DSTB TFM => %s,%s,%s,%s" % (so,subsid,devid,devser)
    							#KBRO去讀mi0130
    							else:
    									querysql2 = "select b.stbcmmac from mi0130 b with (nolock) where b.companyno ='%s' and b.singlesn ='%s' " %(so,devid)
    									cur.execute(querysql2)
    									workarr2 = cur.fetchall()
    									n2=0
    									for wrk2 in workarr2:
    											devid = wrk2[0]
    											n2=n2+1
    									if n2 >0:
    											break
    									#print "DSTB KBRO => %s,%s,%s,%s" % (so,subsid,devid,devser)
    					#else:
    							#print "CM => %s,%s,%s,%s" % (so,subsid,devid,devser)
    					#CMMAC不為空才處理更新CMMAC資料庫
    					if devid is not None:
    							#先讀出地址與NODE與LINKID
    							querysql = "select a.mscity,a.msdistrict,a.msregion,a.msroad,a.addrname, \
    							                   case when a.nodeno is not null and a.nodeno <> '' and a.nodeno <> '未設' then a.nodeno else 'ZZ999' end nodeno, \
                                     case when a.linkid is not null and a.linkid <> '' and a.linkid <> '未設' then a.linkid else 'ZZ999-999999' end linkid \
    							            from ms0102 a with (nolock) where a.companyno='%s' and a.addrno='0' and a.custid= '%s' " %(so,custid)
    							#print querysql
    							cur.execute(querysql)
    							workarr3 = cur.fetchall()
    							n3=0
    							for wrk3 in workarr3:
    							    city = wrk3[0]
    							    district = wrk3[1]
    							    region = wrk3[2]
    							    road = wrk3[3]
    							    addrname = wrk3[4]
    							    nodeno = wrk3[5]
    							    linkid = wrk3[6]
    							    n3=n3+1
    							    if n3 > 0 : 
    							    		break
    							oraupdsql = "update cmmac set subsid='',custstatus='',city='',district='',region='',road='',addrname='',servicename='',node='',link='',billpkg='',billitem='',swversion='',swversion2='',singlesn='',smartcard='',chargename='',singlesn2='',chargename2='',smod='',coss_updtime=trunc(sysdate) where companyno='%s' and cmmac<>'%s' and subsid=%d" % (so, devid, subsid)
    							print oraupdsql
    							try:
    									oracon.execone(oraupdsql)
    							except Exception, detail:
    									print '%s,(%s,%d) -> %s' % (oraupdsql, so, subsid, detail)
    							oraupdsql = "update cmmac set subsid='%d',city='%s',district='%s',region='%s',road='%s',addrname='%s',node='%s',link='%s' where companyno='%s' and cmmac='%s'" % (subsid, city, district, region, road, addrname, nodeno, linkid, so, devid)
    							print oraupdsql
    							try:
    									oracon.execone(oraupdsql)
    							except Exception, detail:
    									print '%s,(%s,%d) -> %s' % (oraupdsql, so, subsid, detail)
    							oracon.commit()
    					con.close()
    			except Exception, errmesg:
    					print 'Error:',errmesg
    					sys.exit(0)

if oracon.db is not None:
    oracon.se_close()

if oracon2.db is not None:
    oracon2.se_close()
    


tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] END\n" % (tme)
