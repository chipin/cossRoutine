#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import MySQLdb
from oraclass import ORA
from pysnmpclass import snmpclass

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

# Juniper	EX4200
# etherStatsCRCAlignErrors 1.3.6.1.2.1.16.1.1.1.8
# jnxCosQstatTailDropPkts  1.3.6.1.4.1.2636.3.15.4.1.11
#   Queue number:         Mapped forwarding classes
#     0                   best-effort
#     1                   assured-forwarding
#     2                   Return-in (VOD)
#     3                   DCN-in
#     4                   OA-in
#     5                   SO-in
#     6                   DTV-in
#     7                   network-control

def to_oems(p_so,p_neid,p_idx,p_special,p_reason,p_descr,p_act):
    global oraoems, oems

    kk = "%s,%d,%s" % (p_neid,p_idx,p_special)
    oems_id = 0
    try:
        if oems[kk] is not None:
            oems_id = oems[kk]
    except:
        pass

    if p_act == 'D' and oems_id == 0:
       pass
    else:
        print '['+p_act+']',p_descr

        if p_act == 'A':
            p_descr = "[告警]%s" % (p_descr)
        else:
            p_descr = "[解除]%s" % (p_descr)

        if oems_id > 0: # 持續異常
            updsql = "insert into oems_tickets_log (sid,status_date,orig_status,status,descr,account) values (%d,sysdate,5120,5120,'%s','CDNMONv2')" % (oems_id,p_descr)
            print updsql
            try:
                oraoems.execone(updsql)
                oraoems.commit()
                #pass
            except:
                print 'Except: Unable to insert OEMS_TICKETS_LOG (LOG)'
        else: # 初次異常
            updsql = "begin insert into oems_tickets_main (status,type,subtype,reason,descr,create_date,operator,account,location,normal_flag,impact_list,special_flag) values ('5120','3111','311108','%s','%s',sysdate,'13001','CDNMONv2','%s','A','%s,%d','%s') return to_char(sid) into :1 ; end;" % (p_reason,p_descr,p_so,p_neid,p_idx,p_special)
            print updsql
            try:
                oems_sid_ary = oraoems.db.BindingArray(1,12,'SQLT_STR')
                oraoems.c.execute(updsql, oems_sid_ary)
                oraoems.commit()
                oems_id = int(oems_sid_ary[0])
                #pass
            except:
                print 'Except: Unable to insert OEMS_TICKETS_MAIN (NEW)'

            if oems_id > 0:
                updsql = "insert into oems_tickets_log (sid,status_date,orig_status,status,descr,account) values (%d,sysdate,5120,5120,'%s','CDNMONv2')" % (oems_id,p_descr)
                print updsql
                try:
                    oraoems.execone(updsql)
                    oraoems.commit()
                    #pass
                except:
                    print 'Except: Unable to insert OEMS_TICKETS_LOG (NEW)'
            else:
                print 'Except: Unable to insert OEMS_TICKETS_LOG (NEW)'


oracnis = ORA('nms@cnis')
if not oracnis.db:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Error: Unable to connect to server [CNIS]'
    sys.exit(0)

snmp_oid = {}
SQL = "select name,oid from snmp_mib where name in ('etherStatsCRCAlignErrors','jnxCosQstatTailDropPkts')"
rst = oracnis.execall(SQL)
if rst is not None and len(rst)>0:
    for aw in rst:
        try:
            xname = aw[0]
            xoid = aw[1]
            snmp_oid[xname] = xoid
        except Exception, msg:
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print '['+nowdate+'] Except: SNMP_MIB '+str(msg)
if len(snmp_oid) == 0:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Error: SNMP_MIB is empty [CNIS]'
    if oracnis is not None:
        oracnis.se_close()
    sys.exit(0)

cdn = {}
cdn_cnt = 0
SQL = "select e.shortname,a.companyno,a.ne_id,a.ifindex,d.ifdescr,b.ip,b.snmp_ro,c.maker,c.model,b.type,a.alarm_type,a.k_crc_error,a.k_droppkt_dtv,a.k_droppkt_vod \
from ipif_kpi a \
inner join ip_ne b on b.companyno=a.companyno and b.ne_id = a.ne_id and b.stopyn='N' \
inner join sys_object c on c.ne_id=substr(a.ne_id,-8,4) and c.stopyn='N' and upper(c.maker)='JUNIPER' \
inner join ip_ne_if d on d.companyno=a.companyno and d.ne_id=a.ne_id and d.ifindex=a.ifindex and d.stopyn='N' \
inner join so e on e.companyno=a.companyno \
where a.alarm_type = 'CDN 電路' order by a.companyno,a.ne_id,a.ifindex"
print SQL
rst = oracnis.execall(SQL)
if rst is not None and len(rst) > 0:
    for aw in rst:
        try:
            name = aw[0]
            so = aw[1]
            neid = aw[2]
            idx = int(aw[3])
            descr = aw[4]
            ip = aw[5]
            snmp = aw[6]
            crc = aw[11]
            dtv = aw[12]
            vod = aw[13]

            if crc is not None and crc != '':
                crc = int(crc)
            if dtv is not None and dtv != '':
                dtv = int(dtv)
            if vod is not None and vod != '':
                vod = int(vod)

            cdn['NAME-'+str(cdn_cnt)] = name
            cdn['SO-'+str(cdn_cnt)] = so
            cdn['NEID-'+str(cdn_cnt)] = neid
            cdn['IDX-'+str(cdn_cnt)] = idx
            cdn['DESCR-'+str(cdn_cnt)] = descr
            cdn['IP-'+str(cdn_cnt)] = ip
            cdn['SNMP-'+str(cdn_cnt)] = snmp
            cdn['CRC-'+str(cdn_cnt)] = crc
            cdn['DTV-'+str(cdn_cnt)] = dtv
            cdn['VOD-'+str(cdn_cnt)] = vod
            cdn_cnt = cdn_cnt+1

            #if cdn_cnt > 20:
            #    break # 測試用
        except Exception, msg:
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print '['+nowdate+'] Except: CDN '+str(msg)
if len(cdn) == 0:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Error: CDN is empty [CNIS]'
    if oracnis is not None:
        oracnis.se_close()
    sys.exit(0)

oraoems = ORA('oems@kbro_nmsdb')
if not oraoems.db:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Error: Unable to connect to server [OEMS]'
    sys.exit(0)

try:
    mydb = MySQLdb.connect(host="TFM-QOS", user="v2web", passwd="Kbro654Tfm", db="cmdb_500")
    mydbcur = mydb.cursor()
except Exception, msg:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Error: Unable to connect to server [MYSQL]'
    sys.exit(0)

sys.stdout.flush()

duration = 60*5
oracnis_retry = oraoems_retry = mydb_retry = 0
startime = time.time()

while 1:
    try:
        oracnis.execone('select sysdate from dual')
        oracnis_retry = 0
    except Exception, msg:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+'] Error: Lost connection to [CNIS], trying to reconnect. '+str(msg)
        oracnis_retry = oracnis_retry + 1
        oracnis = ORA('nms@cnis')
        if not oracnis.db:
            if oracnis_retry >= 10:
                print '['+nowdate+'] Error: Lost connection to [CNIS], fail to retry [EXIT]'
                break
            else:
                print '['+nowdate+'] Error: Unable to reconnect to server [CNIS]',oracnis_retry
                sys.stdout.flush()
                time.sleep(300)
                continue

    try:
        oraoems.execone('select sysdate from dual')
        oraoems_retry = 0
    except Exception, msg:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+'] Error: Lost connection to [OEMS], trying to reconnect. '+str(msg)
        oraoems_retry = oraoems_retry + 1
        oraoems = ORA('oems@kbro_nmsdb')
        if not oraoems.db:
            if oraoems_retry >= 10:
                print '['+nowdate+'] Error: Lost connection to [OEMS], fail to retry [EXIT]'
                break
            else:
                print '['+nowdate+'] Error: Unable to reconnect to server [oraoems_retry]',oraoems_retry
                sys.stdout.flush()
                time.sleep(300)
                continue

    try:
        mydb.ping()
        mydb_retry = 0
    except Exception, msg:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+'] Error: Lost connection to [MYSQL], trying to reconnect. '+str(msg)
        mydb_retry = mydb_retry + 1
        try:
            mydb = MySQLdb.connect(host="TFM-QOS", user="v2web", passwd="Kbro654Tfm", db="cmdb_500")
            mydbcur = mydb.cursor()
        except Exception, msg:
            if mydb_retry >= 10:
                print '['+nowdate+'] Error: Lost connection to [MYSQL], fail to retry [EXIT]'
                break
            else:
                print '['+nowdate+'] Error: Unable to reconnect to server [MYSQL]',mydb_retry
                sys.stdout.flush()
                time.sleep(300)
                continue

    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] START'

    # 載入目前的告警單號
    oems = {}
    SQL = "select sid,impact_list,special_flag from oems_tickets_main where account='CDNMONv2' and close_date is null and normal_flag in ('A','B') and type in ('3111') and status not in ('5029','5125') and impact_list like '%%,%%' and special_flag is not null"
    print SQL
    rst = oraoems.execall(SQL)
    if rst is not None and len(rst) > 0:
        for aw in rst:
            try:
                oems[aw[1] + ',' + aw[2]] = int(aw[0])
            except Exception, msg:
                nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                print '['+nowdate+'] Except: OEMS_TICKETS_MAIN '+str(msg)
    print 'OEMS:',oems

    sid = (int)((time.time()/300)%57600)
    t_sid = sid - 1
    if t_sid < 0:
        t_sid = 57600 + t_sid

    # 載入上次的數據
    prev_qos = {}
    SQL = "select ne_id,ifidx,crc_error,droppkt_vod,droppkt_dtv from cdn_qos where sid=%d and updatetime >= date_add(now(),interval - 30 minute)" % (t_sid)
    print SQL
    mydbcur.execute(SQL)
    rst = mydbcur.fetchall()
    if rst is not None and len(rst) > 0:
        for aw in rst:
            t_neid = aw[0]
            t_idx = int(aw[1])
            t_crc = aw[2]
            t_vod = aw[3]
            t_dtv = aw[4]

            if t_crc is not None and t_crc != '':
                t_crc = int(t_crc)
            if t_vod is not None and t_vod != '':
                t_vod = int(t_vod)
            if t_dtv is not None and t_dtv != '':
                t_dtv = int(t_dtv)

            prev_qos[t_neid+'-'+str(t_idx)+'-CRC'] = t_crc
            prev_qos[t_neid+'-'+str(t_idx)+'-VOD'] = t_vod
            prev_qos[t_neid+'-'+str(t_idx)+'-DTV'] = t_dtv

    # 撈資料, 寫入, 告警
    i = 0
    while i < cdn_cnt:
        try:
            name = cdn['NAME-'+str(i)]
            so = cdn['SO-'+str(i)]
            neid = cdn['NEID-'+str(i)]
            idx = cdn['IDX-'+str(i)]
            descr = cdn['DESCR-'+str(i)]
            ip = cdn['IP-'+str(i)]
            snmp = cdn['SNMP-'+str(i)]
            print i,so,neid,idx,ip,snmp

            crc_error = droppkt_vod = droppkt_dtv = 'null'
            agt = snmpclass(version='v2c',community=snmp,ptimeout=1,pretries=3,debug=0)

            try:
                mib = "%s.%d" % (snmp_oid['etherStatsCRCAlignErrors'], idx)
                rets = agt.snmpget([ip, '-c', snmp, mib])
                #print rets
                if rets is not None and rets[0][1] is not None and rets[0][1]!='':
                    crc_error = int(rets[0][1])
            except:
                pass

            try:
                mib = "%s.%d.2" % (snmp_oid['jnxCosQstatTailDropPkts'], idx)
                rets = agt.snmpget([ip, '-c', snmp, mib])
                #print rets
                if rets is not None and rets[0][1] is not None and rets[0][1]!='':
                    droppkt_vod = int(rets[0][1])
            except:
                pass

            try:
                mib = "%s.%d.6" % (snmp_oid['jnxCosQstatTailDropPkts'], idx)
                rets = agt.snmpget([ip, '-c', snmp, mib])
                #print rets
                if rets is not None and rets[0][1] is not None and rets[0][1]!='':
                    droppkt_dtv = int(rets[0][1])
            except:
                pass

            nowdate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            SQL = "replace into cdn_qos (sid,ne_id,ifidx,updatetime,crc_error,droppkt_vod,droppkt_dtv) values (%d,'%s',%d,'%s',%s,%s,%s)" % (sid,neid,idx,nowdate,crc_error,droppkt_vod,droppkt_dtv)
            if crc_error != 'null' or droppkt_vod != 'null' or droppkt_dtv != 'null':
                print i,SQL,'=> EXEC'
                try:
                    mydbcur.execute(SQL)
                    mydb.commit()
                    #pass # 測試用
                except Exception, msg:
                    print '['+nowdate+'] Except: '+str(i)+' '+str(msg)
            else:
                print i,SQL,'=> PASS'

            if cdn['CRC-'+str(i)] is not None and cdn['CRC-'+str(i)] != '' and crc_error != 'null':
                if prev_qos[neid+'-'+str(idx)+'-CRC'] is not None and prev_qos[neid+'-'+str(idx)+'-CRC'] != '':
                    prev_crc = prev_qos[neid+'-'+str(idx)+'-CRC']
                    kpi = cdn['CRC-'+str(i)]

                    #if idx == 510:
                    #    crc_error = prev_crc+5

                    print 'CRC_ERROR:',crc_error,'-',prev_crc,'>=',kpi,'?'

                    reason = 'CRC錯誤突升'
                    detail = "%s 設備:%s %s, CRC錯誤突升設定:%d, 目前:%d(%d-%d)" % (name,neid,descr,kpi,crc_error - prev_crc,crc_error,prev_crc)
                    if crc_error - prev_crc >= kpi:
                        act = 'A'
                    else:
                        act = 'D'
                    to_oems(so,neid,idx,'CRC ERROR',reason,detail,act)

            if cdn['VOD-'+str(i)] is not None and cdn['VOD-'+str(i)] != '' and droppkt_vod != 'null':
                if prev_qos[neid+'-'+str(idx)+'-VOD'] is not None and prev_qos[neid+'-'+str(idx)+'-VOD'] != '':
                    prev_vod = prev_qos[neid+'-'+str(idx)+'-VOD']
                    kpi = cdn['VOD-'+str(i)]
                    print 'DROPPKT_VOD:',droppkt_vod,'-',prev_vod,'>=',kpi,'?'

                    reason = '封包丟棄數(VOD)突升'
                    detail = "%s 設備:%s %s, 封包丟棄數(VOD)突升設定:%d, 目前:%d(%d-%d)" % (name,neid,descr,kpi,droppkt_vod - prev_vod,droppkt_vod,prev_vod)
                    if droppkt_vod - prev_vod >= kpi:
                        act = 'A'
                    else:
                        act = 'D'
                    to_oems(so,neid,idx,'DROPPKT VOD',reason,detail,act)

            if cdn['DTV-'+str(i)] is not None and cdn['DTV-'+str(i)] != '' and droppkt_dtv != 'null':
                if prev_qos[neid+'-'+str(idx)+'-DTV'] is not None and prev_qos[neid+'-'+str(idx)+'-DTV'] != '':
                    prev_dtv = prev_qos[neid+'-'+str(idx)+'-DTV']
                    kpi = cdn['DTV-'+str(i)]
                    print 'DROPPKT_DTV:',droppkt_dtv,'-',prev_dtv,'>=',kpi,'?'

                    reason = '封包丟棄數(DTV)突升'
                    detail = "%s 設備:%s %s, 封包丟棄數(DTV)突升設定:%d, 目前:%d(%d-%d)" % (name,neid,descr,kpi,droppkt_dtv - prev_dtv,droppkt_dtv,prev_dtv)
                    if droppkt_dtv - prev_dtv >= kpi:
                        act = 'A'
                    else:
                        act = 'D'
                    to_oems(so,neid,idx,'DROPPKT DTV',reason,detail,act)

        except Exception, msg:
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print '['+nowdate+'] Except: '+str(i)+' '+str(msg)
        sys.stdout.flush()
        i = i+1

    endtime = time.time()
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print "[%s] END (totalsec: %d)\n" % (nowdate, endtime-startime)
    sys.stdout.flush()

    #break # 測試用

    while (endtime-startime) < duration:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print "[%s] WAIT 10 seconds %d %d %d (%d)" % (nowdate, endtime, startime, endtime-startime, duration)
        sys.stdout.flush()
        time.sleep(10)
        endtime = time.time()
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    startime = time.time()
    print "[%s] NEXT" % (nowdate)
    print ""

if oracnis:
    oracnis.se_close()
if oraoems:
    oraoems.se_close()
if mydb:
    mydb.close()
sys.exit(0)
