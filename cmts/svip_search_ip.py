#!/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
import binascii
import threading
from pysnmpclass import snmpclass
from oraclass import ORA
import cm2privateIP
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

######################
# 程式開始
######################
nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print '###################################'
print '#',nowdate
print '###################################'
oracnis = ORA('nms@cnis')
oracoss = ORA('coss@cnis')
oraoems = ORA('oems@kbro_nmsdb')

# 參數
if  len(sys.argv) != 2:
    print 'please input parameter type!'
    sys.exit(0)

svipType = sys.argv[1].upper()
if  svipType!='SVIP' and svipType!='WRS':
    print 'input type error!'
    sys.exit(0)

'''
--測試1
rst = cm2privateIP.getIP('220','788df7316b00')
if  rst['rtn']=='ok':
    print rst['msg']
sys.exit(0)

--測試2
import cossdb,pymssql
con = pymssql.connect(host='kbroCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')
cur = con.cursor()
sql = "SELECT singlesn FROM ms0200 WITH(NOLOCK) WHERE companyno='%s' AND subsid='%s' AND singlesn!=''ORDER BY companyno ASC,subsid ASC"%('220','500026')
cur.execute(sql)
curarr = cur.fetchall()
if  curarr:
    print curarr[0][0]
else:
    print 'none'
sys.exit(0)

--測試3
sql = "SELECT cmmac from ca_stb where stbno ='167601309097' and cmmac!=''"
rst = oracoss.execall(sql)
if  rst is not None and len(rst) > 0:
    print rst[0][0]
sys.exit(0)
'''



# 搜尋 svip_alarm 資料表
sql = "SELECT companyno,subsid,type FROM svip_alarm WHERE STOPYN='N' AND FLAG='%s' ORDER BY companyno ASC,subsid ASC"%(svipType)
rst = oraoems.execall(sql)
svipInfos = []
if  rst is not None and len(rst) > 0:
    for item in rst:
        temp = {'so':str(int(item[0])),'subsid':int(item[1]),'type':item[2]}
        svipInfos.append(temp)
else:
    print "[%s-project]step1.SELECT TABLE svip_alarm null"%(svipType)

# step2.查詢ip
for svipInfo in svipInfos:
    so     = svipInfo['so']
    subsid = svipInfo['subsid']
    type   = svipInfo['type']
    print "\n### SEARCH IP start[so=%s,subsid=%s,type=%s]"%(so,subsid,type)
    sql = "SELECT ip FROM cmmac WHERE companyno='%s' AND subsid ='%s' AND status='6'"%(so,subsid)
    print "[%s-project]step1.%s"%(svipType,sql)
    rst = oracnis.execall(sql)
    privateIp = ''
    if  rst is not None and len(rst) > 0:
        privateIp = rst[0][0]
        print "[%s-project]step2-1.privateIp=%s"%(svipType,privateIp)
    else:
        # step2-2.若無ip資料，需由 cmmac 反查 ip
        cmmac  = ''
        import cossdb,pymssql
        if  so=='106':
            con = pymssql.connect(host='CossMS_CG',user=cossdb.account,password=cossdb.passwd,database='cossdb_cg')
        elif so in ['101','103','104','300','701']:
            con = pymssql.connect(host='TFMCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')
        else:
            con = pymssql.connect(host='kbroCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')

        # step2-2-1.先取得 singlesn
        # 中斷測試stb so,subsid,type = '220','9040800','STB'
        # 中斷測試cm  so,subsid,type = '220','500026','CM'
        cur = con.cursor()
        sql = "SELECT singlesn FROM ms0200 WITH(NOLOCK) WHERE companyno='%s' AND subsid='%s' AND singlesn!='' ORDER BY companyno ASC,subsid ASC"%(so,subsid)
        cur.execute(sql)
        curarr = cur.fetchall()
        if  curarr:
            # 有 singlesn
            singlesn = curarr[0][0]
            print "[%s-project]step2-2(1).singlesn=%s"%(svipType,singlesn)
        else:
            # 無 singlesn 跳過迴圈
            print "[%s-project]step2-2(1).search singlesn null\n[%s]"%(svipType,sql)
            continue

        # step3-2：取得 cmmac(依type有不同處理)
        if  type=='CM':
            # CM：singlesn 即 cmmac
            cmmac = singlesn
            print "[%s-project]step2-2(2).cmmac=singlesn(%s)"%(svipType,cmmac)
        else:
            # STB：用【機號singlesn】查詢 cmmac
            sql = "SELECT stbcmmac FROM mi0130 WITH(NOLOCK) WHERE companyno='%s' AND singlesn='%s' AND stbcmmac!='' "%(so,singlesn)
            cur.execute(sql)
            curarr = cur.fetchall()
            # 台媒和凱擘處理機制不同
            if  so in ['101','103','104','300','701']:
                # 台媒
                if  curarr:
                    cmmac = curarr[0][0]
                    print "[%s-project]step2-2(2)tfm.cmmac=stbcmmac(%s)"%(svipType,cmmac)
                else:
                    # 無 stbcmmac 跳過迴圈
                    print "[%s-project]step2-2(2)tfm.search stbcmmac null\n[%s]"%(svipType,sql)
                    continue
            else:
                # 中斷測試 curarr,singlesn = None,'167601309097'
                # 凱擘
                if  curarr:
                    cmmac = curarr[0][0]
                    print "[%s-project]step2-2(2)kbro.cmmac=stbcmmac(%s)"%(svipType,cmmac)
                else:
                    # 無 stbcmmac 則搜尋 ca_stb
                    print "[%s-project]step2-2(2)kbro.search stbcmmac null\n[%s]"%(svipType,sql)
                    sql = "SELECT cmmac FROM ca_stb WHERE stbno ='%s' AND cmmac IS NOT NULL"%(singlesn)
                    rst = oracoss.execall(sql)
                    if  rst is not None and len(rst) > 0:
                        cmmac = rst[0][0]
                        print "[%s-project]step2-2(3)kbro.cmmac=stbno(%s)"%(svipType,cmmac)
                    else:
                        print "[%s-project]step2-2(3)kbro.search stbno null\n[%s]"%(svipType,sql)
                        continue

        # step2-3：由 cmmac 取得ip
        rst = cm2privateIP.getIP(so,cmmac)
        if  rst['rtn']=='ok':
            privateIp = rst['msg']
            print "[%s-project]step2-3.cmmac2ip[%s]"%(svipType,privateIp)


    # step3：將 ip update 回 svip_alarm
    sql = "UPDATE svip_alarm SET CMIP='%s' WHERE companyno='%s' AND subsid='%s' AND type='%s' AND FLAG='%s'"%(privateIp,so,subsid,type,svipType)
    oraoems.execone(sql)
    oraoems.commit()
    print "[%s-project]step3.update table svip_alarm\n[%s]"%(svipType,sql)



    # 67行 for迴圈結束

if  oracnis:
    oracnis.se_close()
if  oracoss:
    oracoss.se_close()
if  oraoems:
    oraoems.se_close()
sys.exit(0)
