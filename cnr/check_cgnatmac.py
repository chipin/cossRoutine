#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# CMMAC: xxxSTB   CPEMAC: xxxSTBdefault
# CMMAC: xxxTV10M CPEMAC: xxxTVSTB
# CMMAC: xxxCPzz  CPEMAC: xxxMTA-yy
import os,sys,time,string,re
from oraclass import ORA
import cossdb,pymssql
import pexpect

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

  
def upt_temp2(con,singlesn,companyno,res):
  SQL = "update temp2 set ver = '%s' where so ='%s' and singlesn='%s' " % (res,companyno,singlesn)
  try:
    con.execone(SQL)
    print SQL
    con.commit()
  except Exception, msg:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Except-01: '+str(msg)
    
def check_ms0200(curos,cpemac,companyno):
  
  SQL = "select subsid from ms0200 with(nolock) where companyno='%s' and singlesn='%s'" % (companyno,cpemac)
  curos.execute(SQL)
  curarr = curos.fetchmany(100)
  if curarr:
      xlen = len(curarr)
      for ii in range(0, xlen):
            subsid = curarr[ii][0]
      return subsid
  else:
      return 0
      

def conn(host, uid, pwd):
    try:
        nrcmd = '/opt/nwreg2/usrbin/nrcmd -C ' + host + ' -N ' + uid + ' -P ' + pwd
        print nrcmd
        cnr_shell = pexpect.spawn(nrcmd, timeout=15)
        cnr_shell.expect('nrcmd>', timeout=15)
        print cnr_shell.before
        print 'conn() - OK'
        return cnr_shell
    except Exception, e:
        print 'conn() - ERROR: '+str(e)
        if cnr_shell is not None:
            cnr_shell.close(True)
        return None
        
def fixpublic(cnr_shell,mac):
  try:
      
      _get_str = ''
      _result_str = ''
      print mac
      cnr_shell.sendline('client ' + mac )
      cnr_shell.expect('nrcmd>', timeout=60)
      print cnr_shell.before
      _get_str = cnr_shell.before
      if _get_str.find("302 Not Found") >=0:
         #cnr_shell.sendline('client ' + mac + ' create selection-criteria=%s'%(addTag))
         #cnr_shell.expect('nrcmd>', timeout=60)
         #print cnr_shell.before
         return 0
      else:
         #cnr_shell.sendline('client ' + mac + ' set selection-criteria=%s'%(addTag))
         #cnr_shell.expect('nrcmd>', timeout=60)
         #print cnr_shell.before
         return 1
      #_result_str = cnr_shell.before
      #cnr_shell.sendline('save')
      #cnr_shell.expect('nrcmd>', timeout=60)
      #print cnr_shell.before
      #cnr_shell.sendline('dhcp reload')
      #cnr_shell.expect('nrcmd>', timeout=60)
      #print cnr_shell.before
      
      
  except Exception, e:
      print 'fixpublic() - ERROR: '+str(e)
      return -2   
      
def fixprivate(cnr_shell,ora,singlesn,companyno,mac):
  try:
      
      _get_str = ''
      _result_str = ''
      print mac
      cnr_shell.sendline('client ' + mac )
      cnr_shell.expect('nrcmd>', timeout=60)
      print cnr_shell.before
      _get_str = cnr_shell.before
      if _get_str.find("302 Not Found") >=0:
         _result_str = '100Ok'
      else:
          
        cnr_shell.sendline('client ' + mac + ' delete')  
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _result_str = cnr_shell.before
      cnr_shell.sendline('save')
      cnr_shell.expect('nrcmd>', timeout=60)
      print cnr_shell.before
      cnr_shell.sendline('dhcp reload')
      cnr_shell.expect('nrcmd>', timeout=60)
      print cnr_shell.before

      _result_str = _result_str.replace(" ","")
      _result_str = _result_str.replace("'","")
      _result_str = _result_str.replace(chr(13),"")
      _result_str = _result_str.strip()

      if _result_str.find("100Ok") >= 0:
          updateSql = "UPDATE temp2 SET type='1' WHERE singlesn='%s' and so ='%s'" % (singlesn,companyno)
          print 'fixip_private() - %s => OK' % (mac)
      else:
          updateSql = "UPDATE temp2 SET type='0' WHERE singlesn='%s' and so ='%s'" % (singlesn,companyno)
      print updateSql
      ora.execone(updateSql)
      ora.commit()
      
      
  except Exception, e:
      print 'fixpublic() - ERROR: '+str(e)
      return -2         
  
so = '330'

oracon = ORA('nms@cnis')
if not oracon.db:
    sys.exit(0)
            
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
  
host = '10.222.104.79'
uid = 'provgw'
pwd = 'pv#1176'
try:
  cnr_shell_main = conn(host, uid, pwd)
  pass
  
except Exception, msg:
  nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
  print '['+nowdate+'] Error: Unable to connect to server [CNR][RETRY] '+str(msg)
  sys.stdout.flush()
  time.sleep(60)
if cnr_shell_main is None:
  sys.exit(0)
    

#SQL = "select so,singlesn,case when maker like '%仲琦%' then trim(to_char(to_number(singlesn,'XXXXXXXXXXXX')+3,'00XXXXXXXXXX')) when maker like '%凱碩%' then  \
#trim(to_char(to_number(singlesn,'XXXXXXXXXXXX')+1,'00XXXXXXXXXX')) end cpemac  from temp2 a left join cnr_ip_public b on a.singlesn = b.cmmac where b.subsid is  null and (maker like '%仲琦%' or maker like '%凱碩%') and a.so in ('330') and ver is null   "
SQL = "select so,singlesn,case when maker like '%仲琦%' then trim(to_char(to_number(singlesn,'XXXXXXXXXXXX')+3,'00XXXXXXXXXX')) when maker like '%凱碩%' then  \
  trim(to_char(to_number(singlesn,'XXXXXXXXXXXX')+1,'00XXXXXXXXXX')) end cpemac from temp2 where ver = 1 and so in ( '810','820') and type is null ";
print SQL
        
try:
  rst = oracon.execall(SQL)
  if rst is not None and len(rst) > 0:
     for aw in rst:
         so = aw[0]
         cmmac = aw[1]
         cpemac = aw[2]
         ms0200 = check_ms0200(cur,cpemac,so)
         if ms0200 ==0:
           result = fixprivate(cnr_shell_main,oracon,cmmac,so,cpemac)
           print cpemac,':fixprivate'
         else:
           print cpemac,':',ms0200
         #upt_temp2(oracon,cmmac,so,result)
         
  else:
    print 'NO data'      
except Exception, msg:
  nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
  print '['+nowdate+'] Except-01: '+str(msg)
  