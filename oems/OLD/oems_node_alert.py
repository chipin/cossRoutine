#!/bin/env python
# -*- coding: big5 -*-
import sys,datetime,time
import pymssql
from oraclass import ORA

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "=> [%s]" % (tme)

con = pymssql.connect(dsn='cnis_web@TFMCossMS_CP950_HUGE')
cur = con.cursor()
con_qry = pymssql.connect(dsn='cnis_web@TFMCossMS_CP950_HUGE')
cur_qry = con_qry.cursor()

oracon_upd = ORA('OEMS@KBRO_NMSDB')
oracon_cti = ORA('CTI@CNIS')

so_name = {}
oraqrysql = "select name,id from oems_mapping where type='OPERATOR' and name is not null"
rs = oracon_upd.execall(oraqrysql)
if rs != None and len(rs) > 0:
    for a_row in rs:
       so_name[a_row[0]] = int(a_row[1])

#query="select nodeno,companyno,mscitya,msdistricta,count(*) cnt from v_tfm_node_alert where servicename<>'8 LS' and createtime>=getdate()-2 group by nodeno,companyno,mscitya,msdistricta having count(*)>4 union select nodeno,companyno,mscitya,msdistricta,-1 cnt from v_tfm_node_alert where servicename='8 LS' group by nodeno,companyno,mscitya,msdistricta"
query="select nodeno,companyno,mscitya,msdistricta,count(*) cnt from v_tfm_node_alert where servicename<>'8 LS' and createtime>=getdate()-1 group by nodeno,companyno,mscitya,msdistricta having count(*)>4 union select nodeno,companyno,mscitya,msdistricta,-1 cnt from v_tfm_node_alert where servicename='8 LS' group by nodeno,companyno,mscitya,msdistricta"
print query
cur.execute(query)
node_arr = {}
i = 0
while 1:
  curarr = cur.fetchmany(100)
  i = i+1
  if curarr:
    xlen = len(curarr)
    for ii in range(0, xlen):
        nodeno = curarr[ii][0]
        companyno = curarr[ii][1]
        mscitya = curarr[ii][2]
        msdistricta = curarr[ii][3]
        district = "%s-%s" % (curarr[ii][2], curarr[ii][3])
        alert_cnt = curarr[ii][4]
        print companyno,nodeno,district,alert_cnt
        if alert_cnt>0:
            sidqry = "select servicename,count(*) cnt from ms0200 a with (nolock),ms0102 b with (nolock) where a.companyno=b.companyno and a.custid=b.custid and b.addrno=0 and a.subsid in (select subsid from v_tfm_node_alert where companyno='%s' and nodeno='%s') group by servicename" % (companyno, nodeno)
            cur_qry.execute(sidqry);
            sidarr = cur_qry.fetchall()
            reason_str = "網點# %s 已有[%d]戶報修," % (nodeno, alert_cnt)
            for ssid in sidarr:
                reason_str = "%s %s共%d件," % (reason_str, ssid[0], ssid[1])

            roadqry = "select b.msroad from ms0200 a with (nolock),ms0102 b with (nolock) where a.companyno=b.companyno and a.custid=b.custid and b.AddrNo ='0' and a.subsid in (select subsid from v_tfm_node_alert where companyno='%s' and nodeno='%s') group by b.msroad" % (companyno, nodeno)
            cur_qry.execute(roadqry);
            roadarr = cur_qry.fetchall()

            descr_str = reason_str
            node_str = "%s-%s" % (companyno, nodeno)
            node_arr[node_str] = 9
            sid = 0
            roadflag = 0
            updflag = 0
            if nodeno and companyno and alert_cnt:
                oraqrysql = "select sid,impact_list from oems_tickets_main where ((type in (3107) and subtype in (310701,310703)) or ticket_id is not null) and status<=5104 and impact_list='%s' and account='TFM-COSS'" % (node_str)
                rs = oracon_upd.execall(oraqrysql)
                if rs != None and len(rs) > 0:
                    for a_row in rs:
                        sid = a_row[0]
                        #orig_node_str = a_row[1]
                    oraupdsql = "update oems_tickets_main set reason='%s',descr='%s' where sid='%d'" % (reason_str,descr_str, sid)
                    updflag = 1
                    roadflag = 1
                else:
                    taipower_sid = ''
                    subtype = 310701
                    oraqrysql = "select sid from oems_tickets_main where account='SWALLOW' and reason='台電計畫性停電' and normal_flag='P' and \
                                 sysdate between impact_bg_date and impact_end_date and operator='%d' and descr like '%%%s%%' order by create_date desc" % (so_name[companyno], nodeno)
                    print oraqrysql
                    rs = oracon_upd.execall(oraqrysql)
                    if rs != None and len(rs) > 0:
                        for a_row in rs:
                            taipower_sid = (int)(a_row[0])
                            subtype = 310703
                            break

                    oraupdsql = "insert into oems_tickets_main(status,type,subtype,reason,descr,create_date,operator,account,normal_flag,impact_list,location) \
                                 values('5100',3107,'%d','%s','%s',sysdate,'%s','TFM-COSS','B','%s','%s')" \
                                 % (subtype, reason_str, descr_str, so_name[companyno], node_str, taipower_sid)
                    roadflag = 1
                    tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                    print "[%s]" % (tme)
                try:
                    print oraupdsql
                    oracon_upd.execone(oraupdsql)
                    oracon_upd.commit()
                except Exception, detail:
                    print '%s,%s,%s -> %s' % (companyno, nodeno, alert_cnt, detail)
                    pass
            if roadflag==1:
                oraqrysql = "select sid from oems_tickets_main where type in (3107) and subtype in (310701,310703) and status<=5104 and impact_list='%s' and account='TFM-COSS'" % (node_str)
                rs = oracon_upd.execall(oraqrysql)
                if rs != None and len(rs) > 0:
                    for a_row in rs:
                        sid = a_row[0]

                    if updflag==0:
                        orainssql = "insert into oems_impact(sid,type,value,companyno,node,area) values('%d','NODE','%s','%s','%s','%s')" % (sid, nodeno, companyno, nodeno, district)
                        try:
                            print orainssql
                            oracon_upd.execone(orainssql)
                        except Exception, detail:
                            print detail
                            pass
                        oracon_upd.commit()

                    # Checking duplicated road
                    oraqrysql = "select value from oems_impact where type='ROAD' and sid='%d'" % (sid)
                    rs = oracon_upd.execall(oraqrysql)
                    if rs != None and len(rs) > 0:
                        saved_rd = rs
                    else:
                        saved_rd = None

                    for rd in roadarr:
                        if saved_rd is not None:
                            duplicated_flag = 0
                            for svrd in saved_rd:
                                if svrd[0]==rd[0]:
                                    duplicated_flag = 1
                                    break
                            if duplicated_flag==1:
                                print 'Skip %s' % (rd[0])
                                continue
                        orainssql = "insert into oems_impact(sid,type,value,companyno,node,area) values('%d','ROAD','%s','%s','%s','%s')" % (sid, rd[0], companyno, nodeno, district)
                        print orainssql
                        try:
                            oracon_upd.execone(orainssql)
                        except Exception, detail:
                            print detail
                            pass
                        oracon_upd.commit()

                    # update CTI010 via WorkSheetNo
                    worksheet_arr = []
                    worksheet_str = ''
                    workqry="select worksheet from v_tfm_node_alert where servicename<>'8 LS' and createtime>=getdate()-1 and companyno='%s' and nodeno='%s' and mscitya='%s' and msdistricta='%s'" % (companyno, nodeno, mscitya, msdistricta)
                    cur_qry.execute(workqry);
                    workarr = cur_qry.fetchall()
                    if workarr:
                        wlen = len(workarr)
                        for ww in range(0, wlen):
                            worksheet = workarr[ww][0]
                            if worksheet not in worksheet_arr:
                                worksheet_arr.append(worksheet)

                    if worksheet_arr:
                        worksheet_str = "','" . join(worksheet_arr)
                    print 'worksheet:',companyno,nodeno,sid,worksheet_arr

                    if worksheet_str != None and len(worksheet_str) > 0 and sid != None and sid > 0:
                        oraupdsql = "update cti010 set ext_oems_id='%d' where so='%d' and coss_id in ('%s') and coss_id is not null and (ext_oems_id is null or ext_oems_id = 0)" % (sid, int(companyno), worksheet_str)
                        print oraupdsql
                        try:
                            oracon_cti.execone(oraupdsql)
                            oracon_cti.commit()
                            pass
                        except Exception, detail:
                            print detail

                #mailsql = "begin BOMB_TICKET_SEND_MAIL(%d);end;" % (sid)
                #oracon_upd.execone(mailsql)
                #oracon_upd.commit()
    #print "%c%6d" % (chr(13),i),
    sys.stdout.flush()
  else:
    break

#query="select nodeno,companyno,mscitya,msdistricta,count(*) cnt from v_tfm_node_alert where servicename<>'8 LS' and createtime>=getdate()-(1.5/24) group by nodeno,companyno,mscitya,msdistricta having count(*) in (3,4) and datediff(minute,min(createtime),max(createtime))<60"
query="select nodeno,companyno,mscitya,msdistricta,count(*) cnt from v_tfm_node_alert where servicename<>'8 LS' and createtime>=getdate()-(1.0/24) group by nodeno,companyno,mscitya,msdistricta having count(*) in (3,4)"

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print ""
print "[%s]" % (tme)
print query
cur.execute(query)
i = 0
while 1:
  curarr = cur.fetchmany(100)
  i = i+1
  if curarr:
    xlen = len(curarr)
    for ii in range(0, xlen):
        nodeno = curarr[ii][0]
        companyno = curarr[ii][1]
        mscitya = curarr[ii][2]
        msdistricta = curarr[ii][3]
        district = "%s-%s" % (curarr[ii][2], curarr[ii][3])
        alert_cnt = curarr[ii][4]
        print 'Alert 3 in one hour ->',companyno,nodeno,district,alert_cnt
        if alert_cnt>0:
            sidqry = "select servicename,count(*) cnt from ms0200 a with (nolock),ms0102 b with (nolock) where a.companyno=b.companyno and a.custid=b.custid and b.addrno=0 and a.subsid in (select subsid from v_tfm_node_alert where companyno='%s' and nodeno='%s') group by servicename" % (companyno, nodeno)
            cur_qry.execute(sidqry);
            sidarr = cur_qry.fetchall()
            reason_str = "網點# %s 1小時內已有[%d]戶報修," % (nodeno, alert_cnt)
            for ssid in sidarr:
                reason_str = "%s %s共%d件," % (reason_str, ssid[0], ssid[1])

            roadqry = "select b.msroad from ms0200 a with (nolock),ms0102 b with (nolock) where a.companyno=b.companyno and a.custid=b.custid and b.AddrNo ='0' and a.subsid in (select subsid from v_tfm_node_alert where companyno='%s' and nodeno='%s') group by b.msroad" % (companyno, nodeno)
            #print roadqry
            cur_qry.execute(roadqry);
            roadarr = cur_qry.fetchall()

            descr_str = reason_str
            node_str = "%s-%s" % (companyno, nodeno)
            node_arr[node_str] = 9
            sid = 0
            roadflag = 0
            updflag = 0
            if nodeno and companyno and alert_cnt:
                oraqrysql = "select sid,impact_list from oems_tickets_main where ((type in (3107) and subtype in (310701,310703)) or ticket_id is not null) and status<=5104 and impact_list='%s' and account='TFM-COSS'" % (node_str)
                print oraqrysql
                rs = oracon_upd.execall(oraqrysql)
                if rs != None and len(rs) > 0:
                    for a_row in rs:
                        sid = a_row[0]
                        #orig_node_str = a_row[1]
                    # 建立路段影響範圍更新
                    #if orig_node_str==node_str:
                    #    continue
                    oraupdsql = "update oems_tickets_main set reason='%s',descr='%s' where sid='%d'" % (reason_str,descr_str, sid)
                    updflag = 1
                    roadflag = 1
                else:
                    taipower_sid = ''
                    subtype = 310701
                    oraqrysql = "select sid from oems_tickets_main where account='SWALLOW' and reason='台電計畫性停電' and normal_flag='P' and \
                                 sysdate between impact_bg_date and impact_end_date and operator='%d' and descr like '%%%s%%' order by create_date desc" % (so_name[companyno], nodeno)
                    print oraqrysql
                    rs = oracon_upd.execall(oraqrysql)
                    if rs != None and len(rs) > 0:
                        for a_row in rs:
                            taipower_sid = (int)(a_row[0])
                            subtype = 310703
                            break

                    oraupdsql = "insert into oems_tickets_main(status,type,subtype,reason,descr,create_date,operator,account,normal_flag,impact_list,location) \
                                 values('5100',3107,'%d','%s','%s',sysdate,'%s','TFM-COSS','B','%s','%s')" \
                                 % (subtype, reason_str, descr_str, so_name[companyno], node_str, taipower_sid)
                    #print oraupdsql
                    roadflag = 1
                    tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                    print "[%s]" % (tme)
                try:
                    print oraupdsql
                    oracon_upd.execone(oraupdsql)
                    oracon_upd.commit()
                except Exception, detail:
                    print '%s,%s,%s -> %s' % (companyno, nodeno, alert_cnt, detail)
                    pass
            if roadflag==1:
                oraqrysql = "select sid from oems_tickets_main where type in (3107) and subtype in (310701,310703) and status<=5104 and impact_list='%s' and account='TFM-COSS'" % (node_str)
                rs = oracon_upd.execall(oraqrysql)
                if rs != None and len(rs) > 0:
                    for a_row in rs:
                        sid = a_row[0]

                    if updflag==0:
                        orainssql = "insert into oems_impact(sid,type,value,companyno,node,area) values('%d','NODE','%s','%s','%s','%s')" % (sid, nodeno, companyno, nodeno, district)
                        try:
                            oracon_upd.execone(orainssql)
                        except Exception, detail:
                            print detail
                            pass
                        oracon_upd.commit()

                    # Checking duplicated road
                    oraqrysql = "select value from oems_impact where type='ROAD' and sid='%d'" % (sid)
                    rs = oracon_upd.execall(oraqrysql)
                    if rs != None and len(rs) > 0:
                        saved_rd = rs
                    else:
                        saved_rd = None

                    for rd in roadarr:
                        if saved_rd is not None:
                            duplicated_flag = 0
                            for svrd in saved_rd:
                                if svrd[0]==rd[0]:
                                    duplicated_flag = 1
                                    break
                            if duplicated_flag==1:
                                print 'Skip %s' % (rd[0])
                                continue
                        orainssql = "insert into oems_impact(sid,type,value,companyno,node,area) values('%d','ROAD','%s','%s','%s','%s')" % (sid, rd[0], companyno, nodeno, district)
                        print orainssql
                        try:
                            oracon_upd.execone(orainssql)
                        except Exception, detail:
                            print detail
                            pass
                        oracon_upd.commit()

                    # update CTI010 via WorkSheetNo
                    worksheet_arr = []
                    worksheet_str = ''
                    workqry="select worksheet from v_tfm_node_alert where servicename<>'8 LS' and createtime>=getdate()-(1.0/24) and companyno='%s' and nodeno='%s' and mscitya='%s' and msdistricta='%s'" % (companyno, nodeno, mscitya, msdistricta)
                    cur_qry.execute(workqry);
                    workarr = cur_qry.fetchall()
                    if workarr:
                        wlen = len(workarr)
                        for ww in range(0, wlen):
                            worksheet = workarr[ww][0]
                            if worksheet not in worksheet_arr:
                                worksheet_arr.append(worksheet)

                    if worksheet_arr:
                        worksheet_str = "','" . join(worksheet_arr)
                    print 'worksheet:',companyno,nodeno,sid,worksheet_arr

                    if worksheet_str != None and len(worksheet_str) > 0 and sid != None and sid > 0:
                        #oraqrysql = "select callin_history_id from cti010 where so='%s' and coss_id in ('%s')" % (companyno, worksheet_str)
                        #print oraqrysql
                        #rs = oracon_cti.execall(oraqrysql)
                        #if rs != None and len(rs) > 0:
                        #    for a_row in rs:
                        #        callin_history_id = int(a_row[0])
                        #        print callin_history_id

                        oraupdsql = "update cti010 set ext_oems_id='%d' where so='%d' and coss_id in ('%s') and coss_id is not null and (ext_oems_id is null or ext_oems_id = 0)" % (sid, int(companyno), worksheet_str)
                        print oraupdsql
                        try:
                            oracon_cti.execone(oraupdsql)
                            oracon_cti.commit()
                            pass
                        except Exception, detail:
                            print detail

                #mailsql = "begin BOMB_TICKET_SEND_MAIL(%d);end;" % (sid)
                #oracon_upd.execone(mailsql)
                #oracon_upd.commit()
  else:
      break

oraqrysql = "select sid,impact_list from oems_tickets_main where account='TFM-COSS' and status=5104"
rs = oracon_upd.execall(oraqrysql)
ticket_arr = {}
sid_arr = {}
ii = 0
if rs != None and len(rs) > 0:
    for a_row in rs:
        sid = a_row[0]
        implst = a_row[1]
        ticket_arr[ii] = implst
        sid_arr[implst] = sid
        ii = ii+1
jj = 0
while jj<ii:
    try:
        print ticket_arr[jj]
        print node_arr[ticket_arr[jj]]
    except:
        oraupdsql = "update oems_tickets_main set status=5105 where sid='%d'" % (sid_arr[ticket_arr[jj]])
        oracon_upd.execone(oraupdsql)
        oracon_upd.commit()
        print oraupdsql

#follow bomb close auto_alert tickets(aasql)
        aasql = "update oems_tickets_main set status='5123',close_date=sysdate where ticket_id='%d' and account='TFM-COSS'" % (sid_arr[ticket_arr[jj]])
        oracon_upd.execone(aasql)
        oracon_upd.commit()
        print aasql
        pass
    jj = jj+1

oracon_upd.commit()
if oracon_upd is not None:
    oracon_upd.se_close()
if oracon_cti is not None:
    oracon_cti.se_close()

con.close()
con_qry.close()
