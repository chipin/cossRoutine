#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

def append_lac(xso, xtel):
    if xtel is None or xtel=='':
        return ''
    xtel = xtel.replace("*","")
    if xso=='101' or xso=='103' or xso=='104':
        return xtel
    elif xso=='300':
        lac = '03'
    elif xso=='701':
        lac = '07'
    else:
        lac = '02'
    return '%s%s' % (lac, xtel)

def get_email_status(inv, ora):
    SQL = "select sid,status,to_char(status_date,'yyyy-mm-dd hh24:mi:ss') status_date,seq from oss_mail_invoice where invoice='%s'" % (inv)
    o_rs = ora.execall(SQL)
    xid = -1
    if o_rs != None and len(o_rs) > 0:
        for o_row in o_rs:
            xid = int(o_row[0])
            xstatus = o_row[1]
            real_sendtime = o_row[2]
    if xid<0:
        return 'SKIP',''
    elif xstatus=='OK':
        return 'OK',real_sendtime
    elif xstatus=='ERROR':
        return 'FAIL',''
    return None,''

def get_sms_status(inv, ora):
    SQL = "select sid,sent,to_char(real_sendtime,'yyyy-mm-dd hh24:mi:ss') real_sendtime,round(sysdate-real_sendtime,0) sent_day from sms_invoice where invoice='%s'" % (inv)
    o_rs = ora.execall(SQL)
    xid = -1
    if o_rs != None and len(o_rs) > 0:
        for o_row in o_rs:
            xid = int(o_row[0])
            xsent = o_row[1]
            real_sendtime = o_row[2]
            sent_day = int(o_row[3])
    if xid<0:
        return 'SKIP',''
    elif xsent=='DELIVRD' or xsent=='ACCEPTED':
        return 'OK',real_sendtime
    elif xsent=='EXPIRED' or sent_day>3:
        return 'FAIL',''
    return None,''

def get_ivr_status(inv, ora):
    SQL = "select sid,status,to_char(updatetime,'yyyy-mm-dd hh24:mi:ss') updatetime,redial from cti.v_cti_invoice_notify where invoice='%s'" % (inv)
    o_rs = ora.execall(SQL)
    xid = -1
    if o_rs != None and len(o_rs) > 0:
        for o_row in o_rs:
            xid = int(o_row[0])
            xstatus = o_row[1]
            real_sendtime = o_row[2]
            redial = int(o_row[3])
    if xid<0:
        return 'SKIP',''
    elif xstatus=='1':
        return 'OK',real_sendtime
    elif xstatus=='-1' and redial>=3:
        return 'FAIL',''
    return None,''

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print '['+nowdate+'] START'

func = 'CHECK'
db_host = "TFMCossMS"
if len(sys.argv)<2:
    sosql = "'101','103','104','300','701'"
else:
    if len(sys.argv)>2:
        func = sys.argv[2]
    sosql = "'%s'" % (sys.argv[1])

yymmdd = time.strftime("%Y%m%d", time.localtime())
year = int(yymmdd[:4])
month = int(yymmdd[4:6])
day = int(yymmdd[6:8])
ydate = time.localtime(time.mktime((year,month,day,0,0,0,-1,-1,-1))-86400*23)
target_day = "%d/%.2d/%.2d" % (ydate[0], ydate[1], ydate[2])
ydate = time.localtime(time.mktime((year,month,day,0,0,0,-1,-1,-1)))
target_day_end = "%d/%.2d/%.2d" % (ydate[0], ydate[1], ydate[2])
ydate = time.localtime(time.mktime((year,month,day,12,0,0,-1,-1,-1))+86400)
sms_day = "%d/%.2d/%.2d %.2d:%.2d:%.2d" % (ydate[0], ydate[1], ydate[2], ydate[3], ydate[4], ydate[5])

print target_day,target_day_end

con = pymssql.connect(host=db_host,user=cossdb.account,password=cossdb.passwd,database='cossdb')
cur = con.cursor()

oracon = ORA('coss@cnis')
SQL = "select companyno,fullname,soname,printname from nms.so"
so_info = {}
so_name = {}
so_printname = {}
for i in range(0, 3):
    try:
        rst = oracon.execall(SQL)
        break
    except Exception, msg:
        oracon.se_close()
        oracon = None

        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+'] Error: Lost connection to [CNIS], trying to reconnect. '+str(msg)

        if i == 2:
            sys.exit(0)
        else:
            time.sleep(60)

        oracon = ORA('coss@cnis')
        continue
if rst is not None and len(rst)>0:
    for aw in rst:
        so_info[aw[0]] = aw[1]
        so_name[aw[0]] = aw[2]
        so_printname[aw[0]] = aw[3]

if func=='SYNCDATA':
############# Query all new invoice data --------  BEGIN
    nowtime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print "[%s]: Sync beginning" % (nowtime)
    loopsql="select a.companyno,a.subsid,a.invoice,a.acctcno,a.invtextpath,convert(varchar(19),a.invtexttime,20) invtexttime,b.cellphone01,b.cellphone02,b.telenum01,b.telenum02,b.telenum03,b.email,a.invamt+a.invtax invamt,convert(varchar(10),a.invdate,111) invdate,b.subsname from ms4000 a with (nolock),ms0200 b with (nolock) where a.companyno=b.companyno and a.subsid=b.subsid and a.companyno in (%s) and a.createtime between '%s 00:00:00' and '%s 20:00:00' and a.invcode = '35' and a.einvyn='Y' and a.exportdate<>'' and a.exportdate is not null and a.invamt > 0 and a.taxkind != 'D 作廢'" % (sosql, target_day, target_day_end)
    print loopsql
    for i in range(0, 3):
        try:
            cur.execute(loopsql)
            curarr = cur.fetchall()
            break
        except Exception, msg:
            con.close()
            con = None

            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print '['+nowdate+'] Error: Lost connection to [TFMCossMS], trying to reconnect. '+str(msg)

            if i == 2:
                sys.exit(0)
            else:
                time.sleep(60)

            con = pymssql.connect(host=db_host,user=cossdb.account,password=cossdb.passwd,database='cossdb')
            cur = con.cursor()
            continue

    xlen = len(curarr)
    print "Checking %d invoice tickets" % (xlen)
    sys.stdout.flush()
    i = 0
    while i<xlen:
        so = curarr[i][0]
        subsid = int(curarr[i][1])
        invoice = curarr[i][2]
        acc_so = curarr[i][3]
        invtextpath = curarr[i][4]
        if invtextpath is None:
            invtextpath = ''
        invtexttime = curarr[i][5]
        if invtexttime is None:
            updtime_sql = "to_date(NULL)"
        else:
            updtime_sql = "to_date('%s','yyyy-mm-dd hh24:mi:ss')" % (invtexttime)
        mobile1 = curarr[i][6]
        mobile2 = curarr[i][7]
        mobile = ''
        if mobile!='' and mobile1 is not None and len(mobile1)<=10 and mobile1<>'0900000000' and mobile1[:2]=='09':
            mobile = "%s,%s" % (mobile, mobile1[:10])
        elif mobile1 is not None and len(mobile1)<=10 and mobile1<>'0900000000' and mobile1[:2]=='09':
            mobile = "%s" % (mobile1[:10])
        if mobile!='' and mobile2 is not None and len(mobile2)<=10 and mobile2<>'0900000000' and mobile2[:2]=='09':
            mobile = "%s,%s" % (mobile, mobile2[:10])
        elif mobile2 is not None and len(mobile2)<=10 and mobile2<>'0900000000' and mobile2[:2]=='09':
            mobile = "%s" % (mobile2[:10])
        tel1 = append_lac(so, curarr[i][8])
        tel2 = append_lac(so, curarr[i][9])
        tel3 = append_lac(so, curarr[i][10])

        tel = ''
        if tel1 is not None and len(tel1)<=10 and len(tel1)>5 and tel1[:2]<>'09':
            tel = "%s," % (tel1[:10])
        elif tel2 is not None and len(tel2)<=10 and len(tel2)>5 and tel2[:2]<>'09':
            tel = "%s," % (tel2[:10])
        elif tel3 is not None and len(tel3)<=10 and len(tel3)>5 and tel3[:2]<>'09':
            tel = "%s," % (tel3[:10])
        email = curarr[i][11]
        invamt = int(curarr[i][12])
        invdate = curarr[i][13]
        subsname = curarr[i][14]
        if email is None or email[:4]=="000@" or "@" not in email or '@tfm' in email:
            email = ''

        ## Insert new data to making control status
        p_sid = -1
        qrySQL = "select sid from invoice_status where invoice='%s'" % (invoice)
        o_rs = oracon.execall(qrySQL)
        if o_rs != None and len(o_rs) > 0:
            for o_row in o_rs:
                p_sid = int(o_row[0])
        if p_sid<0:
            mSQL = "insert into invoice_status(so,acc_so,subsid,invoice,coss_status,coss_updtime,mobile,tele,email,inv_amount,inv_date,subsname) values('%s','%s',%d,'%s','%s',%s,'%s','%s','%s',%d,to_date('%s','yyyy/mm/dd'),'%s')" % (so, acc_so, subsid, invoice, invtextpath, updtime_sql, mobile, tel, email, invamt, invdate, subsname)
            try:
                print ".",
                oracon.execone(mSQL)
                if (i%30)==0:
                    oracon.commit()
            except Exception, msg:
                pass
                print mSQL
                print 'ERROR: '+str(msg)
        else:
            #print "Skip: %s, %d, %s -> %d" % (so, subsid, invoice, p_sid)
            print "X",
        sys.stdout.flush()
        i = i+1
    oracon.commit()
    print ""
    nowtime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print "[%s]: Sync OK" % (nowtime)
    sys.exit(0)
######## Query all new invoice data --------  END

######## Query all black list  -------- BEGIN
invoice_blacklist = {}
qrySQL = "select so,subsid,type from invoice_blacklist"
o_rs = oracon.execall(qrySQL)
if o_rs != None and len(o_rs) > 0:
    for o_row in o_rs:
        b_so = o_row[0]
        b_subsid = int(o_row[1])
        b_type = o_row[2]
        invoice_blacklist["%s-%d" % (b_so, b_subsid)] = b_type
######## Query all black list  -------- END

print "Query all black list"
sys.stdout.flush()

######## Update status from e-mail, SMS, IVR --------  BEGIN
print "Updating E-Mail SKIP"
sys.stdout.flush()

updSQL = "update invoice_status set email_status='SKIP',email_updtime=sysdate where email_status is null and email is null and so in (%s)" % (sosql)
try:
    oracon.execone(updSQL)
    oracon.commit()
except Exception, msg:
    pass
    print updSQL
    print 'ERROR: '+str(msg)

print "Updating SMS SKIP"
sys.stdout.flush()

updSQL = "update invoice_status set sms_status='SKIP',sms_updtime=sysdate where email_status in ('SKIP','FAIL') and sms_status is null and mobile is null and so in (%s)" % (sosql)
try:
    oracon.execone(updSQL)
    oracon.commit()
except Exception, msg:
    pass
    print updSQL
    print 'ERROR: '+str(msg)

print "Updating IVR SKIP"
sys.stdout.flush()

updSQL = "update invoice_status set ivr_status='SKIP',sms_updtime=sysdate where sms_status in ('SKIP','FAIL') and ivr_status is null and tele is null and so in (%s)" % (sosql)
try:
    oracon.execone(updSQL)
    oracon.commit()
except Exception, msg:
    pass
    print updSQL
    print 'ERROR: '+str(msg)

print "Updated SKIP status to invoice_status"
sys.stdout.flush()

qrySQL = "begin proc_upd_invoice_status; end;"
print qrySQL
oracon.execone(qrySQL)
######## Update status from e-mail, SMS, IVR --------  END

print "Sending email"
sys.stdout.flush()

######## Send to e-mail --------  BEGIN
oracon_mail = ORA('coss@kbro_nmsdb')
qrySQL = "select sid,so,acc_so,subsid,invoice,email,inv_amount,inv_date,subsname from invoice_status where email_status is null and so in (%s)" % (sosql)
o_rs = oracon.execall(qrySQL)
if o_rs != None and len(o_rs) > 0:
    commit_loop = 0
    for o_row in o_rs:
        p_sid = int(o_row[0])
        p_so = o_row[1]
        p_acc_so = o_row[2]
        p_subsid = int(o_row[3])
        p_invoice = o_row[4]
        p_email = o_row[5]
        try:
            p_invamt = int(o_row[6])
        except:
            pass
            p_invamt = 0
        p_invdate = o_row[7]
        p_subsname = o_row[8]

        email_skip = ''
        try:
            email_skip = invoice_blacklist["%s-%d" % (p_so, p_subsid)]
        except:
            pass

        if p_so=='104':
            from_mail = 'service@mangrovecatv.com.tw'
        else:
            from_mail = 'service@twmbroadband.com'
        updSQL = ''
        if p_email is None or '000@kbro' in p_email or '@tfm' in p_email or email_skip=='EMAIL':
            updSQL = "update invoice_status set email_status='SKIP',email_updtime=sysdate where sid=%d" % (p_sid)
        elif p_email is not None and '000@kbro' not in p_email and '@tfm' not in p_email:
            insSQL = "insert into oss_mail_invoice(sender,target,subject,so,subsid,invoice,invamt,invdate,soname,acct_so,msg) values('%s','%s','%s電子發票開立通知','%s',%d,'%s',%d,to_date('%s','yyyy-mm-dd hh24:mi:ss'),'%s','%s','%s')" % (from_mail,p_email,so_info[p_acc_so],p_so,p_subsid,p_invoice,p_invamt,p_invdate,so_name[p_acc_so],p_acc_so,p_subsname)
            try:
                oracon_mail.execone(insSQL)
                updSQL = "update invoice_status set email_status='SENT',email_updtime=sysdate where sid=%d" % (p_sid)
            except Exception, msg:
                pass
                print insSQL
                print 'ERROR: '+str(msg)
        if updSQL!='':
            try:
                oracon.execone(updSQL)
            except Exception, msg:
                pass
                print updSQL
                print 'ERROR: '+str(msg)
        commit_loop = commit_loop+1
        if (commit_loop%30)==0:
            oracon.commit()
    oracon.commit()
######## Send to e-mail --------  END

print "Sending SMS"
sys.stdout.flush()

######## Send to SMS --------  BEGIN
qrySQL = "select sid,so,acc_so,subsid,invoice,mobile,inv_amount,to_char(inv_date,'yyyy/mm/dd') invdate from invoice_status where email_status in ('SKIP','FAIL') and sms_status is null and so in (%s)" % (sosql)
o_rs = oracon.execall(qrySQL)
if o_rs != None and len(o_rs) > 0:
    commit_loop = 0
    for o_row in o_rs:
        p_sid = int(o_row[0])
        p_so = o_row[1]
        p_acc_so = o_row[2]
        p_subsid = int(o_row[3])
        p_invoice = o_row[4]
        if o_row[5] is not None:
            p_mobile = o_row[5].split(",")[0]
        else:
            p_mobile = None
        p_amount = int(o_row[6])
        p_invdate = o_row[7]

        sms_skip = ''
        try:
            sms_skip = invoice_blacklist["%s-%d" % (p_so, p_subsid)]
        except:
            pass

        if p_subsid>=1000:
            cust_no = '%04s' % (str(p_subsid)[:4])
        else:
            cust_no = '%04d' % (p_subsid)
        sms_msg = "貴訂戶編號%d電子發票號碼%s日期%s金額%s個人識別碼%s至公司網站查詢，%s敬上" % (p_subsid,p_invoice,p_invdate,p_amount,cust_no,so_printname[p_acc_so])
        updSQL = ''
        if p_mobile is None or p_mobile=='' or sms_skip=='SMS':
            updSQL = "update invoice_status set sms_status='SKIP',sms_updtime=sysdate where sid=%d" % (p_sid)
        elif p_mobile is not None:
            insSQL = "insert into sms_invoice(sys,target,msg,so,subsid,invoice,booking_sendtime,acctso) values('SYS_INV','%s','%s','%s',%d,'%s',sysdate,'%s')" % (p_mobile, sms_msg, p_so, p_subsid, p_invoice, p_acc_so)
            try:
                oracon.execone(insSQL)
                print insSQL
                updSQL = "update invoice_status set sms_status='SENT',sms_updtime=sysdate where sid=%d" % (p_sid)
            except Exception, msg:
                pass
                print insSQL
                print 'ERROR: '+str(msg)
        if updSQL!='':
            try:
                oracon.execone(updSQL)
            except Exception, msg:
                pass
                print updSQL
                print 'ERROR: '+str(msg)
        commit_loop = commit_loop+1
        if (commit_loop%30)==0:
            oracon.commit()
    oracon.commit()
######## Send to SMS --------  END

print "Sending IVR"
sys.stdout.flush()

######## Send to IVR --------  BEGIN
oracon_cti = ORA('cti@kbro_nmsdb')
qrySQL = "select sid,so,acc_so,subsid,invoice,tele,subsname from invoice_status where sms_status in ('SKIP','FAIL') and ivr_status is null and so in (%s)" % (sosql)
o_rs = oracon.execall(qrySQL)
if o_rs != None and len(o_rs) > 0:
    commit_loop = 0
    for o_row in o_rs:
        p_sid = int(o_row[0])
        p_so = o_row[1]
        p_acc_so = o_row[2]
        p_subsid = int(o_row[3])
        p_invoice = o_row[4]
        if o_row[5] is not None:
            p_ivr = o_row[5]
        else:
            p_ivr = None
        p_subsname = o_row[6]

        ivr_skip = ''
        try:
            ivr_skip = invoice_blacklist["%s-%d" % (p_so, p_subsid)]
        except:
            pass

        updSQL = ''
        if p_ivr is None or p_ivr=='' or ivr_skip=='IVR':
            updSQL = "update invoice_status set ivr_status='SKIP',ivr_updtime=sysdate where sid=%d" % (p_sid)
        elif p_ivr is not None:
            seqSQL = "select icare_custlist_seq.nextval from dual"
            try:
                s_rs = oracon_cti.execall(seqSQL)
                p_seq = -1
                for s_row in s_rs:
                    p_seq = int(s_row[0])
                if p_seq>0:
                    insFirstSQL = "insert into custlist@ICARE(sid,customer_id,name,tel,rands,status,redialcnt,flowtype,flowid,so_id,createname,flowsource,outbound_type,worksheet,servicename,acct_so) values(%d,%d,'%s','%s','%s','-1',0,'I002','001','%s','E_INV','OUT','1','%s','1 CATV','%s')" % (p_seq, p_subsid, p_invoice, p_ivr, p_ivr, p_so, p_invoice, p_acc_so)
                    insSecondSQL = "insert into custlist_rands@ICARE(sid,rands,status,createdate) values(%d,'%s','-1',sysdate)" % (p_seq, p_ivr)
                    try:
                        oracon_cti.execone(insFirstSQL)
                        oracon_cti.execone(insSecondSQL)
                        print insFirstSQL
                        updSQL = "update invoice_status set ivr_status='SENT',ivr_updtime=sysdate where sid=%d" % (p_sid)
                    except Exception, msg:
                        pass
                        print insFirstSQL
                        print 'ERROR: '+str(msg)

                    if updSQL!='':
                        try:
                            oracon.execone(updSQL)
                        except Exception, msg:
                            pass
                            print updSQL
                            print 'ERROR: '+str(msg)
            except Exception, msg:
                pass
                print seqSQL
                print 'ERROR: '+str(msg)
        commit_loop = commit_loop+1
        if (commit_loop%30)==0:
            oracon.commit()
            oracon_cti.commit()
    oracon.commit()
    oracon_cti.commit()
    oracon_cti.se_close()
######## Send to IVR --------  END

print "Sending COSS"
sys.stdout.flush()

######## Send to COSS --------  BEGIN
qrySQL = "select sid,so,subsid,invoice,email_status,sms_status,ivr_status,to_char(email_sendtime,'yyyy-mm-dd hh24:mi:ss') emailtime,to_char(sms_sendtime,'yyyy-mm-dd hh24:mi:ss') smstime,to_char(ivr_sendtime,'yyyy-mm-dd hh24:mi:ss') ivrtime from invoice_status where coss_flag='N' and (coss_updtime is null or coss_updtime<sysdate-0.5) and so in (%s)" % (sosql)
o_rs = oracon.execall(qrySQL)
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

        mSQL = ''
        updSQL = ''
        if (p_email=='SKIP' or p_email=='FAIL') and (p_sms=='SKIP' or p_sms=='FAIL') and (p_ivr=='SKIP' or p_ivr=='FAIL'):
            mSQL = "update ms4000 set invtextpath='通知失敗',invtexttime='%s' where companyno='%s' and subsid=%d and invoice='%s'" % (nowtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='通知失敗',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email=='OK':
            mSQL = "update ms4000 set invtextpath='完成EMail通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_emailtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成EMail通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_sms=='OK':
            mSQL = "update ms4000 set invtextpath='完成簡訊通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_smstime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成簡訊通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_ivr=='OK':
            mSQL = "update ms4000 set invtextpath='完成電話語音通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_ivrtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成電話語音通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)

        if mSQL!='':
            print mSQL
            try:
                cur.execute(mSQL)
            except Exception, msg:
                pass
                print mSQL
                print 'ERROR: '+str(msg)
        if updSQL!='':
            print updSQL
            try:
                oracon.execone(updSQL)
            except Exception, msg:
                pass
                print updSQL
                print 'ERROR: '+str(msg)
        commit_loop = commit_loop+1
        if (commit_loop%20)==0:
            con.commit()
            oracon.commit()
    con.commit()
    oracon.commit()
######## Send to COSS --------  END

oracon.se_close()

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print '['+nowdate+'] END'
