#!/usr/bin/env python
# -*- coding: Big5 -*-
import sys,datetime,string,types,time
import pymssql
from oraclass import ORA

if len(sys.argv)<2:
    print "[Error]: Argument error."
    sys.exit(0)
else:
    p_so = sys.argv[1]

if p_so=='TFM':
    db_host = "TFMCossMS_CP950"
    oracon_cti = ORA('cti@CNIS')
    oracon_oems = ORA('oems@KBRO_NMSDB')
    db_name = "cossdb"
elif p_so=='kbro':
    db_host = "kbroCossMS_CP950"
    oracon_cti = ORA('cti@KBRO_NMSDB')
    oracon_oems = ORA('oems@KBRO_NMSDB')
    db_name = "cossdb"
else:
    print "[Error]: Argument %s error." % (p_so)
    sys.exit(0)

con = pymssql.connect(host=db_host,user='proguser',password='cossuser',database=db_name)
cur = con.cursor()

so_name = {}
oraqrysql = "select name,id from oems_mapping where type='OPERATOR' and name is not null"
rs = oracon_oems.execall(oraqrysql)
if rs != None and len(rs) > 0:
    for a_row in rs:
       so_name[a_row[0]] = a_row[1]
fdsql = "select to_char(so) so,subsid,subsname,personid,agent_ext,servicetype,calltypelv1,calltypelv2,calltypelv3,chargename,line_num,phn_num,agent_id,agent_name,agent_dept,decode(bookdate,null,to_char(sysdate,'yyyy/mm/dd hh24:mi'),to_char(bookdate,'yyyy/mm/dd hh24:mi')) bookdate,autoclose,in_out,memo,trunc(callin_history_id,0) callin_history_id,book_flag,to_char(calltime,'yyyy/mm/dd hh24:mi'),updatename,to_char(updatetime,'yyyy/mm/dd hh24:mi'),oems_flag,question_01,question_02,question_03,question_04,question_05,tvposition,tvsetup,tvsize,case when calltypelv3 like '%%行銷推廣%%' then 1 when calltypelv2 like '%%行銷推廣%%' then 1 else 0 end skip_flag,calltypelv4 from cti.cti010 where coss_id is null and so is not null and subsid is not null and create_date>=sysdate-1"
rs = oracon_cti.execall(fdsql)
if rs != None and len(rs) > 0:
    for a_row in rs:
      try:
        qrysql = "select convert(varchar(6),getdate(),112) as yymm"
        cur.execute(qrysql)
        xarr = cur.fetchone()
        yymm = xarr[0]
        try:
            companyno = a_row[0]
            subsid = int(a_row[1])
            createname = a_row[13]
            servicename = a_row[5]
            calltypelv2 = a_row[7]
            if len(calltypelv2)>40:
                print '>>40'
                callrequest = calltypelv2[:40]
                ix = 1
                while ord(calltypelv2[(40-ix):(40-ix+1)])>128 and ix<40:
                    callrequest = calltypelv2[:(40-ix)]
                    ix = ix+1
            else:
                callrequest = calltypelv2
            calltypelv3 = a_row[8]
            if '行銷推廣' in calltypelv3 or '行銷推廣' in calltypelv2:
                msresult = '012 客考慮'
            else:
                msresult = ''
            if a_row[6]=='10.LS':
                servicename = '8 LS'
            memo = a_row[18]
            if memo is None:
                memo=''
            else:
                memo = string.replace(memo,"'","_")
                memo = string.replace(memo,'"','_')
                memo = string.replace(memo,'$','_')
                memo = string.replace(memo,"?","")
                memo = string.replace(memo,"--","_")
                memo = string.replace(memo,chr(10),'')
                memo = string.replace(memo,chr(13),'')
            question1 = ''
            question2 = ''
            question3 = ''
            question4 = ''
            question5 = ''
            tvposition = ''
            tvsetup = ''
            tvsize = ''
            if a_row[25] is not None:
                question1 = a_row[25]
            if a_row[26] is not None:
                question2 = a_row[26]
            if a_row[27] is not None:
                question3 = a_row[27]
            if a_row[28] is not None:
                question4 = a_row[28]
            if a_row[29] is not None:
                question5 = a_row[29]
            if a_row[30] is not None:
                tvposition = a_row[30]
            if a_row[31] is not None:
                tvsetup = a_row[31]
            if a_row[32] is not None:
                tvsize = a_row[32]
            if a_row[34] is not None:
                calltypelv4 = a_row[34]
            skip_flag = int(a_row[33])
            a_row[19] = int(a_row[19])

            try:
                oems_flag = int(a_row[24])
            except:
                oems_flag = 0
            if oems_flag==4:
                calltypelv4 = '004 行銷推廣'
            elif oems_flag==13: # swallow modify
                oraqrysql = "select id,descr from oems_mapping where type='UNITYTYPE' and (name like '%s%%' or '%s' like '%%'||replace(descr,'(CMC)','')||'%%' or '%s' like '%%'||replace(descr,'(DTV)','')||'%%' or '%s' like '%%'||replace(descr,'(CM/CP)','')||'%%')" % (calltypelv4, calltypelv4, calltypelv4, calltypelv4)
                #oraqrysql = "select id,descr from oems_mapping where type='UNITYTYPE' and (name like '%s%%' or '%s' like '%%'||descr||'%%')" % (calltypelv4, calltypelv4)
                #oraqrysql = "select id,descr from oems_mapping where type='UNITYTYPE' and name like '%s%%'" % (calltypelv4)
                o_rs = oracon_oems.execall(oraqrysql)
                oems_typeid = -1
                oems_reason = ''
                if o_rs != None and len(o_rs) > 0:
                    for o_row in o_rs:
                        oems_typeid = int(o_row[0])
                        oems_reason = o_row[1]
#--------------RECODING BY FISHBEAR-----START--------
                if len(question1) > 0:
                    question1 = 'Q1.'+ question1
                if len(question2) > 0:
                    question2 = ',Q2.'+ question2
                if len(question3) > 0:
                    question3 = ',Q3.'+ question3
                if len(question4) > 0:
                    question4 = ',Q4.'+ question4
                if len(question5) > 0:
                    question5 = ',Q5.'+ question5
                remarks = question1 + question2 + question3 + question4 + question5

                oraupdsql = "begin insert into oems_tickets_main(status,type,descr,create_date,operator,account,normal_flag,remarks) \
                                 values('5100','%d','%s',sysdate,'%s','%s','U','%s') return to_char(sid) into :1 ; end;" \
                                 % (oems_typeid, memo, so_name[companyno], createname, remarks)
#--------------RECODING BY FISHBEAR-----END--------
                oems_sid_ary = oracon_oems.db.BindingArray(1,12,'SQLT_STR')
                oracon_oems.c.execute(oraupdsql, oems_sid_ary)
                oems_sid = int(oems_sid_ary[0])

                oraupdsql = "insert into oems_tickets_log(sid,status,descr,account) values('%d','5100','%s','%s')" % (oems_sid, memo, createname)
                oracon_oems.execone(oraupdsql)
                oracon_oems.commit()

                qrysql = "select servicename,singlesn,telenum01,cellphone01,subsname from ms0200 with (nolock) where companyno='%s' and subsid='%d'" % (companyno, subsid)
                cur.execute(qrysql)
                xarr = cur.fetchone()
                if xarr is not None:
                    servicename = xarr[0]
                    cmmac = xarr[1]
                    telenum01 = xarr[2]
                    cellphone01 = xarr[3]
                    subsname = xarr[4]

                    oraupdsql = "insert into OEMS_IMPACT_SUBSCRID(sid,companyno,subsid,servicename,create_date) values(%d,'%s',%d,'%s',sysdate)" % (oems_sid,companyno,subsid,servicename)
                    oracon_oems.c.execute(oraupdsql)
                    oracon_oems.commit()

                    oraupdsql = "update cti010 set coss_id='%d' where CALLIN_HISTORY_ID='%ld'" % (oems_sid, a_row[19])
                    print oraupdsql
                    oracon_cti.execone(oraupdsql)
                    oracon_cti.commit()
                else:
                    oraupdsql = "update cti010 set coss_id='%d' where CALLIN_HISTORY_ID='%ld'" % (oems_sid, a_row[19])
                    print oraupdsql
                    oracon_cti.execone(oraupdsql)
                    oracon_cti.commit()
                continue
        except Exception, msg:
            print msg
            sys.stdout.flush()
            oraupdsql = "update cti010 set coss_id='-1' where CALLIN_HISTORY_ID='%ld'" % (a_row[19])
            print oraupdsql
            oracon_cti.execone(oraupdsql)
            oracon_cti.commit()
            continue

        qrysql = "select custid,subsname,convert(char(10),custbirth,111) custbirth,bornmonth,personid,foreignyn,custstatus,custkind01,servicename,custgender,contractno,nowcount,telenum01,cellphone01,singlesn,smartcard,billitem,salecampaign,packagename from ms0200 with (nolock) where companyno='%s' and subsid='%d'" % (companyno, subsid)
        cur.execute(qrysql)
        xarr = cur.fetchone()
        if xarr is None:
            sys.stdout.flush()
            oraupdsql = "update cti010 set coss_id='-1' where CALLIN_HISTORY_ID='%ld'" % (a_row[19])
            print oraupdsql
            oracon_cti.execone(oraupdsql)
            oracon_cti.commit()
            continue
        else:
            custid = xarr[0]
            custname = xarr[1]
            try:
                custname = custname.decode('cp950').encode('cp950')
            except:
                custname = custname[0:2]
            custbirth = xarr[2]
            if xarr[3] is None:
                bornmonth = ''
            else:
                bornmonth = xarr[3]
            personid = xarr[4]
            foreignyn = xarr[5]
            custstatus = xarr[6]
            custkind01 = xarr[7]
            servicename = xarr[8]
            custgender = xarr[9]
            contractno = xarr[10]
            nowcount = xarr[11]
            telenum01 = xarr[12]
            cellphone01 = xarr[13]
            singlesn = xarr[14]
            if singlesn is None:
                singlesn = ''
            smartcard = xarr[15]
            if smartcard is None:
                smartcard = ''
            billitem = xarr[16]
            salecampaign = xarr[17]
            if salecampaign is None:
                salecampaign = ''
            packagename = xarr[18]

        if contractno is None:
            contractno = ''
        if nowcount is None:
            nowcount = ''
        if telenum01 is None:
            telenum01 = ''
        if cellphone01 is None:
            cellphone01 = ''
        if custbirth is None:
            custbirth = ''

        qrysql = "select worksheet,max(cleancause) cleancause from ms0301 with (nolock) where companyno='%s' and subsid='%s' and salekind='Z 維修' and sheetstatus<>'A...' and createtime>=getdate()-7 group by worksheet" % (companyno, subsid)
        cur.execute(qrysql)
        xarr = cur.fetchone()
        if xarr is None:
            p_worksheet = ''
            p_cleancause = ''
        else:
            p_worksheet = xarr[0]
            p_cleancause = xarr[1]

        qrysql = "select count(distinct worksheet) disp_cnt from ms0301 with (nolock) where companyno='%s' and subsid=%d and salekind='Z 維修' and sheetstatus<>'A...' and createtime>=getdate()-28" % (companyno, subsid)
        cur.execute(qrysql)
        xarr = cur.fetchone()
        p_disp_cnt_28 = 0
        if xarr is not None:
            p_disp_cnt_28 = int(xarr[0])

        qrysql = "select count(distinct worksheet) disp_cnt from ms0301 with (nolock) where companyno='%s' and subsid=%d and salekind='Z 維修' and sheetstatus<>'A...' and createtime>=getdate()-7" % (companyno, subsid)
        cur.execute(qrysql)
        xarr = cur.fetchone()
        p_disp_cnt_7 = 0
        if xarr is not None:
            p_disp_cnt_7 = int(xarr[0])
            p_disp_cnt_7 = p_disp_cnt_7+1

        qrysql = "select count(distinct callin_history_id) cnt from cti010 where subsid=%d and create_date>=sysdate-3" % (subsid)
        o_rs = oracon_cti.execall(qrysql)
        p_inbound_cnt_3 = 0
        if o_rs is not None:
            for o_row in o_rs:
                p_inbound_cnt_3 = int(o_row[0])

        qrysql = "select servname,netid from ms0100 with (nolock) where companyno='%s' and custid='%s'" % (a_row[0], custid)
        cur.execute(qrysql)
        xarr = cur.fetchone()
        if xarr is None:
            sys.stdout.flush()
            continue
        else:
            servname = xarr[0]
            netid = xarr[1]
        qrysql = "select addrno,linkid,nodeno,mscity,msdistrict,msroad,addrname,mduname from ms0102 with (nolock) where addrno='0' and companyno='%s' and custid='%s'" % (a_row[0], custid)
        cur.execute(qrysql)
        xarr = cur.fetchone()
        if xarr is None:
            sys.stdout.flush()
            continue
        else:
            addrno = xarr[0]
            linkid = xarr[1]
            nodeno = xarr[2]
            mscity = xarr[3]
            msdistrict = xarr[4]
            msroad = xarr[5]
            addrname = xarr[6]
            mduname = xarr[7]
            if a_row[17]=='IN':
                inout = 'I'
            else:
                inout = 'O'
        if a_row[17].upper()=='IN' and oems_flag==1:
            wksql = "select coss.func_get_coss_wkid('A','%s') wkid from dual" % (a_row[0])
            workkind = 'T CTI後送'
        elif oems_flag==2:
            wksql = "select coss.func_get_coss_wkid('A','%s') wkid from dual" % (a_row[0])
            workkind = 'L 二階申告'
        elif oems_flag==4:
            wksql = "select coss.func_get_coss_wkid('D','%s') wkid from dual" % (a_row[0])
            workkind = 'E 去電'
        else:
            wksql = "select coss.func_get_coss_wkid('A','%s') wkid from dual" % (a_row[0])
            workkind = 'T CTI後送'
        rs1 = oracon_cti.execall(wksql)
        if rs1 is None or len(rs1)==0:
            time.sleep(5)
            continue
        else:
            for b_row in rs1:
                wkno = b_row[0]

        msremark = "%s" % (calltypelv2)
        createname = "CTI:%s" % (a_row[13])
        if servicename=='1 CATV':
            chargename = '110090 客戶端設備維修費'
            billitem_sql = "'%s','','','','','','','',''" % (billitem)
        elif servicename=='2 CM':
            chargename = '019 維修費'
            billitem_sql = "'','%s','','','','','','',''" % (billitem)
        elif servicename=='3 DSTB':
            chargename = '019 維修費'
            billitem_sql = "'','','%s','','','','','',''" % (billitem)
        elif servicename=='5 FTTB':
            chargename = '019 維修費'
            billitem_sql = "'','','','','%s','','','',''" % (billitem)
        elif servicename=='9 CMC':
            chargename = '019 維修費'
            billitem_sql = "'','','','','','','','','%s'" % (billitem)
        else:
            chargename = '019 維修費'
            billitem_sql = "'','','','','','','','',''"

        if len(calltypelv4)>60:
            calltypelv4 = calltypelv4[:59]
        if memo is None:
            mscomment = "%s%s%s%s%s" % (question1, question2, question3, question4, question5)
        else:
            mscomment = "%s%s%s%s%s%s" % (question1, question2, question3, question4, question5, memo)
        mscomment = string.replace(mscomment,"'","_")
        mscomment = string.replace(mscomment,'"','_')
        mscomment = string.replace(mscomment,'$','_')
        mscomment = string.replace(mscomment,"?","")
        mscomment = string.replace(mscomment,"--","_")
        mscomment = string.replace(mscomment,chr(10),'')
        mscomment = string.replace(mscomment,chr(13),'')
        if p_disp_cnt_28>=2:
            mscomment = '++天內重複派修超過3次++%s' % (mscomment)
            p_disp_cnt_28 = p_disp_cnt_28+1
        if p_worksheet!='':
            mscomment = '**7天內重複派修(工單:%s,原因:%s)%s' % (p_worksheet, p_cleancause, mscomment)

        if len(mscomment)>250:
            print '------  > 250'
            i = 250
            while i>200:
                ch = ord(mscomment[i])
                if ch>128:
                    i = i-1
                else:
                    mscomment = mscomment[:i]+mscomment[i]
                    print mscomment
                    break
            if i<=200:
                mscomment = mscomment[:250]

        book_flag = a_row[20]
        if book_flag is None:
            book_flag = ''
        calltime = a_row[21]
        updatename = a_row[22]
        updatetime = a_row[23]

        if skip_flag==1:
            caseclose = 'Y'
        else:
            caseclose = 'N'

        if updatename is not None and updatename!='':
            ins0310sql = "insert into ms0310(companyno,inoutbound,worksheet,servicename,callrequest,workcause, \
                      custid,custname,subsid,subsname,telenum01,bookdate,workteam,workkind,mscomment,assigndate, \
                      msremark,caseclose,createtime,createname,updatetime,updatename,msresult) values('%s','%s','%s','%s','%s','%s','%s','%s','%s', \
                      '%s','%s','%s','%s','%s','%s',convert(varchar(19),getdate(),121),'%s','%s','%s','%s','%s','%s','%s')" % \
                      (a_row[0],inout,wkno,servicename,callrequest,calltypelv4,custid,custname,a_row[1],custname,a_row[11], \
                       a_row[15],servname,workkind,mscomment,msremark,caseclose,calltime,createname,updatetime,updatename,msresult)
        else:
            ins0310sql = "insert into ms0310(companyno,inoutbound,worksheet,servicename,callrequest,workcause, \
                      custid,custname,subsid,subsname,telenum01,bookdate,workteam,workkind,mscomment,assigndate, \
                      msremark,caseclose,createtime,createname,msresult) values('%s','%s','%s','%s','%s','%s','%s','%s','%s', \
                      '%s','%s','%s','%s','%s','%s',convert(varchar(19),getdate(),121),'%s','%s',convert(varchar(19),getdate(),121),'%s','%s')" % \
                      (a_row[0],inout,wkno,servicename,callrequest,calltypelv4,custid,custname,a_row[1],custname,a_row[11], \
                       a_row[15],servname,workkind,mscomment,msremark,caseclose,createname,msresult)
        try:
            pass # swallow modify
            #cur.execute(ins0310sql)
            #con.commit()
        except Exception, msg:
            print str(msg)
            continue

        if '維修' in calltypelv3:
            address_str = "%s%s" % (msdistrict,addrname)
            ins0300sql = "insert into ms0300(companyno,worksheet,custid,custname,custgender,custbirth,bornmonth, \
                                      personid,foreignyn,custstatus,custkind01,servgroup,servready,servicename, \
                                      workkind,callcause,workcause,printbillyn,mduno,contractno,moditimes, \
                                      modiprint,billprint,addrno,nowcount,telenum01,cellphone01,linkid,nodeno, \
                                      netid,mscitya,msdistricta,msroada,instaddrname,callinname,callintele, \
                                      mscomment1,msvalue,bookdate,workteam,servname,createtime,createname,appointyn, \
                                      billitem1,billitem2,billitem3,billitem4,billitem5,billitem6,billitem7,billitem8,billitem9,salecampaign,mduname) \
                          values('%s','%s','%s','%s','%s','%s','%s','%s', \
                     '%s','%s','%s','%s','%s','%s','5 維修','030 維修','%s','N','%s','%s',0,0,0,'%s','%s','%s','%s', \
                     '%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','3','%s','%s','%s',convert(varchar(19),getdate(),121),'%s','%s',%s,'%s','%s')" % \
                     (a_row[0],wkno,custid,custname,custgender,custbirth,bornmonth,personid,foreignyn,custstatus,custkind01, \
                      servicename,servicename,servicename,calltypelv4,contractno,contractno,addrno,nowcount,telenum01,cellphone01, \
                      linkid,nodeno,netid,mscity,msdistrict,msroad,address_str,a_row[2],a_row[11],mscomment,a_row[15],servname, \
                      servname,createname,book_flag,billitem_sql,salecampaign,mduname)
            try:
                pass # swallow modify
                #cur.execute(ins0300sql)
                #con.commit()
            except Exception, msg:
                print msg
                print ins0300sql
                continue
            ins0301sql = "insert into ms0301(companyno,custid,subsid,worksheet,sheetsno,sheetstatus,servicename, \
                         chargename,salekind,singlesn,smartcard,msvalue,chargekind,billprint,assignsheet, \
                         acceptdate,bookdate,workteam,msremark,listprd,listprice,billprice,billqty,billamt, \
                         billprd,getprice,getqty,getamt,getprd,createtime,createname,packagename,workcause) values('%s','%s','%s','%s',1,'0.預約','%s','%s', \
                     'Z 維修','%s','%s',3,19,0,'%s',convert(varchar(19),getdate(),121),'%s','%s','',0,0,0,0,0,0,0,0,0,0,convert(varchar(19),getdate(),121),'%s','%s','%s')" % \
                     (a_row[0],custid,a_row[1],wkno,servicename,chargename,singlesn,smartcard,wkno,a_row[15], \
                      servname,createname,salecampaign,calltypelv4)
            try:
                pass # swallow modify
                #print ins0301sql
                #cur.execute(ins0301sql)
                #con.commit()
            except Exception, msg:
                print msg
                print ins0301sql
                continue

        if tvposition!='' or tvsetup!='' or tvsize!='':
            option_sql = ''
            if tvposition!='':
                option_sql = "tvposition='%s'" % (tvposition)
            if tvsetup!='':
                if option_sql!='':
                    option_sql = "%s,tvsetup='%s'" % (option_sql, tvsetup)
                else:
                    option_sql = "tvsetup='%s'" % (tvsetup)
            if tvsize!='':
                if option_sql!='':
                    option_sql = "%s,tvsize='%s'" % (option_sql, tvsize)
                else:
                    option_sql = "tvsize='%s'" % (tvsize)
            upd0200sql = "update ms0200 set %s where companyno='%s' and subsid='%s'" % (option_sql, a_row[0], a_row[1])
            try:
                pass # swallow modify
                #cur.execute(upd0200sql)
                #con.commit()
            except Exception, msg:
                print msg
                pass
        if skip_flag==1:
            oraupdsql = "update cti010 set coss_id='%s',coss_status='CLOSE' where callin_history_id='%ld'" % (wkno, a_row[19])
        else:
            oraupdsql = "update cti010 set coss_id='%s',inbound_3=%d,dispatch_cnt_7=%d,dispatch_cnt_28=%d where callin_history_id='%ld'" % (wkno, p_inbound_cnt_3, p_disp_cnt_7, p_disp_cnt_28, a_row[19])
        print oraupdsql
        oracon_cti.execone(oraupdsql)
        oracon_cti.commit()
        sys.stdout.flush()
      except Exception, msg:
          print msg
          pass
          sys.stdout.flush()
          continue

else:
    print 'No data'

if oracon_oems is not None:
    oracon_oems.se_close()
if oracon_cti is not None:
    oracon_cti.se_close()
con.close()
