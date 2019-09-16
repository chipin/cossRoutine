#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
#
# 430101 HFC品質改善單 - 區域性訊號異常
# 430102 HFC品質改善單 - CM品質US-SNR異常
# 430103 HFC品質改善單 - CM品質T3異常
#
import os,sys,time
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

def OEMS_unity(so, node, subtype, msg, alert, city, district, servicename, subsid, subsname, addrname, mduname, link):
    global oracon, ora_oems, so_name

    print so, node, subtype, msg, alert, city, district, servicename, subsid, subsname, addrname, mduname, link

    if subtype == 430101:
        reason = "區域性訊號異常(%s,%s)" % (so, node)
    elif subtype == 430102:
        reason = "CM品質US-SNR異常(%s,%s)" % (so, node)
    elif subtype == 430103:
        reason = "CM品質T3異常(%s,%s)" % (so, node)

    node_info = "%s-%s" % (so, node)

    if subtype == 430101:
        msg = "訂編(%d)區域性訊號異常, %s" % (subsid, msg)
        #oraqrysql = "select a.sid,a.status from oems_tickets_main a inner join oems_impact_subscrid b on b.sid=a.sid \
        #             where a.normal_flag='I' and a.type='4301' and a.subtype='%d' and a.close_date is null and a.operator='%d' and a.impact_list='%s' and b.subsid='%d'" % (subtype, so_name[so], node_info, subsid)
    else:
        pass
        #oraqrysql = "select sid,status from oems_tickets_main where normal_flag='I' and type='4301' and subtype='%d' and close_date is null and operator='%d' and impact_list='%s'" % (subtype, so_name[so], node_info)
    oraqrysql = "select sid,status from oems_tickets_main where normal_flag='I' and type='4301' and subtype='%d' and close_date is null and operator='%d' and impact_list='%s'" % (subtype, so_name[so], node_info)
    sid = -1
    ostatus = 5110
    rs = ora_oems.execall(oraqrysql)
    if rs is not None and len(rs) > 0:
        for a_row in rs:
            sid = int(a_row[0])
            ostatus = int(a_row[1])
    print 'OEMS_ID:',sid
    if alert == 'Y':
        if sid < 0:
            oraupdsql = "begin insert into oems_tickets_main (status,type,subtype,reason,descr,operator,account,normal_flag,impact_list,key,sub_key) values ('%d','4301','%d','%s','%s','%s','CMTSMON','I','%s','3303','330305') return to_char(sid) into :1 ; end;" % (ostatus, subtype, reason, msg, so_name[so], node_info)
            print oraupdsql
            try:
                oems_sid_ary = ora_oems.db.BindingArray(1,12,'SQLT_STR')
                ora_oems.c.execute(oraupdsql, oems_sid_ary)
                sid = int(oems_sid_ary[0])
            except:
                print 'Exception: Unable to insert OEMS_TICKETS_MAIN'

            if sid > 0:
                oraupdsql = "insert into oems_impact (sid,type,value,companyno,getimpactsubsid,result,node,area,createtime) values (%d,'NODE','%s','%s',sysdate,'OK','%s','%s-%s',sysdate)" % (sid, node, so, node, city, district)
                print oraupdsql
                try:
                    ora_oems.execone(oraupdsql)
                except:
                    print 'Exception: Unable to insert OEMS_IMPACT'

                if subtype == 430101:
                    oraupdsql = "insert into oems_impact_subscrid (sid,companyno,subsid,servicename,subsname,nodeno,addrname,mduname,linkid,create_date) values (%d,'%s','%s','%s','%s','%s','%s','%s','%s',sysdate)" % (sid, so, subsid, servicename, subsname, node, addrname, mduname, link)
                    print oraupdsql
                    try:
                        ora_oems.execone(oraupdsql)
                    except:
                        print 'Exception: Unable to insert OEMS_IMPACT_SUBSCRID'

        oraupdsql = "insert into oems_tickets_log (sid,status_date,orig_status,status,descr,account) values (%d,sysdate,%d,%d,'%s','CMTSMON')" % (sid,ostatus,ostatus,msg)
        print oraupdsql
        try:
            ora_oems.execone(oraupdsql)
        except:
            print 'Exception: Unable to insert OEMS_TICKETS_LOG'
    elif sid > 0:
        new_status = ostatus
        if alert == 'C' and ostatus == 5104:
            oraupdsql = ''
            if subtype == 430102:
                oraupdsql = "update node_info set alert='N',ceasetime=sysdate where companyno='%s' and node='%s'" % (so, node)
            elif subtype == 430103:
                oraupdsql = "update node_info set t3_alert='N',t3_ceasetime=sysdate where companyno='%s' and node='%s'" % (so, node)
            if oraupdsql != None and len(oraupdsql) > 0:
                print oraupdsql
                try:
                    oracon.execone(oraupdsql)
                    oracon.commit()
                except:
                    print 'Exception: Unable to update NODE_INFO'

            new_status = 5105
            oraupdsql = "update oems_tickets_main set status='5105',close_date=sysdate where sid=%d and status='5104'" % (sid)
            print oraupdsql
            print 'Close:',sid
            try:
                ora_oems.execone(oraupdsql)
            except:
                print 'Exception: Unable to update OEMS_TICKETS_MAIN'

        oraupdsql = "insert into oems_tickets_log (sid,status_date,orig_status,status,descr,account) values (%d,sysdate,%d,%d,'%s','CMTSMON')" % (sid,ostatus,new_status,msg)
        print oraupdsql
        try:
            ora_oems.execone(oraupdsql)
        except:
            print 'Exception: Unable to update OEMS_TICKETS_LOG'

    ora_oems.commit()


if len(sys.argv) != 2:
    print 'usage:',sys.argv[0],'CompanyNo'
    sys.exit(0)

so = sys.argv[1]

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print '['+nowdate+'] START'

oracon = ORA('nms@cnis')
if not oracon.db:
    sys.exit(0)

ora_oems = ORA('oems@kbro_nmsdb')
if not ora_oems.db:
    sys.exit(0)

so_name = {}
qry = "select companyno,oemsno from so where oemsno is not null"
rs = oracon.execall(qry)
if rs != None and len(rs) > 0:
    for a_row in rs:
        so_name[a_row[0]] = int(a_row[1])

# ulrcvpwr v1 RXPWR   CmStatusRxPower   CMTS上行接收功
# dlrcvpwr v2 CMRXPWR DSPower.3         CM下行接收功率
# cmulpwr  v3 CMTXPWR CmStatusTxPower.2 CM上行發射功率

#
qry = "select companyno,node,sum(q_rxpwr) q_rxpwr,sum(q_cmrxpwr) q_cmrxpwr,sum(q_cmtxpwr) q_cmtxpwr,sum(q_dlsnr) q_dlsnr,sum(q_ulsnr) q_ulsnr,sum(q_rxpwr2) q_rxpwr2,sum(q_cmtxpwr2) q_cmtxpwr2,sum(q_ulsnr2) q_ulsnr2,sum(q_t3) q_t3,sum(q_t4) q_t4 from v_cnis_cm_qos where companyno='%s' group by companyno,node" % (so)
print qry
rs = oracon.execall(qry)
if rs != None and len(rs) > 0:
    for a_row in rs:
        companyno = a_row[0]
        nodeno = a_row[1]
        q_rxpwr = int(a_row[2])
        q_cmrxpwr = int(a_row[3])
        q_cmtxpwr = int(a_row[4])
        q_dlsnr = int(a_row[5])
        q_ulsnr = int(a_row[6])
        q_rxpwr2 = int(a_row[7])
        q_cmtxpwr2 = int(a_row[8])
        q_ulsnr2 = int(a_row[9])
        q_t3 = int(a_row[10])
        q_t4 = int(a_row[11])
        print companyno,nodeno,q_rxpwr,q_cmrxpwr,q_cmtxpwr,q_dlsnr,q_ulsnr,q_rxpwr2,q_cmtxpwr2,q_ulsnr2,q_t3,q_t4

        oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','',%d,'RXPWR'); end;" % (companyno, nodeno, q_rxpwr)
        try:
            oracon.execone(oraupdsql)
        except Exception, detail:
            print '%s -> %s' % (oraupdsql, detail)

        oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','',%d,'CMRXPWR'); end;" % (companyno, nodeno, q_cmrxpwr)
        try:
            oracon.execone(oraupdsql)
        except Exception, detail:
            print '%s -> %s' % (oraupdsql, detail)

        oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','',%d,'CMTXPWR'); end;" % (companyno, nodeno, q_cmtxpwr)
        try:
            oracon.execone(oraupdsql)
        except Exception, detail:
            print '%s -> %s' % (oraupdsql, detail)

        oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','',%d,'DLSNR'); end;" % (companyno, nodeno, q_dlsnr)
        try:
            oracon.execone(oraupdsql)
        except Exception, detail:
            print '%s -> %s' % (oraupdsql, detail)

        oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','',%d,'ULSNR'); end;" % (companyno, nodeno, q_ulsnr)
        try:
            oracon.execone(oraupdsql)
        except Exception, detail:
            print '%s -> %s' % (oraupdsql, detail)

        oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','',%d,'RXPWR2'); end;" % (companyno, nodeno, q_rxpwr2)
        try:
            oracon.execone(oraupdsql)
        except Exception, detail:
            print '%s -> %s' % (oraupdsql, detail)

        oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','',%d,'CMTXPWR2'); end;" % (companyno, nodeno, q_cmtxpwr2)
        try:
            oracon.execone(oraupdsql)
        except Exception, detail:
            print '%s -> %s' % (oraupdsql, detail)

        oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','',%d,'ULSNR2'); end;" % (companyno, nodeno, q_ulsnr2)
        try:
            oracon.execone(oraupdsql)
        except Exception, detail:
            print '%s -> %s' % (oraupdsql, detail)

        oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','',%d,'T3'); end;" % (companyno, nodeno, q_t3)
        try:
            oracon.execone(oraupdsql)
        except Exception, detail:
            print '%s -> %s' % (oraupdsql, detail)

        oraupdsql = "begin proc_cnis_upd_node_info_ext('%s','%s','',%d,'T4'); end;" % (companyno, nodeno, q_t4)
        try:
            oracon.execone(oraupdsql)
        except Exception, detail:
            print '%s -> %s' % (oraupdsql, detail)

        oracon.commit()
        sys.stdout.flush()

#
node_descr = {}
node_arr = {}
node_cnt = 0
qry = "select node,alert,t3_alert from node_info where companyno='%s' and monitor='Y' order by node" % (so)
print qry
rs = oracon.execall(qry)
if rs != None and len(rs) > 0:
    for a_row in rs:
        node = a_row[0]
        alert = a_row[1]
        t3_alert = a_row[2]
        node_arr['USSNR-A-'+node] = alert
        node_arr['USSNR-B-'+node] = 'N'
        node_arr['T3-A-'+node] = t3_alert
        node_arr['T3-B-'+node] = 'N'
        node_arr['NODE-'+str(node_cnt)] = node
        node_cnt = node_cnt+1
else:
    print "Error: NODE_INFO is empty"

#
#qry = "select node,city,district,cm_cnt,q_rxpwr,q_cmrxpwr,q_cmtxpwr,q_dlsnr,q_ulsnr,q_rxpwr2,q_cmtxpwr2,q_ulsnr2,q_t3,q_t4 from v_cnis_cm_qos_stat where companyno='%s'" % (so)
qry = "select node,city,district,sum(cm_cnt) cm_cnt,sum(q_rxpwr) q_rxpwr,sum(q_cmrxpwr) q_cmrxpwr,sum(q_cmtxpwr) q_cmtxpwr,sum(q_dlsnr) q_dlsnr,sum(q_ulsnr) q_ulsnr,sum(q_rxpwr2) q_rxpwr2,sum(q_cmtxpwr2) q_cmtxpwr2,sum(q_ulsnr2) q_ulsnr2,sum(q_t3) q_t3,sum(q_t4) q_t4 from v_cnis_cm_qos_stat where companyno='%s'  group by node,city,district" % (so)
print qry
rs = oracon.execall(qry)
if rs != None and len(rs) > 0:
    for a_row in rs:
        node = a_row[0]
        city = a_row[1]
        district = a_row[2]
        cm_cnt = int(a_row[3])
        rxpwr = int(a_row[4])
        cm_rxpwr = int(a_row[5])
        cm_txpwr = int(a_row[6])
        dlsnr = int(a_row[7])
        ulsnr = int(a_row[8])
        rxpwr2 = int(a_row[9])
        cm_txpwr2 = int(a_row[10])
        ulsnr2 = int(a_row[11])
        t3 = int(a_row[12])
        t4 = int(a_row[13])

        node_descr['USSNR-'+node] = "總數:%d,USSNR:%d,USSNR2:%d,RXPWR:%d,RXPWR2:%d,CMRXPWR:%d,CMTXPWR:%d,CMTXPWR2:%d,DSSNR:%d,T3:%d,T4:%d" % (cm_cnt,ulsnr,ulsnr2,rxpwr,rxpwr2,cm_rxpwr,cm_txpwr,cm_txpwr2,dlsnr,t3,t4)
        node_descr['T3-'+node]    = "總數:%d,T3:%d,T4:%d,RXPWR:%d,RXPWR2:%d,CMRXPWR:%d,CMTXPWR:%d,CMTXPWR2:%d,USSNR:%d,USSNR2:%d,DSSNR:%d" % (cm_cnt,t3,t4,rxpwr,rxpwr2,cm_rxpwr,cm_txpwr,cm_txpwr2,ulsnr,ulsnr2,dlsnr)
        node_descr['QOS-'+node]   = "總數:%d,RXPWR:%d,RXPWR2:%d,CMRXPWR:%d,CMTXPWR:%d,CMTXPWR2:%d,USSNR:%d,USSNR2:%d,DSSNR:%d,T3:%d,T4:%d" % (cm_cnt,rxpwr,rxpwr2,cm_rxpwr,cm_txpwr,cm_txpwr2,ulsnr,ulsnr2,dlsnr,t3,t4)

        ussnr_flag = 0
        if cm_cnt>30 and ((ulsnr*100/cm_cnt)>30 or (ulsnr2*100/cm_cnt)>30):
            ussnr_flag = 1
        elif ulsnr>30 or ulsnr2>30:
            ussnr_flag = 1
        elif cm_cnt>30 and (ulsnr*100/cm_cnt)<10 and (ulsnr2*100/cm_cnt)<10:
            ussnr_flag = 9
        elif ulsnr<3 and ulsnr2<3:
            ussnr_flag = 9

        t3_flag = 0
        if cm_cnt>5 and (t3*100/cm_cnt)>50:
            t3_flag = 1
        elif t3>50:
            t3_flag = 1
        elif cm_cnt>5 and (t3*100/cm_cnt)<10:
            t3_flag = 9
        elif t3<3:
            t3_flag = 9

        if ussnr_flag==1:
            try:
                alert = node_arr['USSNR-A-'+node]
            except:
                print "%s not exist in the NODE_ARR" % ('USSNR-A-'+node)
                alert = ''
            print 'USSNR:',so,node,cm_cnt,ulsnr,ulsnr2,alert
            if alert=='N':
                msg = "NODE(%s)所屬CM USSNR品質低於標準. %s" % (node, node_descr['USSNR-'+node])
                OEMS_unity(so, node, 430102, msg, 'Y', city, district, '', '', '', '', '', '')
                node_arr['USSNR-B-'+node] = 'Y'
                oraupdsql = "update node_info set alert='Y',alerttime=sysdate where companyno='%s' and node='%s'" % (so, node);
                print oraupdsql
                try:
                    oracon.execone(oraupdsql)
                    oracon.commit()
                except:
                    print 'Exception: Unable to update NODE_INFO'
            elif alert=='Y':
                node_arr['USSNR-B-'+node] = 'Y'
        elif ussnr_flag==9:
            node_arr['USSNR-B-'+node] = 'C'

        if t3_flag==1:
            try:
                alert = node_arr['T3-A-'+node]
            except:
                print "%s not exist in the NODE_ARR" % ('T3-A-'+node)
                alert = ''
            print 'T3:',so,node,cm_cnt,t3,alert
            if alert=='N':
                msg = "NODE(%s)所屬CM T3品質低於標準. %s" % (node, node_descr['T3-'+node])
                OEMS_unity(so, node, 430103, msg, 'Y', city, district, '', '', '', '', '', '')
                node_arr['T3-B-'+node] = 'Y'
                oraupdsql = "update node_info set t3_alert='Y',t3_alerttime=sysdate where companyno='%s' and node='%s'" % (so, node);
                print oraupdsql
                try:
                    oracon.execone(oraupdsql)
                    oracon.commit()
                except:
                    print 'Exception: Unable to update NODE_INFO'
            elif alert=='Y':
                node_arr['T3-B-'+node] = 'Y'
        elif t3_flag==9:
            node_arr['T3-B-'+node] = 'C'

        sys.stdout.flush()

for i in range(0, node_cnt):
    node = node_arr['NODE-'+str(i)]
    try:
        if node_arr['USSNR-A-'+node]=='Y' and node_arr['USSNR-B-'+node]=='N':
            msg = "NODE(%s)所屬CM USSNR品質已低於異常標準, 但未達結案標準. %s" % (node, node_descr['USSNR-'+node])
            OEMS_unity(so, node, 430102, msg, 'N', '', '', '', '', '', '', '', '')
            oraupdsql = "update node_info set alert='U',ceasetime=sysdate where companyno='%s' and node='%s'" % (so, node)
            print oraupdsql
            try:
                oracon.execone(oraupdsql)
                oracon.commit()
            except:
                print 'Exception: Unable to update NODE_INFO'
        elif (node_arr['USSNR-A-'+node]=='Y' or node_arr['USSNR-A-'+node]=='U') and node_arr['USSNR-B-'+node]=='C':
            msg = "NODE(%s)所屬CM USSNR品質已符合結案標準. %s" % (node, node_descr['USSNR-'+node])
            OEMS_unity(so, node, 430102, msg, 'C', '', '', '', '', '', '', '', '')
            #oraupdsql = "update node_info set alert='N',ceasetime=sysdate where companyno='%s' and node='%s'" % (so, node)
            #print oraupdsql
            #try:
            #    oracon.execone(oraupdsql)
            #    oracon.commit()
            #except:
            #    print 'Exception: Unable to update NODE_INFO'

        if node_arr['T3-A-'+node]=='Y' and node_arr['T3-B-'+node]=='N':
            msg = "NODE(%s)所屬CM T3品質已低於異常標準, 但未達結案標準. %s" % (node, node_descr['T3-'+node])
            OEMS_unity(so, node, 430103, msg, 'N', '', '', '', '', '', '', '', '')
            oraupdsql = "update node_info set t3_alert='U',t3_ceasetime=sysdate where companyno='%s' and node='%s'" % (so, node)
            print oraupdsql
            try:
                oracon.execone(oraupdsql)
                oracon.commit()
            except:
                print 'Exception: Unable to update NODE_INFO'
        elif (node_arr['T3-A-'+node]=='Y' or node_arr['T3-A-'+node]=='U') and node_arr['T3-B-'+node]=='C':
            msg = "NODE(%s)所屬CM T3品質已符合結案標準. %s" % (node, node_descr['T3-'+node])
            OEMS_unity(so, node, 430103, msg, 'C', '', '', '', '', '', '', '', '')
            #oraupdsql = "update node_info set t3_alert='N',t3_ceasetime=sysdate where companyno='%s' and node='%s'" % (so, node)
            #print oraupdsql
            #try:
            #    oracon.execone(oraupdsql)
            #    oracon.commit()
            #except:
            #    print 'Exception: Unable to update NODE_INFO'

    except:
        pass
    sys.stdout.flush()

#
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

qry = "select a.companyno,a.worksheet,b.subsid,c.subsname,a.mduname,a.mscitya,a.msdistricta,a.instaddrname,b.servicename,a.nodeno,a.linkid,b.backcause1 \
       from ms0300 a with (nolock) \
       inner join ms0301 b with (nolock) on b.companyno=a.companyno and b.worksheet=a.worksheet \
       inner join ms0200 c with (nolock) on c.companyno=a.companyno and c.subsid=b.subsid \
       where a.companyno='%s' and substring(a.workkind,1,1)='5' and substring(b.servicename,1,1) in ('1','2','3','7','9') \
       and substring(b.sheetstatus,1,1) = '4' and substring(b.backcause1,1,5) = 'C0805' and b.cleandate >= getdate()-(63.0/(24*60)) \
       group by a.companyno,a.worksheet,b.subsid,c.subsname,a.mduname,a.mscitya,a.msdistricta,a.instaddrname,b.servicename,a.nodeno,a.linkid,b.backcause1" % (so)
print qry
cur.execute(qry)
workarr = cur.fetchall()
for wrk in workarr:
    companyno = wrk[0]
    worksheet = wrk[1]
    subsid = int(wrk[2])
    subsname = wrk[3]
    mduname = wrk[4]
    city = wrk[5]
    district = wrk[6]
    addrname = wrk[7]
    servicename = wrk[8]
    nodeno = wrk[9]
    linkid = wrk[10]
    backcause = wrk[11]

    descr = ''
    try:
        descr = "NODE(%s)所屬CM品質: %s" % (nodeno, node_descr['QOS-'+nodeno])
    except:
        print "%s not exist in the NODE_DESCR" % ('QOS-'+nodeno)

    OEMS_unity(companyno, nodeno, 430101, descr, 'Y', city, district, servicename, subsid, subsname, addrname, mduname, linkid)
    sys.stdout.flush()

# 更新430101的狀態5104 -> 5105
oraupdsql = "update oems_tickets_main set status='5105',close_date=sysdate where normal_flag='I' and type='4301' and subtype='430101' and status='5104'"
print oraupdsql
try:
    ora_oems.execone(oraupdsql)
    ora_oems.commit()
    #pass
except:
    print 'Exception: Unable to update OEMS_TICKETS_MAIN'

# 每日回填最新NODE品質至HFC改善單
hour = time.strftime("%H", time.localtime())
if hour == '08':
    oraqrysql = "select sid,status,subtype,substr(impact_list,1,instr(impact_list,'-')-1) companyno,substr(impact_list,instr(impact_list,'-')+1) node from oems_tickets_main where normal_flag='I' and type='4301' and close_date is null and operator='%d' order by create_date asc" % (so_name[so])
    print oraqrysql
    rs = ora_oems.execall(oraqrysql)
    if rs is not None and len(rs) > 0:
        i = 0
        for a_row in rs:
            sid = int(a_row[0])
            status = int(a_row[1])
            subtype = int(a_row[2])
            node = a_row[4]

            descr = ''
            if subtype == 430101:
                try:
                    descr = "NODE(%s)所屬CM品質: %s" % (node, node_descr['QOS-'+node])
                except:
                    print "%s not exist in the NODE_DESCR" % ('QOS-'+node)
            elif subtype == 430102:
                try:
                    descr = "NODE(%s)所屬CM品質: %s" % (node, node_descr['USSNR-'+node])
                except:
                    print "%s not exist in the NODE_DESCR" % ('USSNR-'+node)
            elif subtype == 430103:
                try:
                    descr = "NODE(%s)所屬CM品質: %s" % (node, node_descr['T3-'+node])
                except:
                    print "%s not exist in the NODE_DESCR" % ('T3-'+node)

            oraupdsql = "insert into oems_tickets_log (sid,status_date,orig_status,status,descr,account) values (%d,sysdate,%d,%d,'%s','CMTSMON')" % (sid,status,status,descr)
            print oraupdsql
            try:
                ora_oems.execone(oraupdsql)
                if (i%30)==0:
                    ora_oems.commit()
            except:
                print 'Exception: Unable to insert OEMS_TICKETS_LOG'
            i = i+1
        if i > 0:
            ora_oems.commit()

if con is not None:
    con.close()
if oracon.db is not None:
    oracon.se_close()
if ora_oems.db is not None:
    ora_oems.se_close()

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] END\n" % (nowdate)
