#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'


def append_lac(xso, xtel):
    if xtel is None or xtel=='':
        return ''
    xtel = xtel.replace("*","")
    if xso=='300' or xso=='310' or xso=='330':
        lac = '03'
    elif xso=='410' or xso=='420':
        lac = '04'
    elif xso=='610':
        lac = '06'
    elif xso=='701':
        lac = '07'
    elif xso=='810' or xso=='820':
        lac = '08'
    else:
        lac = '02'
    return '%s%s' % (lac, xtel)


if len(sys.argv) != 2:
    print 'usage:',sys.argv[0],'[TFM|KBRO|CG|CompanyNo]'
    sys.exit(0)
else:
    so = sys.argv[1].upper()

if so in ['TFM','KBRO','CG']:
    func = 'CHECK'
    if so == 'CG':
        sosql = "'106'"
    elif so == 'TFM':
        sosql = "'101','103','104','300','701'"
    else:
        sosql = "'210','220','230','240','250','260','310','330','410','420','610','810','820'"
elif re.match(r"^\d{3}$", so) is not None:
    func = 'SYNC'
    sosql = "'%s'" % (so)
else:
    print 'usage:',sys.argv[0],'[TFM|KBRO|CG|CompanyNo]'
    sys.exit(0)

if so in ['TFM','101','103','104','300','701']:
    db_host = 'TFMCossMS'
elif so in ['KBRO','210','220','230','240','250','260','310','330','410','420','610','810','820']:
    db_host = 'kbroCossMS'
elif so in ['CG','106']:
    db_host = 'CossMS_CG'
else:
    print 'usage:',sys.argv[0],'[TFM|KBRO|CG|CompanyNo]'
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


yymmdd = time.strftime("%Y%m%d", time.localtime())
year = int(yymmdd[:4])
month = int(yymmdd[4:6])
day = int(yymmdd[6:8])
ydate = time.localtime(time.mktime((year,month,day,0,0,0,-1,-1,-1))-86400*14)
target_day = "%d/%.2d/%.2d" % (ydate[0], ydate[1], ydate[2])
ydate = time.localtime(time.mktime((year,month,day,0,0,0,-1,-1,-1)))
target_day_end = "%d/%.2d/%.2d" % (ydate[0], ydate[1], ydate[2])
ydate = time.localtime(time.mktime((year,month,day,12,0,0,-1,-1,-1))+86400)

print 'target_day:',target_day,'~',target_day_end

nowtime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] START" % (nowtime)

try:
    con = pymssql.connect(host=db_host,user=cossdb.account,password=cossdb.passwd,database='cossdb')
    cur = con.cursor()
except Exception, msg:
    print 'Error: Unable to connect to ['+db_host+']'
    sys.exit(0)

ora = ORA('nms@cnis')
if not ora.db:
    print 'Error: Unable to connect to [NMS@CNIS]'
    sys.exit(0)

so_info = {}
so_name = {}
so_printname = {}

SQL = "select companyno,fullname,soname,printname from so"
print SQL
rst = ora.execall(SQL)
if rst is not None and len(rst) > 0:
    for aw in rst:
        try:
            so_info[aw[0]] = aw[1]
            so_name[aw[0]] = aw[2]
            so_printname[aw[0]] = aw[3]
        except Exception, msg:
            print 'Except:',str(msg)

if len(so_info) == 0:
    print 'Error: SO is empty [CNIS]'
    sys.exit(0)


# Query all new invoice data BEGIN
if func == 'SYNC':
    loopsql = "select a.companyno,a.subsid,a.invoice,a.acctcno,a.invtextpath,convert(varchar(19),a.invtexttime,20) invtexttime,b.cellphone01,b.cellphone02,b.telenum01,b.telenum02,b.telenum03,b.email,a.invamt+a.invtax invamt,convert(varchar(10),a.invdate,111) invdate,b.subsname,b.contactmode from ms4000 a with (nolock),ms0200 b with (nolock) where a.companyno=b.companyno and a.subsid=b.subsid and a.companyno in (%s) and a.createtime between '%s 00:00:00' and '%s 20:00:00' and a.invcode = '35' and a.einvyn='Y' and a.exportdate<>'' and a.exportdate is not null and (a.invtextyn='N' or a.invtextyn='' or a.invtextyn is null) and a.invamt > 0 and a.taxkind != 'D 作廢'" % (sosql, target_day, target_day_end)
    print loopsql
    cur.execute(loopsql)
    while 1:
        curarr = cur.fetchmany(100)
        if curarr:
            for i in range(0, len(curarr)):
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
                if tel!='' and tel1 is not None and len(tel1)<=10 and tel1[:2]<>'09':
                    tel = "%s,%s" % (tel, tel1[:10])
                elif tel1 is not None and len(tel1)<=10 and tel1[:2]<>'09':
                    tel = "%s" % (tel1[:10])
                if tel!='' and tel2 is not None and len(tel2)<=10 and tel2[:2]<>'09':
                    tel = "%s,%s" % (tel, tel2[:10])
                elif tel2 is not None and len(tel2)<=10 and tel2[:2]<>'09':
                    tel = "%s" % (tel2[:10])
                if tel!='' and tel3 is not None and len(tel3)<=10 and tel3[:2]<>'09':
                    tel = "%s,%s" % (tel, tel3[:10])
                elif tel3 is not None and len(tel3)<=10 and tel3[:2]<>'09':
                    tel = "%s" % (tel3[:10])

                email = curarr[i][11]
                if email is not None and len(email) > 0:
                    email = email.lower()
                if email is None or email[:4]=='000@' or '@' not in email or '@tfm' in email or '@kbronet' in email:
                    email = ''
                invamt = int(curarr[i][12])
                invdate = curarr[i][13]
                subsname = curarr[i][14]
                contactmode = curarr[i][15]

                email_status = email_updtime = sms_status = sms_updtime = ivr_status = ivr_updtime = 'null'
                if contactmode != None and len(contactmode) > 0:
                    if 'EMAIL' in contactmode or '簡訊' in contactmode or '語音' in contactmode or '不通知' in contactmode:
                        if 'EMAIL' in contactmode:
                            email_status = "'YES'"
                        if '簡訊' in contactmode:
                            sms_status = "'YES'"
                        if '語音' in contactmode:
                            ivr_status = "'YES'"

                        if email_status == 'null':
                            email_status = "'NO'"
                        if sms_status == 'null':
                            sms_status = "'NO'"
                        if ivr_status == 'null':
                            ivr_status = "'NO'"

                        email_updtime = sms_updtime = ivr_updtime = 'sysdate'

                # Insert new data to making control status
                p_sid = -1
                qrySQL = "select sid from invoice_status where invoice='%s'" % (invoice)
                print invoice,
                o_rs = oracoss.execall(qrySQL)
                if o_rs != None and len(o_rs) > 0:
                    for o_row in o_rs:
                        p_sid = int(o_row[0])

                if p_sid<0:
                    updSQL = "insert into invoice_status (so,acc_so,subsid,invoice,coss_status,coss_updtime,mobile,tele,email,inv_amount,inv_date,subsname,email_status,email_updtime,sms_status,sms_updtime,ivr_status,ivr_updtime) values ('%s','%s',%d,'%s','%s',%s,'%s','%s','%s',%d,to_date('%s','yyyy/mm/dd'),'%s',%s,%s,%s,%s,%s,%s)" % (so, acc_so, subsid, invoice, invtextpath, updtime_sql, mobile, tel, email, invamt, invdate, subsname, email_status,email_updtime,sms_status,sms_updtime,ivr_status,ivr_updtime)
                    print updSQL
                    try:
                        oracoss.execone(updSQL)
                        if (i%30)==0:
                            oracoss.commit()
                    except Exception, msg:
                        print 'Except:',str(msg)
                else:
                    print 'PASS'
                sys.stdout.flush()
        else:
            break
    oracoss.commit()
    oracoss.se_close()
    con.close()

    nowtime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print "[%s] END" % (nowtime)

    sys.exit(0)
# Query all new invoice data END

# Update status from EMAIL, SMS, IVR BEGIN
updSQL = "update invoice_status set email_status='SKIP',email_updtime=sysdate where (email_status='YES' or email_status is null) and email is null and so in (%s)" % (sosql)
print updSQL
sys.stdout.flush()
try:
    oracoss.execone(updSQL)
    oracoss.commit()
except Exception, msg:
    print 'Except:',str(msg)

updSQL = "update invoice_status set sms_status='SKIP',sms_updtime=sysdate where (sms_status='YES' or (email_status in ('SKIP','FAIL') and sms_status is null)) and mobile is null and so in (%s)" % (sosql)
print updSQL
sys.stdout.flush()
try:
    oracoss.execone(updSQL)
    oracoss.commit()
except Exception, msg:
    print 'Except:',str(msg)

updSQL = "update invoice_status set ivr_status='SKIP',ivr_updtime=sysdate where (ivr_status='YES' or (sms_status in ('SKIP','FAIL') and ivr_status is null)) and tele is null and so in (%s)" % (sosql)
print updSQL
sys.stdout.flush()
try:
    oracoss.execone(updSQL)
    oracoss.commit()
except Exception, msg:
    print 'Except:',str(msg)

qrySQL = "begin proc_upd_invoice_status; end;"
print qrySQL
sys.stdout.flush()
oracoss.execone(qrySQL)
oracoss.commit()
# Update status from EMAIL, SMS, IVR END

# Send to EMAIL BEGIN
oramail = ORA('coss@kbro_nmsdb')
if not oramail.db:
    print 'Error: Unable to connect to [COSS@KBRO_NMSDB]'
    sys.exit(0)

qrySQL = "select sid,so,acc_so,subsid,invoice,email,inv_amount,inv_date,subsname from invoice_status where (email_status='YES' or email_status is null) and so in (%s)" % (sosql)
print qrySQL
sys.stdout.flush()
o_rs = oracoss.execall(qrySQL)
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
            p_invamt = 0
        p_invdate = o_row[7]
        p_subsname = o_row[8]

        if p_so in ['101','103','300','701','500']:
            from_mail = 'service@twmbroadband.com'
        elif p_so=='104':
            from_mail = 'service@mangrovecatv.com.tw'
        elif p_so=='106':
            from_mail = 'service01@cable-giant.com.tw'
        elif p_so=='820':
            from_mail = 'service01@pncatv.com.tw'
        elif p_so in ['210','220','230','240','250','260','310','330','410','420','610','810','026']:
            from_mail = 'service01@kbronet.com.tw'
        else:
            from_mail = 'service01@cablecatv.com.tw'

        updSQL = ''
        if p_email is None or p_email[:4]=='000@' or '@' not in p_email or '@tfm' in p_email or '@kbronet' in p_email:
            updSQL = "update invoice_status set email_status='SKIP',email_updtime=sysdate where sid=%d" % (p_sid)
        elif p_email is not None and len(p_email) > 0:
            insSQL = "insert into oss_mail_invoice(sender,target,subject,so,subsid,invoice,invamt,invdate,soname,acct_so,msg) values('%s','%s','%s電子發票開立通知','%s',%d,'%s',%d,'%s','%s','%s','%s')" % (from_mail,p_email,so_info[p_acc_so],p_so,p_subsid,p_invoice,p_invamt,p_invdate,so_name[p_acc_so],p_acc_so,p_subsname)
            print insSQL
            try:
                oramail.execone(insSQL)
                updSQL = "update invoice_status set email_status='SENT',email_updtime=sysdate where sid=%d" % (p_sid)
            except Exception, msg:
                print 'Except:',str(msg)
        if updSQL!='':
            print updSQL
            try:
                oracoss.execone(updSQL)
            except Exception, msg:
                print 'Except:',str(msg)
        commit_loop = commit_loop+1
        if (commit_loop%30)==0:
            oramail.commit()
            oracoss.commit()
        sys.stdout.flush()
    oramail.commit()
    oracoss.commit()

oramail.se_close()
# Send to EMAIL END

# Send to SMS BEGIN
qrySQL = "select sid,so,acc_so,subsid,invoice,mobile,inv_amount,to_char(inv_date,'yyyy/mm/dd') invdate from invoice_status where (sms_status='YES' or (email_status in ('SKIP','FAIL') and sms_status is null)) and so in (%s)" % (sosql)
print qrySQL
sys.stdout.flush()
o_rs = oracoss.execall(qrySQL)
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
        if p_subsid>=1000:
            cust_no = '%04s' % (str(p_subsid)[:4])
        else:
            cust_no = '%04d' % (p_subsid)

        if p_acc_so in ['101','103','104','300','701','500']:
            sms_msg = "貴訂戶編號%d發票號碼%s日期%s金額%s個人識別碼%s請至公司網站查詢，%s敬上" % (p_subsid,p_invoice,p_invdate,p_amount,cust_no,so_printname[p_acc_so])
        elif p_acc_so=='240':
            sms_msg = "貴戶有線電視繳費已收到，發票號碼%s日期%s金額%s訂戶編號%d請至公司網站查詢，%s上" % (p_invoice,p_invdate,p_amount,p_subsid,so_printname[p_acc_so])
        elif p_acc_so=='250':
            sms_msg = "貴戶有線電視繳費已收到，發票號碼%s日期%s金額%s訂編%d請至公司網站查詢，全聯有線電視上" % (p_invoice,p_invdate,p_amount,p_subsid)
        elif p_acc_so=='310':
            sms_msg = "貴戶有線電視繳費已收到，發票號碼%s日期%s金額%s訂戶編號%d請至公司網站查詢，%s上" % (p_invoice,p_invdate,p_amount,p_subsid,so_printname[p_acc_so])
        elif p_acc_so=='026':
            sms_msg = "貴戶寬頻上網繳費已收到，發票號碼%s日期%s金額%s訂戶編號%d請至公司網站查詢，凱擘敬上" % (p_invoice,p_invdate,p_amount,p_subsid)
        elif p_acc_so=='106':
            sms_msg = "貴戶繳費已收到，發票號碼%s日期%s金額%s訂戶編號%d請至公司網站查詢，%s敬上" % (p_invoice,p_invdate,p_amount,p_subsid,so_printname[p_acc_so])
        else:
            sms_msg = "貴戶有線電視繳費已收到，發票號碼%s日期%s金額%s訂戶編號%d請至公司網站查詢，%s敬上" % (p_invoice,p_invdate,p_amount,p_subsid,so_printname[p_acc_so])

        updSQL = ''
        if p_mobile is None or p_mobile=='':
            updSQL = "update invoice_status set sms_status='SKIP',sms_updtime=sysdate where sid=%d" % (p_sid)
        elif p_mobile is not None:
            insSQL = "insert into oss_sms_invoice(sys,target,msg,so,subsid,invoice,booking_sendtime,acctso) values('SYS_INV','%s','%s','%s',%d,'%s',sysdate,'%s')" % (p_mobile, sms_msg, p_so, p_subsid, p_invoice, p_acc_so)
            print insSQL
            try:
                oracoss.execone(insSQL)
                updSQL = "update invoice_status set sms_status='SENT',sms_updtime=sysdate where sid=%d" % (p_sid)
            except Exception, msg:
                print 'Except:',str(msg)
        if updSQL!='':
            print updSQL
            try:
                oracoss.execone(updSQL)
            except Exception, msg:
                print 'Except:',str(msg)
        commit_loop = commit_loop+1
        if (commit_loop%30)==0:
            oracoss.commit()
        sys.stdout.flush()
    oracoss.commit()
# Send to SMS END

# Send to IVR BEGIN
oracti = ORA('icare@cti')
if not oracti.db:
    print 'Error: Unable to connect to [ICARE@CTI]'
    sys.exit(0)

qrySQL = "select sid,so,acc_so,subsid,invoice,tele from invoice_status where (ivr_status='YES' or (sms_status in ('SKIP','FAIL') and ivr_status is null)) and so in (%s)" % (sosql)
print qrySQL
sys.stdout.flush()
o_rs = oracoss.execall(qrySQL)
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
        if p_so in ['101','103','104','300','701','500']:
            p_flowtype = 'I002'
        else:
            p_flowtype = 'I001'

        updSQL = ''
        if p_ivr is None or p_ivr=='':
            updSQL = "update invoice_status set ivr_status='SKIP',ivr_updtime=sysdate where sid=%d" % (p_sid)
        elif p_ivr is not None:
            seqSQL = "select custlist_seq.nextval from dual"
            print seqSQL
            try:
                s_rs = oracti.execall(seqSQL)
                p_seq = -1
                for s_row in s_rs:
                    p_seq = int(s_row[0])
                if p_seq>0:
                    insFirstSQL = "insert into custlist (sid,customer_id,name,tel,rands,status,redialcnt,flowtype,flowid,so_id,createname,flowsource,outbound_type,worksheet,servicename,acct_so) values (%d,%d,'%s','%s','%s','-1',0,'%s','001','%s','E_INV','OUT','1','%s','1 CATV','%s')" % (p_seq, p_subsid, p_invoice, p_ivr, p_ivr, p_flowtype, p_so, p_invoice, p_acc_so)
                    insSecondSQL = "insert into custlist_rands (sid,rands,status,createdate) values(%d,'%s','-1',sysdate)" % (p_seq, p_ivr)
                    print insFirstSQL
                    print insSecondSQL
                    try:
                        oracti.execone(insFirstSQL)
                        oracti.execone(insSecondSQL)
                        updSQL = "update invoice_status set ivr_status='SENT',ivr_updtime=sysdate where sid=%d" % (p_sid)
                    except Exception, msg:
                        print 'Except:',str(msg)
                else:
                    print 'Except: IVR SID create fail %s' % (p_invoice)
            except Exception, msg:
                print 'Except:',str(msg)
        if updSQL!='':
            print updSQL
            try:
                oracoss.execone(updSQL)
            except Exception, msg:
                print 'Except:',str(msg)
        commit_loop = commit_loop+1
        if (commit_loop%30)==0:
            oracoss.commit()
            oracti.commit()
        sys.stdout.flush()
    oracoss.commit()
    oracti.commit()

oracti.se_close()
# Send to IVR END

# Send to COSS BEGIN
qrySQL = "select sid,so,subsid,invoice,email_status,sms_status,ivr_status,to_char(email_sendtime,'yyyy-mm-dd hh24:mi:ss') emailtime,to_char(sms_sendtime,'yyyy-mm-dd hh24:mi:ss') smstime,to_char(ivr_sendtime,'yyyy-mm-dd hh24:mi:ss') ivrtime from invoice_status where coss_flag='N' and (coss_updtime is null or coss_updtime<sysdate-0.5) and so in (%s)" % (sosql)
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
        if p_email=='NO' and p_sms=='NO' and p_ivr=='NO':
            mSQL = "update ms4000 set invtextpath='不通知',invtexttime='%s' where companyno='%s' and subsid=%d and invoice='%s'" % (nowtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='不通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email in ['SKIP','FAIL','NO'] and p_sms in ['SKIP','FAIL','NO'] and p_ivr in ['SKIP','FAIL','NO']:
            mSQL = "update ms4000 set invtextpath='通知失敗',invtexttime='%s' where companyno='%s' and subsid=%d and invoice='%s'" % (nowtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='通知失敗',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email=='OK' and p_sms=='OK' and p_ivr=='OK':
            mSQL = "update ms4000 set invtextpath='完成EMAIL&簡訊&電話語音通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_ivrtime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成EMAIL&簡訊&電話語音通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email=='OK' and p_sms=='OK' and p_ivr in ['SKIP','FAIL','NO']:
            mSQL = "update ms4000 set invtextpath='完成EMAIL&簡訊通知',invtexttime='%s',invtextyn='Y' where companyno='%s' and subsid=%d and invoice='%s'" % (p_smstime, p_so, p_subsid, p_invoice)
            updSQL = "update invoice_status set coss_status='完成EMAIL&簡訊通知',coss_updtime=sysdate,coss_flag='Y' where sid=%d" % (p_sid)
        elif p_email=='OK' and p_sms in ['SKIP','FAIL','NO'] and p_ivr=='OK':
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
            except Exception, msg:
                print 'Except:',str(msg)
        if updSQL!='':
            print updSQL
            try:
                oracoss.execone(updSQL)
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

oracoss.se_close()
con.close()

nowtime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] END" % (nowtime)
