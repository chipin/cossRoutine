#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# 60000突發告警單, 70000手開單
# 80000震江工單回填OEMS_ID正確, 90000震江工單回填OEMS_ID不正確
import os,sys,string,time
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv) != 2:
    print 'usage:',sys.argv[0],'[KBRO | CG | TFM]'
    sys.exit(0)

mso = sys.argv[1].upper()

if mso != 'TFM' and mso != 'KBRO' and mso != 'CG':
    print 'usage:',sys.argv[0],'[KBRO | CG | TFM]'
    sys.exit(0)

sosql = ''
try:
    if mso == 'CG':
        con = pymssql.connect(host='CGCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb_cg')
        sosql = "and companyno='106'"
    elif mso == 'TFM':
        con = pymssql.connect(host='TFMCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
        sosql = "and companyno in ('101','103','104','300','701')"
    else:
        con = pymssql.connect(host='kbroCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
        sosql = "and companyno not in ('106','101','103','104','300','701')"
    cur = con.cursor()
except Exception, errmesg:
    print 'Error:',errmesg
    sys.exit(0)

if sosql is None or len(sosql) <= 0:
    print 'Error: Unknown MSO'
    sys.exit(0)

oracon = ORA('CTI@CNIS')
if not oracon.db:
    sys.exit(0)

oracon_oems = ORA('OEMS@KBRO_NMSDB')
if not oracon_oems.db:
    sys.exit(0)

#oracon_cti = ORA('ICARE/ICARE@CTI')
#if not oracon_cti.db:
#    sys.exit(0)

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print 'START TIME:',tme

so_name = {}
oraqrysql = "select name,id from oems_mapping where type='OPERATOR' and name is not null and rank > 0"
rs = oracon_oems.execall(oraqrysql)
if rs is not None and len(rs) > 0:
    for a_row in rs:
       so_name[int(a_row[0])] = a_row[1]

print 'FLAG=1,2,5 update status from COSS'
fdsql = "select flag,companyno,subsid,cti_id,oems_id,coss_id,coss_status from cti020 \
        where flag in (1,2,5) and companyno is not null  %s  and subsid is not null  and instime >= to_date('2019/03/04 00:00:00','YYYY/MM/DD HH24:MI:SS') and instime <= to_date('2019/03/04 23:59:59','YYYY/MM/DD HH24:MI:SS') and subsid in ('15034473','1968378','1922899','15131118','1922849','1928356','1980019','15020787','1928356')  " % (sosql) 
print fdsql
rs = oracon.execall(fdsql)
if rs is not None and len(rs) > 0:
    for a_row in rs:
      try:
          flag = int(a_row[0])
          so = int(a_row[1])
          subsid = int(a_row[2])
          cti_id = int(a_row[3])
          oems_id = a_row[4]
          if oems_id is None:
              oems_id = 0
          oems_id = int(oems_id)
          coss_id = a_row[5]
          coss_status = a_row[6]
          if coss_status is None:
              coss_status = ''

          print 'CTI_ID:',cti_id,'[',flag,']',so,',',subsid,',',coss_id,',',coss_status,',',oems_id
          #qrysql = "select a.sheetstatus,a.finishdate,a.cleancause,a.cleanname,a.backcause,a.backcause1,convert(varchar(19),a.cleandate,20) cleandate,convert(varchar(19),a.finishtime,20) finishtime,worknum,convert(varchar(19),a.bookdate,20) bookdate,msremark,a.singlesn,convert(varchar(19),a.createtime,20) createtime,a.servicename,a.orgsinglesn,a.orgsmartcard,a.orgswversion from ms0301 a with (nolock) inner join ms0300 b with (nolock) on b.companyno=a.companyno and b.worksheet=a.worksheet where a.companyno='%d' and a.worksheet='%s'" % (so, coss_id)
          qrysql = "select a.sheetstatus,a.finishdate,a.cleancause,a.worker1,a.backcause,a.backcause1,convert(varchar(19),a.cleandate,20) cleandate,convert(varchar(19),a.finishtime,20) finishtime,worknum,convert(varchar(19),a.bookdate,20) bookdate,msremark,a.singlesn,convert(varchar(19),a.createtime,20) createtime,a.servicename,a.orgsinglesn,a.orgsmartcard,a.orgswversion from ms0301 a with (nolock) inner join ms0300 b with (nolock) on b.companyno=a.companyno and b.worksheet=a.worksheet where a.companyno='%d' and a.worksheet='%s'" % (so, coss_id)
          print qrysql
          sys.stdout.flush()
          cur.execute(qrysql)
          xarr = cur.fetchone()
          upd_flag = 0
          cti_flag = ''
          bc = bc1 = mscomment = finish_remark = executor = orgsinglesn = orgsmartcard = orgswversion = ''
          ftime_sql = "to_date(NULL)"
          bookdate_sql = "to_date(NULL)"
          chg_book_cnt = 0
          #singlesn = ''
          ctime_sql = "to_date(NULL)"
          if xarr is None:
              qrysql = "select worksheet,caseclose,mscomment,executor,convert(varchar(19),updatetime,20) ftime,msremark from ms0310 with (nolock) where companyno='%d' and worksheet='%s'" % (so, coss_id)
              print qrysql
              sys.stdout.flush()
              cur.execute(qrysql)
              xarr = cur.fetchone()
              p_coss_id = ''
              if xarr is not None:
                  p_coss_id = xarr[0]
                  caseclose = xarr[1]
                  finish_remark = xarr[2]
                  #marked by swallow 2014.11.13 結案人員改為工程人員
                  #executor = xarr[3]
                  #if executor is None:
                  #    executor = ''
                  mscomment = xarr[5]
                  #msremark = xarr[5]
                  #mscomment = msremark
                  if mscomment is not None:
                      mscomment = string.replace(mscomment,"'","_")
                      mscomment = string.replace(mscomment,'"',"_")
                      mscomment = mscomment.strip()
                  else:
                      mscomment = ''
                  ftime = xarr[4]
                  if ftime is not None:
                      ftime_sql = "to_date('%s','yyyy-mm-dd hh24:mi:ss')" % (ftime)
                  else:
                      ftime_sql = "to_date(NULL)"
                  if caseclose=='Y':
                      upd_flag = 1
                      upd_str = 'CLOSE'
                      cti_flag = '3'
                  if p_coss_id=='':
                      upd_flag = 1
                      upd_str = 'CLOSE'
                      cti_flag = '3'
                      #msremark = '無資料'
                      #mscomment = '無資料'
              else:
                  upd_flag = 1
                  upd_str = 'CLOSE'
                  cti_flag = '3'
                  #msremark = '無資料'
                  #mscomment = '無資料'
          else:
              upd_str = xarr[0]
              if upd_str[:1]=='A':
                  upd_str = 'CANCEL'
                  cti_flag = '3'
              elif upd_str[:1]=='4' and xarr[1] is not None and xarr[1]!='':
                  upd_str = 'CLOSE'
                  cti_flag = '3'
              elif upd_str is not None:
                  pass
              else:
                  upd_str = 'CANCEL'
                  cti_flag = '3'
              
              upd_flag = 1
              mscomment = xarr[2]
              if mscomment is not None:
                  mscomment = string.replace(mscomment,"'","_")
                  mscomment = string.replace(mscomment,'"',"_")
                  mscomment = mscomment.strip()
              else:
                  mscomment = ''
              executor = xarr[3]
              if executor is None:
                  executor = ''
              bc = xarr[4]
              if bc is not None:
                  bc = string.replace(bc,"'","_")
                  bc = string.replace(bc,'"',"_")
                  bc = bc.strip()
              else:
                  bc = ''
              bc1 = xarr[5]
              if bc1 is not None:
                  bc1 = string.replace(bc1,"'","_")
                  bc1 = string.replace(bc1,'"',"_")
                  bc1 = bc1.strip()
              else:
                  bc1 = ''
              ctime = xarr[6]
              if ctime is not None:
                  ctime_sql = "to_date('%s','yyyy-mm-dd hh24:mi:ss')" % (ctime)
              else:
                  ctime_sql = "to_date(NULL)"
              ftime = xarr[7]
              if ftime is not None:
                  ftime_sql = "to_date('%s','yyyy-mm-dd hh24:mi:ss')" % (ftime)
              else:
                  ftime_sql = "to_date(NULL)"
              srvname = xarr[13]
              orgsinglesn = xarr[14]
              if orgsinglesn is None:
                  orgsinglesn = ''
              orgsmartcard = xarr[15]
              if orgsmartcard is None:
                  orgsmartcard = ''
              orgswversion = xarr[16]
              if orgswversion is None:
                  orgswversion = ''

              if oems_id == 0:
                  try:
                      oems_id = int(xarr[8])
                      cf_sql = "select a.sid from oems_impact_subscrid a \
inner join ( \
  select sid from oems_tickets_main where sid='%d' and status not in ('5029','5125') \
  union \
  select sid from oems_tickets_main where owner=(select owner from oems_tickets_main where sid='%d') and status not in ('5029','5125') \
) b on b.sid=a.sid \
where a.companyno='%d' and a.subsid='%d' and a.impact='Y' order by a.sid desc" % (oems_id, oems_id, so, subsid)
                      print cf_sql
                      sys.stdout.flush()
                      oems_id = oems_id+90000000000
                      cf_rs = oracon_oems.execall(cf_sql)
                      if cf_rs is not None and len(cf_rs) > 0:
                          for cf_row in cf_rs:
                              oems_id = int(cf_row[0])+80000000000
                              print '8W:',oems_id
                              break
                  except:
                      print 'except: oems_id=0'
                      sys.stdout.flush()
                      wrkctime = xarr[12]
                      cf_sql = "select a.sid from oems_impact_subscrid a \
inner join oems_tickets_main b on b.sid=a.sid and b.operator='%d' and b.normal_flag='Y' and b.status in (5008,5013,5018,5020) and b.close_date is null and to_date('%s','YYYY-MM-DD HH24:MI:SS') between b.impact_bg_date and b.impact_end_date \
where a.companyno='%d' and a.subsid='%d' and a.impact='Y' \
union \
select a.sid from oems_impact_subscrid a \
inner join oems_tickets_main b on b.sid=a.sid and b.operator='%d' and b.normal_flag='B' and b.status in (5100,5101,5102,5103,5104) and b.type='3103' and b.close_date is null and b.create_date >= sysdate-7 and b.create_date <= to_date('%s','YYYY-MM-DD HH24:MI:SS')+(30/1440) \
where a.companyno='%d' and a.subsid='%d' and a.impact='Y' \
union \
select a.sid from oems_impact_subscrid a \
inner join oems_tickets_main b on b.sid=a.sid and b.operator='%d' and b.normal_flag='N' and b.status in (5100,5101,5102,5103,5104) and b.close_date is null and b.create_date >= sysdate-7 and b.create_date <= to_date('%s','YYYY-MM-DD HH24:MI:SS')+(30/1440) \
where a.companyno='%d' and a.subsid='%d' and a.impact='Y' \
order by sid desc" % (so_name[so], wrkctime, so, subsid, so_name[so], wrkctime, so, subsid, so_name[so], wrkctime, so, subsid)
                      print cf_sql
                      sys.stdout.flush()
                      cf_rs = oracon_oems.execall(cf_sql)
                      if cf_rs is not None and len(cf_rs) > 0:
                          for cf_row in cf_rs:
                              oems_id = int(cf_row[0])+70000000000
                              print '7W:',oems_id
                              sys.stdout.flush()
                              break
              if oems_id == 0:
                  cf_sql = "select a.sid from oems_impact_subscrid a \
inner join oems_tickets_main b on b.sid=a.sid and b.operator='%d' and b.normal_flag='B' and b.status in (5100,5101,5102,5103,5104) and b.account='COSSv2' and b.type='3107' and b.subtype in (310701,310703) and b.close_date is null and b.create_date >= sysdate-7 and b.create_date <= to_date('%s','YYYY-MM-DD HH24:MI:SS') \
where a.companyno='%d' and a.subsid='%d' and a.impact='Y' order by a.sid desc" % (so_name[so], wrkctime, so, subsid)
                  print cf_sql
                  sys.stdout.flush()
                  cf_rs = oracon_oems.execall(cf_sql)
                  if cf_rs is not None and len(cf_rs) > 0:
                      for cf_row in cf_rs:
                          oems_id = int(cf_row[0])+60000000000
                          print '6W:',oems_id
                          sys.stdout.flush()
                          break

              bookdate = xarr[9]
              if bookdate is not None:
                  bookdate_sql = "to_date('%s','yyyy-mm-dd hh24:mi:ss')" % (bookdate)
                  upd_flag = 1
              else:
                  bookdate_sql = "to_date(NULL)"

              finish_remark = xarr[10]
              finish_remark = finish_remark.replace('--','')
              finish_remark = finish_remark.replace('\'','')
              #singlesn = xarr[11]
              book_sql = "select chtimes from ms03011 a with (nolock) where a.companyno='%d' and a.worksheet='%s'" % (so, coss_id)
              print book_sql
              sys.stdout.flush()
              cur.execute(book_sql)
              book_arr = cur.fetchone()
              if book_arr is not None and len(book_arr) > 0:
                  chg_book_cnt = int(book_arr[0])

          if upd_flag == 1:
              effect_sql = ''
              if flag == 1 and upd_str == 'CLOSE' and bc1 is not None and len(bc1) > 0:
                  esql = "select oper_type,oper_belong from cticode2effect where flag=1 and instr(upper(servicename),upper('%s')) > 0 and upper(workcause)=upper('%s')" % (srvname, bc1)
                  print esql
                  sys.stdout.flush()
                  ers = oracon.execall(esql)
                  if ers is not None and len(ers) > 0:
                      for e_row in ers:
                          effect_sql = ",oper_type='%s',oper_belong='%s'" % (e_row[0], e_row[1])
                          break
              reply_sql  = "reply1='%s',reply2='%s',reply3='%s',reply4='%s'" % (mscomment, bc, bc1, finish_remark)
              if flag == 1 and upd_str == 'CLOSE':
                  reply_sql = "reply1='%s',reply2='%s',reply3='%s',reply4='%s'" % (bc, mscomment, bc1, finish_remark)
              if flag == 1 and upd_str == 'CANCEL':
                  reply_sql  = "reply1='%s',reply2='%s',reply3='%s',reply4='%s'" % (mscomment, bc1, bc, finish_remark)
                  #effect_sql = ",oper_type='取消(其它)',oper_belong='用戶行為'"
              if oems_id <= 0:
                  oems_id = ''
              oraupdsql = "update cti020 set coss_status='%s',%s,finishdate=%s,oems_id='%s',last_bookdate=%s,chg_bookcnt='%d',scantime=sysdate,worker='%s',cleandate=%s,orgsinglesn='%s',orgsmartcard='%s',orgswversion='%s' %s where companyno='%d' and cti_id='%d'" % (upd_str, reply_sql, ftime_sql, oems_id, bookdate_sql, chg_book_cnt, executor, ctime_sql, orgsinglesn, orgsmartcard, orgswversion, effect_sql, so, cti_id)
              print oraupdsql
              sys.stdout.flush()
              #oracon.execone(oraupdsql)
              #oracon.commit()

             

          
      except Exception, msg:
          print 'Error:',msg
          sys.stdout.flush()
          #continue

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print 'TIME:',tme

#REGEXP_LIKE(bandwidth, '^[0-9]{1,3}K/[0-9]{1,3}(M|K)$')


if oracon is not None:
    oracon.se_close()
#if oracon_cti is not None:
#    oracon_cti.se_close()
if oracon_oems is not None:
    oracon_oems.se_close()
con.close()

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print 'END TIME:',tme
