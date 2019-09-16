#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# 2015/03/01停止IVR通知
# 2015/04/01停止SMS通知(TFM,YMS,NTY)
# 2015/05/01停止SMS通知(全區)
import os,sys,time,re
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'


if len(sys.argv) != 2:
    print 'usage:',sys.argv[0],'[TFM|KBRO|CG]'
    sys.exit(0)
else:
    so = sys.argv[1].upper()

if so == 'CG':
    sosql = "'106'"
    db_host = 'CossMS_CG'
elif so == 'TFM':
    sosql = "'101','103','104','300','701'"
    db_host = 'TFMCossMS'
elif so == 'KBRO':
    sosql = "'210','220','230','240','250','260','310','330','410','420','610','810','820'"
    db_host = 'kbroCossMS'
else:
    print 'usage:',sys.argv[0],'[TFM|KBRO|CG]'
    sys.exit(0)

if db_host == 'TFMCossMS':
    oracoss = ORA('coss@cnis')
    if not oracoss.db:
        print 'Error: Unable to connect to [COSS@CNIS]'
        sys.exit(0)
else:
    oracoss = ORA('coss@kbro_nmsdb')
    if not oracoss.db:
        print 'Error: Unable to connect to [COSS@KBRO_NMSDB]'
        sys.exit(0)


nowtime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] START" % (nowtime)

ora = ORA('nms@cnis')
if not ora.db:
    print 'Error: Unable to connect to [NMS@CNIS]'
    sys.exit(0)

so_info = {}
so_name = {}
so_print = {}
so_sender = {}

SQL = "select companyno,fullname,soname,printname,email_sender from so"
print SQL
rst = ora.execall(SQL)
if rst is not None and len(rst) > 0:
    for aw in rst:
        try:
            so_info[aw[0]] = aw[1]
            so_name[aw[0]] = aw[2]
            so_print[aw[0]] = aw[3]
            so_sender[aw[0]] = aw[4]
        except Exception, msg:
            print 'Except:',str(msg)

ora.se_close()

if len(so_info) == 0:
    print 'Error: SO is empty [CNIS]'
    sys.exit(0)


if so != 'CG':
    qrySQL = "begin proc_upd_invoice_status; end;"
    print qrySQL
    sys.stdout.flush()
    oracoss.execone(qrySQL)
    oracoss.commit()





# Send to COSS BEGIN
try:
    con = pymssql.connect(host=db_host,user=cossdb.account,password=cossdb.passwd,database='cossdb')
    cur = con.cursor()
except Exception, msg:
    print 'Error: Unable to connect to ['+db_host+']'
    sys.exit(0)

qrySQL = "select sid,so,subsid,invoice,email_status,sms_status,ivr_status,to_char(email_sendtime,'yyyy-mm-dd hh24:mi:ss') emailtime,to_char(sms_sendtime,'yyyy-mm-dd hh24:mi:ss') smstime,to_char(ivr_sendtime,'yyyy-mm-dd hh24:mi:ss') ivrtime from invoice_status where coss_flag='N' and (coss_updtime is null or coss_updtime<sysdate-0.5) and so in (%s) and createtime > to_date('2017/12/13','YYYY/MM/DD')" % (sosql)
print qrySQL
sys.stdout.flush()
o_rs = oracoss.execall(qrySQL)
if o_rs != None and len(o_rs) > 0:
    commit_loop = 0
    for o_row in o_rs:
        p_sid = int(o_row[0])
        p_so = o_row[1]
        p_subsid = int(o_row[2])
        p_invoice = o_row[3]
        p_email = o_row[4]
        p_sms = o_row[5]
        p_ivr = o_row[6]
        p_emailtime = o_row[7]
        p_smstime = o_row[8]
        p_ivrtime = o_row[9]

        nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if p_emailtime is None or p_emailtime=='':
            p_emailtime = nowtime
        if p_smstime is None or p_smstime=='':
            p_smstime = nowtime
        if p_ivrtime is None or p_ivrtime=='':
            p_ivrtime = nowtime

        mSQL = updSQL = ''
        if (p_email=='NO' and p_sms=='NO' and p_ivr=='NO') or (p_email=='SKIP' and p_sms=='SKIP' and p_ivr=='SKIP'):
            mSQL = "update ms4000 set invtextpath='不通知',invtexttime='%s' where companyno='%s' and subsid=%d and invoice='%s'" % (nowtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='不通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email in ['SKIP','FAIL','NO'] and p_sms in ['SKIP','FAIL','NO'] and p_ivr in ['SKIP','FAIL','NO']:
            mSQL = "update ms4000 set invtextpath='通知失敗',invtexttime='%s' where companyno='%s' and subsid=%d and invoice='%s'" % (nowtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='通知失敗',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email=='SENT' and p_sms=='OK' and p_ivr=='OK':
            mSQL = "update ms4000 set invtextpath='完成EMAIL&簡訊&電話語音通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_ivrtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成EMAIL&簡訊&電話語音通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email=='SENT' and p_sms=='OK' and p_ivr in ['SKIP','FAIL','NO']:
            mSQL = "update ms4000 set invtextpath='完成EMAIL&簡訊通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_smstime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成EMAIL&簡訊通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email=='SENT' and p_sms in ['SKIP','FAIL','NO'] and p_ivr=='OK':
            mSQL = "update ms4000 set invtextpath='完成EMAIL&電話語音通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_ivrtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成EMAIL&電話語音通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email in ['SKIP','FAIL','NO'] and p_sms=='OK' and p_ivr=='OK':
            mSQL = "update ms4000 set invtextpath='完成簡訊&電話語音通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_ivrtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成簡訊&電話語音通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email=='OK' and p_sms in ['SKIP','FAIL','NO'] and p_ivr in ['SKIP','FAIL','NO']:
            mSQL = "update ms4000 set invtextpath='完成EMAIL通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_emailtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成EMAIL通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email in ['SKIP','FAIL','NO'] and p_sms=='OK' and p_ivr in ['SKIP','FAIL','NO']:
            mSQL = "update ms4000 set invtextpath='完成簡訊通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_smstime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成簡訊通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email in ['SKIP','FAIL','NO'] and p_sms in ['SKIP','FAIL','NO'] and p_ivr=='OK':
            mSQL = "update ms4000 set invtextpath='完成電話語音通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_ivrtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成電話語音通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        if mSQL!='':
            print mSQL
            try:
                cur.execute(mSQL)
                pass
            except Exception, msg:
                print 'Except:',str(msg)
        if updSQL!='':
            print updSQL
            try:
                oracoss.execone(updSQL)
                pass
            except Exception, msg:
                print 'Except:',str(msg)
        commit_loop = commit_loop+1
        if (commit_loop%30)==0:
            con.commit()
            oracoss.commit()
        sys.stdout.flush()
    con.commit()
    oracoss.commit()
# Send to COSS END

con.close()
oracoss.se_close()

nowtime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] END" % (nowtime)
