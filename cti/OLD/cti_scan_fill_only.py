#!/usr/bin/env python
# -*- coding: Big5 -*-
import sys,datetime,string,types,time
import pymssql
from oraclass import ORA

con = pymssql.connect(host='TFMCossMS_CP950',user='proguser',password='cossuser',database='cossdb')
cur = con.cursor()

if len(sys.argv)<3:
    print "Argument error"
    sys.exit(0)

oracon = ORA('CTI@CNIS')
oracon_upd = ORA('CTI@CNIS')
fdsql = "select callin_history_id,coss_id,to_char(so) so from cti010 where coss_id is not null and coss_id<>'-1' and so is not null and subsid is not null and create_date between to_date('%s','yyyymmdd') and to_date('%s235959','yyyymmddhh24miss')" % (sys.argv[1], sys.argv[2])
print fdsql
rs = oracon.execall(fdsql)
if rs != None and len(rs) > 0:
    for a_row in rs:
      try:
          callin_history_id = int(a_row[0])
          wkno = a_row[1]
          so = a_row[2]
          qrysql = "select a.singlesn from ms0301 a with (nolock) where a.companyno='%s' and a.worksheet='%s' and singlesn<>'' and singlesn is not null and singlesn<>'None'" % (so, wkno)
          #print qrysql
          upd_flag = 0
          cur.execute(qrysql)
          xarr = cur.fetchone()
          if xarr is not None:
              singlesn = xarr[0]
              if singlesn is not None and singlesn!='':
                  upd_flag = 1
                                
          if upd_flag==1:
              oraupdsql = "update cti010 set singlesn='%s' where callin_history_id='%d'" % (singlesn, callin_history_id)
              print oraupdsql
              oracon_upd.execone(oraupdsql)
              oracon_upd.commit()
          
      except Exception, msg:
          print msg
          sys.stdout.flush()
          break
          
          
if oracon is not None:
    oracon.se_close()
if oracon_upd is not None:
    oracon_upd.se_close()
con.close()

