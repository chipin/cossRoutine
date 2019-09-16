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

someday = time.localtime(time.time()+6*60*60)

time1_start = "%s%02d%02d 09:00:00" % (someday[0],someday[1],someday[2])
time1_end = "%s%02d%02d 09:15:00" % (someday[0],someday[1],someday[2])

time2_start = "%s%02d%02d 13:30:00" % (someday[0],someday[1],someday[2])
time2_end = "%s%02d%02d 13:45:00" % (someday[0],someday[1],someday[2])

time3_start = "%s%02d%02d 18:00:00" % (someday[0],someday[1],someday[2])
time3_end = "%s%02d%02d 18:15:00" % (someday[0],someday[1],someday[2])


try:
  con = pymssql.connect(host='kbroCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')
  cur = con.cursor()
except Exception, errmesg:
  print 'Error:',errmesg
  sys.exit(0)
  
sql = "select companyno,custid,subsid,worksheet,servicename,convert(varchar,bookdate,120) booktime from ms0301 with(nolock)  where companyno = '210' and servicename = '3 DSTB' and substring(sheetstatus,1,1) = '0'  \
and ((bookdate between '%s' and '%s' ) or (bookdate between '%s' and '%s' ) or (bookdate between '%s' and '%s' )) \
and substring(packagename,1,4) in ('G148','G149') and convert(char,bookdate,24) != '09:16:00' and convert(char,bookdate,24) != '13:46:00' and convert(char,bookdate,24) != '18:16:00' and (prndate ='' or prndate is null)  \
group by companyno,custid,subsid,worksheet,servicename,bookdate" % (time1_start,time1_end,time2_start,time2_end,time3_start,time3_end)
#print sql
cur.execute(sql)
curarr = cur.fetchall()
xlen = len(curarr)
print sql
mloop = xlen
i=0
while i<xlen:
    companyno = curarr[i][0]
    custid = int(curarr[i][1])
    subsid = int(curarr[i][2])
    worksheet = curarr[i][3]
    servicename= curarr[i][4]
    booktime = curarr[i][5]
    i = i+1
    upttime = ""
    uptdate = ""
    if int(booktime[11:13]) == 9:
      upttime = "09:16:00"
    elif int(booktime[11:13]) == 13:
      upttime = "13:46:00"
    elif int(booktime[11:13]) == 18:
      upttime = "18:16:00"
    
    bookdate = booktime[:10]
    print '[OrigData] Subsid:',subsid,'-Worksheet:',worksheet,'-booktime:',booktime
    upt = "update ms0301 set bookdate =convert(varchar(20),'%s %s',20) where subsid='%d' and worksheet='%s' and companyno='210' and servicename = '3 DSTB' and substring(sheetstatus,1,1) = '0' and (prndate ='' or prndate is null) and substring(packagename,1,4) in ('G148','G149') " % (bookdate,upttime,subsid,worksheet)
    print '[UptSQL]',upt
    try:
      #cur.execute(upt)
      pass
    except Exception, msg:
      print 'ERROR:',str(msg)
      
    upt = "update ms0301 set bookdate =convert(varchar(20),'%s %s',20) where custid='%d' and worksheet='%s' and companyno='210' and servicename != '3 DSTB' and substring(sheetstatus,1,1) = '0' and (prndate ='' or prndate is null)  " % (bookdate,upttime,custid,worksheet)
    print '[UptSQL]',upt
    try:
      #cur.execute(upt)
      pass
    except Exception, msg:
      print 'ERROR:',str(msg)

    
    upt2 = "update ms0300 set bookdate=convert(varchar(20),'%s %s',20),examremark = case when examremark is null then 'K'  when examremark ='' then 'K' else examremark+',K' end where custid='%d' and worksheet='%s' and companyno='210'" % (bookdate,upttime,custid,worksheet)
    #cur.execute(upt2)
    print '[UptSQL2]',upt2
    try:
      #cur.execute(upt2)
      pass
    except Exception, msg:
      print 'ERROR:',str(msg)
    #if (i%30)==0:
    #con.commit()
    #print 'companyno:',companyno,';custid:',custid,';subsid:',subsid,';worksheet:',worksheet,';bookdate:',bookdate,';createtime:',createtime

print 'count:',i

con.close()

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] END\n" % (tme)
