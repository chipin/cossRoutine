#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import locale,re,threading
import MySQLdb
from oraclass import ORA
from pysnmpclass import snmpclass

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv) != 2:
    print 'usage:',sys.argv[0],'CompanyNo'
    sys.exit(0)

so = sys.argv[1]
startime = time.time()

locale.setlocale(locale.LC_NUMERIC, 'en_US.ISO8859-1') # 可以啟動locale.format的貨幣分隔符號

#I 品質改善單, A 自動告警, B 突發性障礙, 5113 TAC處理中, 5106 機線處理中, 13001 NOC, 13002 TAC, 13037 機線, 4304 流量告警改善單
def IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,alarm_type,alarm_status,alarm_msg):
    global oraoems, oems_sid

    print oemsno,companyno,ne_type,ne_id,ifindex,alarm_type,alarm_status,alarm_msg

    # OPERATOR: 改善單給SO, 自動告警及突發給NOC
    if alarm_type in ['IN_TOP','IN_MIN','IN_INC','IN_DEC','OUT_TOP','OUT_MIN','OUT_INC','OUT_DEC','NODATA']:
        operator = 13001
    else:
        operator = oemsno
        return

    if alarm_type in ['IN_MAX','OUT_MAX']:
        normal_flag = 'I'
        type = 4304
        subtype = ''
        if ne_type in ['CMTS','QAM']:
            status = 5106
        else:
            status = 5113
    elif alarm_type in ['IN_TOP','IN_MIN','OUT_TOP','OUT_MIN']:
        normal_flag = 'B'
        type = 3111
        subtype = 311101
        status = 5100
    else:
        normal_flag = 'A'
        type = 3111
        subtype = 311109
        status = 5120

    alarm_reaon = ne_type + ' 流量異常'
    if alarm_type == 'IN_TOP':
        alarm_reaon = alarm_reaon + '(RX超標)'
    elif alarm_type == 'IN_MAX':
        alarm_reaon = alarm_reaon + '(RX高標)'
    elif alarm_type == 'IN_MIN':
        alarm_reaon = alarm_reaon + '(RX低標)'
    if alarm_type == 'OUT_TOP':
        alarm_reaon = alarm_reaon + '(TX超標)'
    elif alarm_type == 'OUT_MAX':
        alarm_reaon = alarm_reaon + '(TX高標)'
    elif alarm_type == 'OUT_MIN':
        alarm_reaon = alarm_reaon + '(TX低標)'
    elif alarm_type == 'IN_INC':
        alarm_reaon = alarm_reaon + '(RX突升)'
    elif alarm_type == 'IN_DEC':
        alarm_reaon = alarm_reaon + '(TX突降)'
    elif alarm_type == 'OUT_INC':
        alarm_reaon = alarm_reaon + '(TX突升)'
    elif alarm_type == 'OUT_DEC':
        alarm_reaon = alarm_reaon + '(TX突降)'
    elif alarm_type == 'NODATA':
        alarm_reaon = alarm_reaon + '(SNMP)'
    #alarm_msg = alarm_msg + '(測試件,勿理會)'

    oems_id = 0
    try:
        if oems_sid[ne_id + '-' + str(ifindex) + '-' + alarm_type] is not None:
            oems_id = oems_sid[ne_id + '-' + str(ifindex) + '-' + alarm_type]
    except:
        pass

    action_flag = ''
    if alarm_status == 1:
        alarm_msg = '[告警]' + alarm_msg
        if oems_id > 0: # 持續異常
            action_flag = 'LOG'
        else: # 初次異常
            action_flag = 'NEW'
    else:
        alarm_msg = '[解除]' + alarm_msg
        if oems_id > 0: # 恢復正常
            action_flag = 'LOG'
        else: # 一切正常
            pass

    if action_flag == 'NEW':
        if normal_flag == 'I':
            pass
        else:
            sid = 0
            updsql = "begin insert into oems_tickets_main (status,type,subtype,reason,descr,create_date,operator,account,location,normal_flag,impact_list,special_flag) values (%d,%d,%d,'%s','%s',sysdate,%d,'IPMONv2','%s','%s','%s-%s','%s') return to_char(sid) into :1 ; end;" % (status,type,subtype,alarm_reaon,alarm_msg,operator,companyno,normal_flag,ne_id,ifindex,alarm_type)
            print updsql
            try:
                oems_sid_ary = oraoems.db.BindingArray(1,12,'SQLT_STR')
                oraoems.c.execute(updsql, oems_sid_ary)
                sid = int(oems_sid_ary[0])
                #pass
            except:
                print 'Exception: Unable to insert OEMS_TICKETS_MAIN (NEW)'

            if sid > 0:
                updsql = "insert into oems_tickets_log (sid,status_date,orig_status,status,descr,account) values (%d,sysdate,5120,5120,'%s','IPMONv2')" % (sid,alarm_msg)
                print updsql
                try:
                    oraoems.execone(updsql)
                    #pass
                except:
                    print 'Exception: Unable to insert OEMS_TICKETS_LOG (NEW)'
            else:
                print 'Exception: Unable to insert OEMS_TICKETS_LOG (NEW)'
    elif action_flag == 'LOG':
        if normal_flag == 'I':
            pass
        else:
            if oems_id > 0:
                updsql = "insert into oems_tickets_log (sid,status_date,orig_status,status,descr,account) values (%d,sysdate,5120,5120,'%s','IPMONv2')" % (oems_id,alarm_msg)
                print updsql
                try:
                    oraoems.execone(updsql)
                    #pass
                except:
                    print 'Exception: Unable to insert OEMS_TICKETS_LOG (LOG)'
            else:
                print 'Exception: Unable to insert OEMS_TICKETS_LOG (LOG)'

    oraoems.commit()


mysqldb = None
oracnis = None
oraoems = None

while 1:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] START'

    #print 'start: connect oracle'
    oracnis = ORA('nms@cnis')
    if not oracnis.db:
        print 'Error: Unable to connect to server [CNIS]'
        #sys.exit(0)
        break
    #print 'end: connect oracle'

    #print 'start: query oracle'
    server_ip = ''
    qry_sql = "select server_ip from so where companyno='%s' and server_ip is not null" % (so)
    rs1 = oracnis.execall(qry_sql)
    if rs1 is not None and len(rs1) > 0:
        for aw in rs1:
            server_ip = aw[0]
            break
    #print 'end: query oracle'

    if len(server_ip) == 0:
        print 'Error: Unable to get QOS Server IP [CNIS]'
        #sys.exit(0)
        break

    #print 'start: connect mysql'
    try:
        mysqldb = MySQLdb.connect(host="%s" % (server_ip), user="root", passwd="newom123", db="cmdb_%s" % (so))
        mysqlcur = mysqldb.cursor()
    except Exception, msg:
        print 'Error: Unable to connect to server',server_ip,'[MYSQL]'
        #sys.exit(0)
        break
    #print 'end: connect mysql'

    oraoems = ORA('oems@kbro_nmsdb')
    if not oraoems.db:
        print 'Error: Unable to connect to server [OEMS]'
        #sys.exit(0)
        break

    oems_sid = {}
    qry_sql = "select a.sid,a.impact_list,a.special_flag from oems_tickets_main a \
inner join oems_mapping b on b.id=a.operator and b.subtype is not null \
where a.account='IPMONv2' and a.close_date is null and a.normal_flag in ('A','B','I') and a.type in ('3111','4304') and a.status not in ('5029','5125') and a.impact_list like '%%-%%' and a.special_flag is not null and a.location='%s'" % (so)
    print qry_sql
    rs1 = oraoems.execall(qry_sql)
    if rs1 is not None and len(rs1) > 0:
        for aw in rs1:
            oems_sid[aw[1] + '-' + aw[2]] = int(aw[0])
    print 'OEMS_ID:',oems_sid

    ip_ne = []
    qry_sql = "select z.shortname,z.oemsno,a.companyno,b2.type,a.ne_id,a.ifindex,b1.ifdescr,b1.ifspeed*0.05, \
a.k_top_in,a.k_max_in,a.k_min_in,a.k_increase_in,a.k_decrease_in,a.k_top_out,a.k_max_out,a.k_min_out,a.k_increase_out,a.k_decrease_out \
from ipif_kpi a \
inner join ip_ne_if b1 on b1.companyno=a.companyno and b1.ne_id=a.ne_id and b1.ifindex=a.ifindex and b1.stopyn='N' \
inner join ip_ne b2 on b2.companyno=a.companyno and b2.ne_id=a.ne_id and b2.stopyn='N' \
inner join so z on z.companyno=a.companyno \
where a.companyno='%s' and \
(a.k_top_in > 0 or a.k_max_in > 0 or a.k_min_in > 0 or a.k_increase_in > 0 or a.k_decrease_in > 0 or a.k_top_out > 0 or a.k_max_out > 0 or a.k_min_out > 0 or a.k_increase_out > 0 or a.k_decrease_out > 0) \
union \
select z.shortname,z.oemsno,a.companyno,'CMTS',a.ne_id,a.ifindex,c1.ifdescr,c1.ifspeed*0.05, \
a.k_top_in,a.k_max_in,a.k_min_in,a.k_increase_in,a.k_decrease_in,a.k_top_out,a.k_max_out,a.k_min_out,a.k_increase_out,a.k_decrease_out \
from ipif_kpi a \
inner join cmts_if c1 on c1.companyno=a.companyno and c1.cmts_id=a.ne_id and c1.ifindex=a.ifindex and c1.stopyn='N' \
inner join cmts c2 on c2.companyno=a.companyno and c2.cmts_id=a.ne_id and c2.stopyn='N' \
inner join so z on z.companyno=a.companyno \
where a.companyno='%s' and \
(a.k_top_in > 0 or a.k_max_in > 0 or a.k_min_in > 0 or a.k_increase_in > 0 or a.k_decrease_in > 0 or a.k_top_out > 0 or a.k_max_out > 0 or a.k_min_out > 0 or a.k_increase_out > 0 or a.k_decrease_out > 0) \
order by companyno,ne_id,ifindex" % (so,so)
    print qry_sql
    ip_ne = oracnis.execall(qry_sql)
    if ip_ne is not None and len(ip_ne) > 0:
        pass
    else:
        print "Error: IPIF_KPI is empty"
        #sys.exit(0)
        break

    #print ip_ne,len(ip_ne)

    for xx in range(len(ip_ne)):
        soname = ip_ne[xx][0]
        oemsno = ip_ne[xx][1]
        companyno = ip_ne[xx][2]
        ne_type = ip_ne[xx][3]
        ne_id = ip_ne[xx][4]
        ifindex = int(ip_ne[xx][5])
        ifdescr = ip_ne[xx][6]
        ifspeed = int(ip_ne[xx][7])

        k_top_in = ip_ne[xx][8]
        if k_top_in is not None and k_top_in != '':
            k_top_in = int(k_top_in)
        k_max_in = ip_ne[xx][9]
        if k_max_in is not None and k_max_in != '':
            k_max_in = int(k_max_in)
        k_min_in = ip_ne[xx][10]
        if k_min_in is not None and k_min_in != '':
            k_min_in = int(k_min_in)
        k_increase_in = ip_ne[xx][11]
        if k_increase_in is not None and k_increase_in != '':
            k_increase_in = int(k_increase_in)
        k_decrease_in = ip_ne[xx][12]
        if k_decrease_in is not None and k_decrease_in != '':
            k_decrease_in = int(k_decrease_in)
        k_top_out = ip_ne[xx][13]
        if k_top_out is not None and k_top_out != '':
            k_top_out = int(k_top_out)
        k_max_out = ip_ne[xx][14]
        if k_max_out is not None and k_max_out != '':
            k_max_out = int(k_max_out)
        k_min_out = ip_ne[xx][15]
        if k_min_out is not None and k_min_out != '':
            k_min_out = int(k_min_out)
        k_increase_out = ip_ne[xx][16]
        if k_increase_out is not None and k_increase_out != '':
            k_increase_out = int(k_increase_out)
        k_decrease_out = ip_ne[xx][17]
        if k_decrease_out is not None and k_decrease_out != '':
            k_decrease_out = int(k_decrease_out)

        print '＊',soname,companyno,ne_type,ne_id,ifindex,ifdescr,'IN_TOP:',k_top_in,'IN_MAX:',k_max_in,'IN_MIN:',k_min_in,'IN_INC:',k_increase_in,'IN_DEC:',k_decrease_in,'OUT_TOP:',k_top_out,'OUT_MAX:',k_max_out,'OUT_MIN:',k_min_out,'OUT_INC:',k_increase_out,'OUT_DEC:',k_decrease_out

        mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()-(60*30)))
        stime1 = stime2 = stime3 = time1 = time2 = time3 = inoctets1 = inoctets2 = inoctets3 = outoctets1 = outoctets2 = outoctets3 = 0
        inbps1 = outbps1 = inbps2 = outbps2 = 0

        if ne_type == 'CMTS':
            qry_sql = "select cmts_id,ifidx,updatetime,unix_timestamp(updatetime),HCInOctets,HCOutOctets,InOctets,OutOctets from cmtsv2_qos where updatetime >= '%s' and cmts_id='%s' and ifidx=%d group by updatetime order by updatetime desc limit 3" % (mtime, ne_id, ifindex)
        else:
            qry_sql = "select ne_id,ifidx,updatetime,unix_timestamp(updatetime),HCInOctets,HCOutOctets,InOctets,OutOctets from ipif_qos where updatetime >= '%s' and ne_id='%s' and ifidx=%d group by updatetime order by updatetime desc limit 3" % (mtime, ne_id, ifindex)
        print qry_sql
        mysqlcur.execute(qry_sql)
        result = mysqlcur.fetchall()
        if result is not None and len(result) > 0:
            i = 0
            for aw in result:
                stimex = aw[2]

                timex = aw[3]
                if timex is not None and timex != '':
                    timex = int(timex)
                else:
                    timex = 0

                inx = aw[4]
                if inx is not None and inx != '':
                    inx = int(inx)
                else:
                    inx = 0

                outx = aw[5]
                if outx is not None and outx != '':
                    outx = int(outx)
                else:
                    outx = 0

                if i == 0:
                    stime1 = stimex
                    time1 = timex
                    inoctets1 = inx
                    outoctets1 = outx
                elif i == 1:
                    stime2 = stimex
                    time2 = timex
                    inoctets2 = inx
                    outoctets2 = outx
                else:
                    stime3 = stimex
                    time3 = timex
                    inoctets3 = inx
                    outoctets3 = outx

                i = i + 1
        print '近三次數據byte(time,in,out):',stime1,time1,locale.format("%d",inoctets1,1),locale.format("%d",outoctets1,1),':',stime2,time2,locale.format("%d",inoctets2,1),locale.format("%d",outoctets2,1),':',stime3,time3,locale.format("%d",inoctets3,1),locale.format("%d",outoctets3,1)

        if time1 == 0:
            alarm_msg = "%s 設備:%s %s無法取回流量數據" % (soname,ne_id,ifdescr)
            #IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'NODATA',1,alarm_msg)
            continue

        try:
            if oems_sid[ne_id + '-' + str(ifindex) + '-NODATA'] is not None:
                alarm_msg = "%s 設備:%s %s已可取回流量數據" % (soname,ne_id,ifdescr)
                IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'NODATA',0,alarm_msg)
        except:
            pass

        if time1 > 0 and time2 > 0 and inoctets1 > 0 and inoctets2 >= 0 and inoctets1 > inoctets2:
            inbps1 = ((inoctets1-inoctets2)*8)/(time1-time2)
        if time1 > 0 and time2 > 0 and outoctets1 > 0 and outoctets2 >= 0 and outoctets1 > outoctets2:
            outbps1 = ((outoctets1-outoctets2)*8)/(time1-time2)
        if time2 > 0 and time3 > 0 and inoctets2 > 0 and inoctets3 >= 0 and inoctets2 > inoctets3:
            inbps2 = ((inoctets2-inoctets3)*8)/(time2-time3)
        if time2 > 0 and time3 > 0 and outoctets2 > 0 and outoctets3 >= 0 and outoctets2 > outoctets3:
            outbps2 = ((outoctets2-outoctets3)*8)/(time2-time3)
        print '近二次流速bps(in,out):',locale.format("%d",inbps1,1),locale.format("%d",outbps1,1),':',locale.format("%d",inbps2,1),locale.format("%d",outbps2,1)

        if k_top_in > 0:
            status = 0
            if inbps1 >= k_top_in and inbps1 > 0:
                status = 1
            msg = "%s 設備:%s %s, RX超標設定:%sbps, 目前流量:%sbps" % (soname,ne_id,ifdescr,locale.format("%d",k_top_in,1),locale.format("%d",inbps1,1))
            IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'IN_TOP',status,msg)

        if k_max_in > 0:
            status = 0
            if inbps1 >= k_max_in and inbps1 > 0:
                status = 1
            msg = "%s 設備:%s %s, RX高標設定:%sbps, 目前流量:%sbps" % (soname,ne_id,ifdescr,locale.format("%d",k_max_in,1),locale.format("%d",inbps1,1))
            IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'IN_MAX',status,msg)

        if k_min_in > 0:
            status = 0
            if k_min_in >= inbps1 and inbps1 >= 0 and time1 > 0 and time2 > 0:
                status = 1
            msg = "%s 設備:%s %s, RX低標設定:%sbps, 目前流量:%sbps" % (soname,ne_id,ifdescr,locale.format("%d",k_min_in,1),locale.format("%d",inbps1,1))
            IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'IN_MIN',status,msg)

        if k_increase_in > 0 and inbps1 > ifspeed:
            status = 0
            inrate = 0
            if inbps1 > 0 and inbps2 > 0 and inbps1 > inbps2:
                inrate = round(((inbps1-inbps2)/float(inbps2))*100,1)
                if inrate >= k_increase_in:
                    status = 1
            msg = "%s 設備:%s %s, RX突升設定:%d%%, 目前流量:%sbps, 上次流量:%sbps, 突升:%.1f%%" % (soname,ne_id,ifdescr,k_increase_in,locale.format("%d",inbps1,1),locale.format("%d",inbps2,1),inrate)
            IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'IN_INC',status,msg)

        if k_decrease_in > 0 and inbps1 > ifspeed:
            status = 0
            inrate = 0
            if inbps1 > 0 and inbps2 > 0 and inbps2 > inbps1:
                inrate = round(((inbps2-inbps1)/float(inbps2))*100,1)
                if inrate >= k_decrease_in:
                    status = 1
            msg = "%s 設備:%s %s, RX突降設定:%d%%, 目前流量:%sbps, 上次流量:%sbps, 突降:%.1f%%" % (soname,ne_id,ifdescr,k_decrease_in,locale.format("%d",inbps1,1),locale.format("%d",inbps2,1),inrate)
            IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'IN_DEC',status,msg)

        if k_top_out > 0:
            status = 0
            if outbps1 >= k_top_out and outbps1 > 0:
                status = 1
            msg = "%s 設備:%s %s, TX超標設定:%sbps, 目前流量:%sbps" % (soname,ne_id,ifdescr,locale.format("%d",k_top_out,1),locale.format("%d",outbps1,1))
            IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'OUT_TOP',status,msg)

        if k_max_out > 0:
            status = 0
            if outbps1 >= k_max_out and outbps1 > 0:
                status = 1
            msg = "%s 設備:%s %s, TX高標設定:%sbps, 目前流量:%sbps" % (soname,ne_id,ifdescr,locale.format("%d",k_max_out,1),locale.format("%d",outbps1,1))
            IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'OUT_MAX',status,msg)

        if k_min_out > 0:
            status = 0
            if k_min_out >= outbps1 and outbps1 >= 0 and time1 > 0 and time2 > 0:
                status = 1
            msg = "%s 設備:%s %s, TX低標設定:%sbps, 目前流量:%sbps" % (soname,ne_id,ifdescr,locale.format("%d",k_min_out,1),locale.format("%d",outbps1,1))
            IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'OUT_MIN',status,msg)

        if k_increase_out > 0 and outbps1 > ifspeed:
            status = 0
            outrate = 0
            if outbps1 > 0 and outbps2 > 0 and outbps1 > outbps2:
                outrate = round(((outbps1-outbps2)/float(outbps2))*100,1)
                if outrate >= k_increase_out:
                    status = 1
            msg = "%s 設備:%s %s, TX突升設定:%d%%, 目前流量:%sbps, 上次流量:%sbps, 突升:%.1f%%" % (soname,ne_id,ifdescr,k_increase_out,locale.format("%d",outbps1,1),locale.format("%d",outbps2,1),outrate)
            IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'OUT_INC',status,msg)

        if k_decrease_out > 0 and outbps1 > ifspeed:
            status = 0
            outrate = 0
            if outbps1 > 0 and outbps2 > 0 and outbps2 > outbps1:
                outrate = round(((outbps2-outbps1)/float(outbps2))*100,1)
                if outrate >= k_decrease_out:
                    status = 1
            msg = "%s 設備:%s %s, TX突降設定:%d%%, 目前流量:%sbps, 上次流量:%sbps, 突降:%.1f%%" % (soname,ne_id,ifdescr,k_decrease_out,locale.format("%d",outbps1,1),locale.format("%d",outbps2,1),outrate)
            IP_Alarm(oemsno,companyno,ne_type,ne_id,ifindex,'OUT_DEC',status,msg)

    sys.stdout.flush()
    if mysqldb is not None:
        mysqldb.close()
        mysqldb = None
    if oracnis is not None:
        oracnis.se_close()
        oracnis = None
    if oraoems is not None:
        oraoems.se_close()
        oraoems = None
    endtime = time.time()
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print "[%s] END (totalsec: %d)\n" % (nowdate, endtime-startime)
    sys.stdout.flush()

    #break

    while endtime-startime<300:
        time.sleep(5)
        endtime = time.time()
    startime = time.time()

if mysqldb is not None:
    mysqldb.close()
if oracnis is not None:
    oracnis.se_close()
if oraoems is not None:
    oraoems.se_close()
sys.exit(0)
