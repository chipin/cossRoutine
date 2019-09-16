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
print "[%s]: Begin" % (tme)

oracon = ORA('QOS@CNIS')

con_kbro = pymssql.connect(host='kbroCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
cur_kbro = con_kbro.cursor()

con_TFM = pymssql.connect(host='TFMCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
cur_TFM = con_TFM.cursor()

con_CG = pymssql.connect(host='CossMS_CG',user=cossdb.account,password=cossdb.passwd,database='cossdb_cg')
cur_CG = con_CG.cursor()

fdsql = "select sid,companyno,cmmac from speedtest where cmmac is not null and v2sw_id is null and status='OK' and subsid=0 and time >= sysdate-14"
print fdsql
rs = oracon.execall(fdsql)
if rs != None and len(rs) > 0:
    for a_row in rs:
        try:
            sid = a_row[0]
            so = a_row[1]
            cmmac = a_row[2]
            print sid,so,cmmac
            qrysql = "select subsid,billitem from ms0200 with (nolock) where companyno='%s' and singlesn='%s'" % (so, cmmac)
            if so in ['101','103','104','300','701']:
                cur_TFM.execute(qrysql)
                xarr = cur_TFM.fetchone()
            elif so == '106':
                cur_CG.execute(qrysql)
                xarr = cur_CG.fetchone()
            else:
                cur_kbro.execute(qrysql)
                xarr = cur_kbro.fetchone()
            if xarr is not None:
                subsid = xarr[0]
                billitem = xarr[1]

                oraupdsql = "update speedtest set subsid=%d,billitem='%s' where sid=%d" % (subsid, billitem, sid)
                print oraupdsql
                oracon.execone(oraupdsql)
                oracon.commit()
        except Exception, msg:
            print msg
            sys.stdout.flush()
            continue

oracon_nmscm = ORA('NMS_CM@KBRO_NMSDB')
fdsql = "select sid,companyno,v2sw_id,v2sw_port from speedtest where v2sw_id is not null and status='OK' and subsid=0 and time >= sysdate-14"
print fdsql
rs = oracon.execall(fdsql)
if rs != None and len(rs) > 0:
    for a_row in rs:
        try:
            sid = a_row[0]
            so = a_row[1]
            v2sw_id = a_row[2]
            v2sw_port = a_row[3]
            print sid,so,v2sw_id,v2sw_port
            subsid = -1
            billitem = ''
            if v2sw_port>0:
                qrysql = "select so,subsid from fttb_v2sw_port where ne_id='%s' and port=%d and subsid > 0" % (v2sw_id, v2sw_port)
                print qrysql
                rsqry = oracon_nmscm.execall(qrysql)
                if rsqry is not None and len(rsqry)>0:
                    for qry_row in rsqry:
                        qso = qry_row[0]
                        subsid = qry_row[1]
                        print qso,subsid
                if subsid>0:
                    qrysql = "select subsid,billitem from ms0200 with (nolock) where companyno='%s' and subsid=%d" % (so, subsid)
                    if so in ['101','103','104','300','701']:
                        cur_TFM.execute(qrysql)
                        xarr = cur_TFM.fetchone()
                    elif so == '106':
                        cur_CG.execute(qrysql)
                        xarr = cur_CG.fetchone()
                    else:
                        cur_kbro.execute(qrysql)
                        xarr = cur_kbro.fetchone()
                    if xarr is not None:
                        subsid = xarr[0]
                        billitem = xarr[1]

                        oraupdsql = "update speedtest set subsid=%d,billitem='%s' where sid=%d" % (subsid, billitem, sid)
                        print oraupdsql
                        oracon.execone(oraupdsql)
                        oracon.commit()
        except Exception, msg:
            print msg
            sys.stdout.flush()
            continue

if oracon_nmscm.db:
    oracon_nmscm.se_close()

if oracon.db:
    oracon.se_close()

con_kbro.close()
con_TFM.close()
con_CG.close()
tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s]: Finish" % (tme)
