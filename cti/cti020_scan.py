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
where flag in (1,2,5) and companyno is not null %s and subsid is not null and (coss_status is null or coss_status not in ('CLOSE','CANCEL')) and coss_id is not null and instime >= to_date('20130401','YYYYMMDD') and instime >= sysdate-30" % (sosql)
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
              if upd_str != coss_status or coss_status is None or coss_status == '':
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
              oracon.execone(oraupdsql)
              oracon.commit()

              if mso != 'TFM':
                  oraupdsql = "begin sp_coss_oems_postback@cti_icare('%d','%s','%s',%s,'%s'); end;" % (cti_id, cti_flag, mscomment, ftime_sql, executor)
                  print oraupdsql
                  sys.stdout.flush()
                  oracon.execone(oraupdsql)
                  oracon.commit()

          if mso != 'TFM' and flag == 1:
              ctisql = "select callin_history_id from qam_info@cti_icare where callin_history_id=%d" % (cti_id)
              rs_one = oracon.execall(ctisql)
              if rs_one is None or len(rs_one) == 0:
                  oraupdsql = "insert into qam_info@cti_icare (callin_history_id,updatetime,so,subsid,coss_id,finishtime,cleancause,backcause,backcause1,sheetstatus) values(%d,sysdate,'%s',%d,'%s',%s,'%s','%s','%s','%s')" % (cti_id,so,subsid,coss_id,ftime_sql,mscomment,bc,bc1,upd_str)
              else:
                  oraupdsql = "update qam_info@cti_icare set finishtime=%s,cleancause='%s',backcause='%s',backcause1='%s',sheetstatus='%s' where callin_history_id=%d" % (ftime_sql,mscomment,bc,bc1,upd_str,cti_id)
              print oraupdsql
              sys.stdout.flush()
              oracon.execone(oraupdsql)
              oracon.commit()
      except Exception, msg:
          print 'Error:',msg
          sys.stdout.flush()
          #continue


tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print 'TIME:',tme

#REGEXP_LIKE(bandwidth, '^[0-9]{1,3}K/[0-9]{1,3}(M|K)$')

print 'FLAG=1,3,6 update status from OEMS'
fdsql = "select flag,companyno,subsid,cti_id, \
case \
  when oems_id > 80000000000 and oems_id < 90000000000 then oems_id-80000000000 \
  when oems_id > 70000000000 and oems_id < 80000000000 then oems_id-70000000000 \
  when oems_id > 60000000000 and oems_id < 70000000000 then oems_id-60000000000 \
  else oems_id \
end oems_id,oems_status from cti020 \
where flag in (1,3,6) and companyno is not null %s and subsid is not null and oems_id > 0 and oems_id < 80000000000 and (oems_status is null or oems_status not in ('作廢','取消','結案')) and instime >= to_date('20130401','YYYYMMDD') and instime >= sysdate-30" % (sosql)
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
          oems_status = a_row[5]
          if oems_status is None:
              oems_status = ''
          print 'CTI_ID:',cti_id,'[',flag,']',so,',',subsid,',',oems_id,',',oems_status
          sys.stdout.flush()
          if oems_id == 0:
              print 'except: oems_id=0 <PASS>'
              continue
          if oems_id > 80000000000 and oems_id < 90000000000:
               oems_id = oems_id - 80000000000
          if oems_id > 70000000000 and oems_id < 80000000000:
               oems_id = oems_id - 70000000000
          if oems_id > 60000000000 and oems_id < 70000000000:
               oems_id = oems_id - 60000000000

          if oems_id > 80000000000: # 8W 9W不回壓OEMS資料
              continue

          x_status = ''
          x_createdate_sql = x_closedate_sql = x_bgdate_sql = o_bgdate_sql = "to_date(NULL)"
          #0  normal_flag
          #1  normal_flag_str
          #2  create_date
          #3  impact_bg_date
          #4  close_date
          #5  status_name
          #6  type_name
          #7  subtype_name
          #8  qamtype_name
          #9  key_name
          #10 subkey_name
          #11 reason
          #12 descr
          #13 remarks
          cf_sql = "select normal_flag,normal_flag_str,to_char(create_date,'yyyy-mm-dd hh24:mi:ss') create_date,to_char(impact_bg_date,'yyyy-mm-dd hh24:mi:ss') impact_bg_date,to_char(close_date,'yyyy-mm-dd hh24:mi:ss') close_date,status_name,type_name,subtype_name,qamtype_name,key_name,subkey_name,reason,descr,remarks from v_oems_info where sid='%d'" % (oems_id)
          print cf_sql
          cf_rs = oracon_oems.execall(cf_sql)
          if cf_rs is not None and len(cf_rs) > 0:
              for cf_row in cf_rs:
                  x_flag = cf_row[0]
                  x_flag_str = cf_row[1]
                  x_createdate = cf_row[2]
                  if x_createdate is not None:
                      x_createdate_sql = "to_date('%s','yyyy-mm-dd hh24:mi:ss')" % (x_createdate)
                  x_bgdate = cf_row[3]
                  if x_bgdate is not None:
                      x_bgdate_sql = "to_date('%s','yyyy-mm-dd hh24:mi:ss')" % (x_bgdate)
                  if x_flag == 'Y':
                      o_bgdate_sql = x_bgdate_sql
                  else:
                      o_bgdate_sql = x_createdate_sql
                  x_closedate = cf_row[4]
                  if x_closedate is not None:
                      x_closedate_sql = "to_date('%s','yyyy-mm-dd hh24:mi:ss')" % (x_closedate)
                  x_status = cf_row[5]
                  x_type = cf_row[6]
                  if x_type is None:
                      x_type = ''
                  x_subtype = cf_row[7]
                  if x_subtype is None:
                      x_subtype = ''
                  x_qamtype = cf_row[8]
                  if x_qamtype is None:
                      x_qamtype = ''
                  x_key = cf_row[9]
                  if x_key is None:
                      x_key = ''
                  x_subkey = cf_row[10]
                  if x_subkey is None:
                      x_subkey = ''
                  x_reason = cf_row[11]
                  if x_reason is None:
                      x_reason = ''
                  x_descr = cf_row[12]
                  if x_descr is None:
                      x_descr = ''
                  x_remarks = cf_row[13]
                  if x_remarks is None:
                      x_remarks = ''

                  #OEMS工單種類 oems_normalflag
                  #OEMS狀態     oems_statusname
                  #OEMS結案日期 oems_closedate
                  #OEMS QAM分類 oems_qamtypename
                  #OEMS類別     oems_typename
                  #OEMS原因     oems_reason      => KEY + SUBKEY
                  #OEMS細分類   oems_subtypename
                  #OEMS說明     oems_descr
                  #OEMS補充     oems_remarks

                  #天然災害   374453 type=2104, subtype=104117  第一層會放在OEMS類別，第二層放在OEMS細分類 需改放在OEMS原因
                  #計畫性施工 372634 type=3001, subtype=7281    第一層會放在OEMS類別，第二層放在OEMS細分類 需改放在OEMS原因
                  #突發性障礙 372913 key=2104, sub_key=104999   會一起放在OEMS原因。請幫忙將障礙類別拆出來改放在OEMS類別(原本OEMS類別放的”事件主旨”資料不需要，原因保留在OEMS原因欄位上)
                  #單一事件   373299 key=3304, sub_key=104999   會一起放在OEMS原因。請幫忙將第一層原因拆出來改放在OEMS類別，原本OEMS類別放的”報修原因”請移到OEMS細分類，第二層原因保留在OEMS原因欄位上)

                  if x_flag == 'Y' or x_flag == 'N':
                    x_reason  = x_subtype
                    x_subtype = ''
                  elif x_flag == 'B':
                    x_type    = x_key
                    x_reason  = x_subkey
                  elif x_flag == 'U':
                    x_subtype = x_type
                    x_type    = x_key
                    x_reason  = x_subkey

                  break

          if x_status is not None and x_status != '' and len(x_status) > 0 and (x_status != oems_status or oems_status is None or oems_status == ''):
              x_type = x_type.strip()
              x_subtype = x_subtype.strip()
              x_qamtype = x_qamtype.strip()
              x_reason = x_reason.strip()
              x_descr = x_descr.strip()
              x_remarks = x_remarks.strip()

              oraupdsql = "update cti020 set oems_flag='%s',oems_status='%s',oems_bgdate=%s,oems_closedate=%s,oems_type='%s',oems_subtype='%s',oems_qamtype='%s',oems_reason='%s',oems_descr='%s',oems_remarks='%s',scantime=sysdate where companyno='%d' and cti_id='%d'" % (x_flag_str, x_status, o_bgdate_sql, x_closedate_sql, x_type, x_subtype, x_qamtype, x_reason, x_descr, x_remarks, so, cti_id)
              print oraupdsql
              sys.stdout.flush()
              oracon.execone(oraupdsql)
              oracon.commit()

      except Exception, msg:
          print 'Error:',msg
          sys.stdout.flush()


tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print 'TIME:',tme

print 'FLAG=1,3,6 update effect_type_belong (valid OEMS_ID & CLOSE)'
fdsql = "select flag,companyno,subsid,cti_id,oems_id,oems_status,case when oems_flag = '單一事件' then 'U' when oems_flag = '計畫性作業' then 'Y' when oems_flag = '突發性障礙' then 'B' when oems_flag = '天然災害' then 'N' end oems_flag,oems_type,oems_reason from cti020 \
where flag in (1,3,6) and companyno is not null %s and subsid is not null and ((oems_id >= 405000 and oems_id <= 9999999) or (oems_id >= 60000405000 and oems_id <= 60009999999) or (oems_id >= 70000405000 and oems_id <= 70009999999)) and \
oems_status in ('結案') and oems_type is not null and oems_reason is not null and effect_type is null and effect_belong is null and instime >= to_date('20130401','YYYYMMDD') and instime >= sysdate-30" % (sosql)
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
          oems_status = a_row[5]
          if oems_status is None:
              oems_status = ''
          oems_flag = a_row[6]
          if oems_flag is None:
              oems_flag = ''
          oems_type = a_row[7]
          if oems_type is not None and len(oems_type) > 0:
              oems_type = oems_type.strip()
          else:
              oems_type = ''
          oems_reason = a_row[8]
          if oems_reason is not None and len(oems_reason) > 0:
              oems_reason = oems_reason.strip()
          else:
              oems_reason = ''

          print 'CTI_ID:',cti_id,'[',flag,']',so,',',subsid,',',oems_id,',',oems_status,',',oems_flag,',',oems_type,',',oems_reason
          sys.stdout.flush()
          updsql = ''
          esql = "select event_type,event_belong from cticode2event where instr(upper(flag),upper('%s')) > 0 and upper(oems_type)=upper('%s') and upper(oems_reason)=upper('%s')" % (oems_flag, oems_type, oems_reason)
          print esql
          ers = oracon.execall(esql)
          if ers is not None and len(ers) > 0:
              for e_row in ers:
                  updsql = "update cti020 set effect_type='%s',effect_belong='%s' where companyno='%d' and cti_id='%d'" % (e_row[0], e_row[1], so, cti_id)
                  break

          if updsql is not None and len(updsql) > 0:
              print updsql
              oracon.execone(updsql)
              oracon.commit()
          sys.stdout.flush()
      except Exception, msg:
          print 'Error:',msg
          sys.stdout.flush()


tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print 'TIME:',tme

print 'FLAG=1,3,6 update effect_type_belong (valid OEMS_ID & CANCEL)'
fdsql = "select flag,companyno,subsid,servicename,cti_id,oems_id,oems_status,calltypelv3,calltypelv4,coss_id,coss_status,reply3 from cti020 \
where flag in (1,3,6) and companyno is not null %s and subsid is not null and ((oems_id >= 405000 and oems_id <= 9999999) or (oems_id >= 60000405000 and oems_id <= 60009999999) or (oems_id >= 70000405000 and oems_id <= 70009999999)) and \
oems_status in ('作廢','取消','退件') and (calltypelv3 is not null or reply3 is not null) and effect_type is null and effect_belong is null and instime >= to_date('20130401','YYYYMMDD') and instime >= sysdate-30" % (sosql)
print fdsql
rs = oracon.execall(fdsql)
if rs is not None and len(rs) > 0:
    for a_row in rs:
      try:
          flag = int(a_row[0])
          so = int(a_row[1])
          subsid = int(a_row[2])
          srvname = a_row[3]
          cti_id = int(a_row[4])
          oems_id = a_row[5]
          if oems_id is None:
              oems_id = 0
          oems_id = int(oems_id)
          oems_status = a_row[6]
          if oems_status is None:
              oems_status = ''
          calltypelv3 = a_row[7]
          if calltypelv3 is not None and len(calltypelv3) > 0:
              calltypelv3 = calltypelv3.strip()
          else:
              calltypelv3 = ''
          calltypelv4 = a_row[8]
          if calltypelv4 is not None and len(calltypelv4) > 0:
              calltypelv4 = calltypelv4.strip()
          else:
              calltypelv4 = ''
          coss_id = a_row[9]
          if coss_id is None:
              coss_id = ''
          coss_status = a_row[10]
          if coss_status is None:
              coss_status = ''
          reply3 = a_row[11]
          if reply3 is not None and len(reply3) > 0:
              reply3 = reply3.strip()
          else:
              reply3 = ''

          print 'CTI_ID:',cti_id,'[',flag,']',so,',',subsid,',',srvname,',',oems_id,',',oems_status,',',calltypelv3,',',calltypelv4,',',coss_id,',',coss_status,',',reply3
          sys.stdout.flush()
          esql = ''
          if flag == 1 and reply3 is not None and len(reply3) > 0:
              esql = "select effect_type,effect_belong from cticode2effect where flag=%d and instr(upper(servicename),upper('%s')) > 0 and upper(workcause)=upper('%s')" % (flag, srvname, reply3)
          if (flag == 3 or flag == 6) and calltypelv3 is not None and len(calltypelv3) > 0:
              if calltypelv4 is not None and len(calltypelv4) > 0:
                  esql = "select effect_type,effect_belong from cticode2effect where flag=%d and instr(upper(servicename),upper('%s')) > 0 and upper(workcause)=upper('%s') and upper(subcause)=upper('%s')" % (flag, srvname, calltypelv3, calltypelv4)
              else:
                  esql = "select effect_type,effect_belong from cticode2effect where flag=%d and instr(upper(servicename),upper('%s')) > 0 and upper(workcause)=upper('%s')" % (flag, srvname, calltypelv3)
          if esql is not None and len(esql) > 0:
              print esql
              updsql = ''
              ers = oracon.execall(esql)
              if ers is not None and len(ers) > 0:
                  for e_row in ers:
                      updsql = "update cti020 set effect_type='%s',effect_belong='%s' where companyno='%d' and cti_id='%d'" % (e_row[0], e_row[1], so, cti_id)
                      break

              if updsql is not None and len(updsql) > 0:
                  print updsql
                  oracon.execone(updsql)
                  oracon.commit()
          sys.stdout.flush()
      except Exception, msg:
          print 'Error:',msg
          sys.stdout.flush()


tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print 'TIME:',tme

print 'FLAG=1 update effect_type_belong (invalid OEMS_ID)'
fdsql = "select flag,companyno,subsid,servicename,cti_id,coss_id,coss_status,reply3,oems_id,oems_status from cti020 \
where flag=1 and companyno is not null %s and subsid is not null and coss_id is not null and coss_status='CLOSE' and reply3 is not null and \
(not ((oems_id >= 405000 and oems_id <= 9999999) or (oems_id >= 60000405000 and oems_id <= 60009999999) or (oems_id >= 70000405000 and oems_id <= 70009999999)) or oems_id is null) and \
effect_type is null and effect_belong is null and instime >= to_date('20130401','YYYYMMDD') and instime >= sysdate-30" % (sosql)
rs = oracon.execall(fdsql)
if rs is not None and len(rs) > 0:
    for a_row in rs:
      try:
          flag = int(a_row[0])
          so = int(a_row[1])
          subsid = int(a_row[2])
          srvname = a_row[3]
          cti_id = int(a_row[4])
          coss_id = a_row[5]
          if coss_id is None:
              coss_id = ''
          coss_status = a_row[6]
          if coss_status is None:
              coss_status = ''
          reply3 = a_row[7]
          if reply3 is not None and len(reply3) > 0:
              reply3 = reply3.strip()
          else:
              reply3 = ''
          oems_id = a_row[8]
          if oems_id is None:
              oems_id = 0
          oems_id = int(oems_id)
          oems_status = a_row[9]
          if oems_status is None:
              oems_status = ''

          print 'CTI_ID:',cti_id,'[',flag,']',so,',',subsid,',',srvname,',',coss_id,',',coss_status,',',reply3,',',oems_id,',',oems_status
          sys.stdout.flush()
          updsql = ''
          esql = "select effect_type,effect_belong from cticode2effect where flag=1 and instr(upper(servicename),upper('%s')) > 0 and upper(workcause)=upper('%s')" % (srvname, reply3)
          print esql
          ers = oracon.execall(esql)
          if ers is not None and len(ers) > 0:
              for e_row in ers:
                  updsql = "update cti020 set effect_type='%s',effect_belong='%s' where companyno='%d' and cti_id='%d'" % (e_row[0], e_row[1], so, cti_id)
                  break

          if updsql is not None and len(updsql) > 0:
              print updsql
              oracon.execone(updsql)
              oracon.commit()
          sys.stdout.flush()
      except Exception, msg:
          print 'Error:',msg
          sys.stdout.flush()


if time.strftime("%H", time.localtime()) == '08':
    tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print 'TIME:',tme

    print 'update SWVersion from COSS'
    fdsql = "select flag,companyno,subsid,cti_id,servicename,singlesn,smartcard,swversion,swversion2 from cti020 \
where companyno is not null %s and subsid is not null and substr(servicename,1,1) in ('2','3','5','7','8','9') and singlesn is not null and swversion is null and instime >= to_date('20130401','YYYYMMDD') and instime >= sysdate-7" % (sosql)
    print fdsql
    rs = oracon.execall(fdsql)
    if rs is not None and len(rs) > 0:
        for a_row in rs:
          try:
              flag = int(a_row[0])
              so = int(a_row[1])
              subsid = int(a_row[2])
              cti_id = int(a_row[3])
              singlesn = a_row[5]

              print 'CTI_ID:',cti_id,'[',flag,']',so,',',subsid,',',singlesn
              sys.stdout.flush()

              qrysql = "select companyno,subsid,servicename,singlesn,smartcard,swversion,swversion2 from ms0200 with (nolock) where companyno='%d' and subsid='%d' and singlesn='%s'" % (so, subsid, singlesn)
              print qrysql
              cur.execute(qrysql)
              xarr = cur.fetchone()
              if xarr is not None:
                  swversion = xarr[5]
                  if swversion is None:
                      swversion = ''
                  swversion2 = xarr[6]
                  if swversion2 is None:
                      swversion2 = ''

                  if swversion is not None and swversion != '' and len(swversion) > 0:
                      oraupdsql = "update cti020 set swversion='%s',swversion2='%s' where companyno='%d' and cti_id='%d'" % (swversion, swversion2, so, cti_id)
                      print oraupdsql
                      oracon.execone(oraupdsql)
                      oracon.commit()
              sys.stdout.flush()
          except Exception, msg:
              print 'Error:',msg
              sys.stdout.flush()


if oracon is not None:
    oracon.se_close()
#if oracon_cti is not None:
#    oracon_cti.se_close()
if oracon_oems is not None:
    oracon_oems.se_close()
con.close()

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print 'END TIME:',tme
