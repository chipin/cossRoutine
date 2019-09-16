#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import threading
from oraclass import ORA
from pysnmpclass import snmpclass

os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

def to_oems(subsid,ip,reason):
  global oracnis,oraoems,subsid_ip,oems,subsid_ary,so_mapping
  
  impact_list = subsid
  companyno = subsid_ary[subsid]
  operator = so_mapping[str(companyno)]
  
  oems_id = 0
  try:
    if oems[str(impact_list)] is not None:
      oems_id = oems[str(impact_list)]
  except:
    pass
    
  
  if impact_list is not None:
    if reason == 'pingloss':
      p_descr = "SVIP CM Ping loss, 系統台:%s, 客戶編號:%s, 固定IP:%s" % (companyno,subsid,ip)
    else:
      p_descr = "SVIP CM固定IP未設定, 系統台:%s, 客戶編號:%s" % (companyno,subsid)
    if oems_id > 0: ## 持續異常
      updsql = "insert into oems_tickets_log (sid,status_date,orig_status,status,descr,account) values (%d,sysdate,5120,5120,'%s','SVIP_CM')" % (oems_id,p_descr)
      print updsql
      try:
        oraoems.execone(updsql)
        oraoems.commit()
        #pass
      except Exception, msg:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+'] Except: Unable to insert OEMS_TICKETS_LOG (LOG)'+str(msg)
    else: #初次異常
      p_reason = "SVIP CM Ping loss"
      updsql = "begin insert into oems_tickets_main (status,type,subtype,reason,descr,create_date,operator,account,location,normal_flag,impact_list) values ('5120','3111','311106','%s','%s',sysdate,%s,'SVIP_CM','%s','A','%s') return to_char(sid) into :1 ; end;" % (p_reason,p_descr,operator,companyno,subsid)
      print updsql
      try:
        #pass
        oems_sid_ary = oraoems.db.BindingArray(1,12,'SQLT_STR')
        oraoems.c.execute(updsql, oems_sid_ary)
        oraoems.commit()
        oems_id = int(oems_sid_ary[0])
        #pass
      except Exception, msg:
        print 'Exception: Unable to insert OEMS_TICKETS_MAIN (NEW)'+str(msg)
  else:
    pass      
  return    

oraoems = ORA('oems@kbro_nmsdb')
so_mapping = {}
SQL = "select subtype,id from oems_mapping where type = 'OPERATOR' and subtype is not null"
rst = oraoems.execall(SQL)
if rst is not None and len(rst) > 0:
  for az in rst:
    try:
      so_mapping[az[0]] = int(az[1])
    except Exception, msg:
      nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
      print '['+nowdate+'] Except: OEMS_MAPPING '+str(msg)
        
duration = 60*5
startime = time.time()

while 1:
  nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
  print '====',nowdate,'===='
  oracnis = ORA('nms@cnis')
  if not oracnis.db:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Error: Unable to connect to server [CNIS]'
    sys.exit(0)
  
  subsid_ip = {}
  #subsid_ary = [1797645,1797639,1797643,1797647,1797648,1797649,1797650,1797651,9150076,15044550]
  subsid_ary = {}
  subsid_ary[1797645] = 104
  subsid_ary[1797639] = 104
  subsid_ary[1797643] = 104
  subsid_ary[1797647] = 104
  subsid_ary[1797648] = 104
  subsid_ary[1797649] = 104
  subsid_ary[1797650] = 104
  #subsid_ary[1797651] = 104
  subsid_ary[9150076] = 220
  #subsid_ary[15044550] = 240
  
  cnt = 0;
  
  SQL = "select subsid,mac,ip,stopyn,companyno from cnr_fixip_coss where subsid in ('1797645','1797639','1797643','1797647','1797648','1797649','1797650','9150076') and stopyn = 'N'"
  print SQL
  rst = oracnis.execall(SQL)
  if rst is not None and len(rst)>0:
      for aw in rst:
          try:
            if aw[3] == 'N':
              subsid_ip[str(int(aw[0]))+'_IP'] = aw[2]
              subsid_ip[str(int(aw[0]))+'_SO'] = aw[4]
              cnt = cnt+1
          except Exception, msg:
              nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
              print '['+nowdate+'] Except: SVIP_FIXIP '+str(msg)
  
  
  
  if not oraoems.db:
      nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
      print '['+nowdate+'] Error: Unable to connect to server [OEMS]'
      sys.exit(0)
  
  
  oems = {}
  thread_arr = {}
  SQL = "select sid,impact_list from oems_tickets_main where account='SVIP_CM' and close_date is null and normal_flag in ('A') and subtype in ('311106') and status not in ('5029','5125')"
  print SQL
  rst = oraoems.execall(SQL)
  if rst is not None and len(rst) > 0:
    for aw in rst:
      try:
        oems[aw[1]] = int(aw[0])
      except Exception, msg:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+'] Except: OEMS_TICKETS_MAIN '+str(msg)
  print 'OEMS:',oems
  
  for x in subsid_ary:
    try:
      ipstr = str(x)+'_IP'
      #if subsid_ip[str(x)+'_IP'] is not None or subsid_ip[str(x)+'_IP'] == '':
      if ipstr in subsid_ip:
        total = 0
        rtt = -1
        loss_cnt=0
        while total < 5:
          out = os.popen("ping -c 3 -w 5 " + subsid_ip[str(x)+'_IP'] + " | grep 'rtt' | cut -d '=' -f 2 | cut -d '/' -f 2")
          for line in out.readlines():
            rtt = line.strip()
            
          if float(rtt) > 5000 or float(rtt) == -1:
            print x,':Timeout'
            loss_cnt = loss_cnt+1
          else:
            print x,':OK'
            total = 5
          total = total+1
        if loss_cnt >= 5:
          to_oems(x,str(subsid_ip[str(x)+'_IP']),'pingloss')      
      else:
        print x,'No Value'
        to_oems(x,'','novalue')
    except Exception, msg:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+'] Except: Ping '+str(msg)
  
  endtime = time.time()
  nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
  print "[%s] END (totalsec: %d)\n" % (nowdate, endtime-startime)
  sys.stdout.flush()
          
  # 等待到五分鐘才可再繼續執行
  while (endtime-startime) < duration:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print "[%s] WAIT 60 seconds %d %d %d (%d)" % (nowdate, endtime, startime, endtime-startime, duration)
    sys.stdout.flush()
    time.sleep(60)
    endtime = time.time()
  nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
  startime = time.time()
  print "[%s] NEXT" % (nowdate)
  
if oracnis:
    oracnis.se_close()
if oraoems:
    oraoems.se_close()

sys.exit(0)
