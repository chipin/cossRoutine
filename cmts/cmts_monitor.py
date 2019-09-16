#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import string
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

# 函式 2018-09-13byDavis：新增ncc api告警機制
def get_tickets_main_createDate(sid):
    ora = ORA('oems@kbro_nmsdb')
    sql = "SELECT TO_CHAR(CREATE_DATE,'YYYYMMDD') FROM oems_tickets_main WHERE sid='%s'"%(sid)
    rst = ora.execall(sql)
    if  rst!=None and len(rst)>0:
        rst = rst[0][0]
    ora.se_close()
    return rst

def nccApiLog(file,msg):
    fp     = open('/ap/home/coss/log/nccApi/'+file,'a')
    isTime = time.strftime("%Y/%m/%d %H:%M:%S",time.localtime())
    msg    = "[%s]:%s\n"%(isTime,msg)
    fp.write(msg)
    fp.close()

def triggerNccApi(nccSid,nccStatus,so2NccCode,nccSiteid,nccObjectid,nccDesc):
    sid        = str(nccSid)
    createDate = time.strftime("FE%Y%m%d",time.localtime())
    if  nccStatus=='Update':
        rst = get_tickets_main_createDate(sid)
        if  len(rst)>0:
            createDate = 'FE' + rst
    alarmid     = 'AC' + so2NccCode + createDate + sid[-5:]
    source      = 'catv_dev'
    eventtime   = time.strftime("%Y/%m/%d %H:%M:%S",time.localtime())
    networktype = 'AC'
    status      = nccStatus   # 事件狀態 New,Update,,Ceased
    operator    = so2NccCode  # 業者編號
    siteid      = nccSiteid   # 機房名稱
    objectid    = nccObjectid # 設施編號
    severity    = 'Critical'  # 障礙等級 Minor,Major,Critical,Emergency
    identify    = sid         # 識別碼
    alarm       = nccDesc     # 障礙說明
    nccApiJson  = '{"source":"%s","event":{"EventTime":"%s","AlarmID":"%s","NetworkType":"%s","Status":"%s","Operator":"%s","SiteID":"%s","ObjectID":"%s","Severity":"%s","Identify":"%s","Alarm":"%s"}}'%(source,eventtime,alarmid,networktype,status,operator,siteid,objectid,severity,identify,alarm)
    nccApiLog('cmts_monitor_nccApi.log','[ncc api告警機制][開始送出]'+nccApiJson)
    # 執行用 read 可得到執行結果
    rst = os.popen('curl -s -k --tlsv1.2 -H "Authorization: Splunk 47491100-5C99-4228-85FA-C009FB8AC803" https://211.22.193.184:8088/services/collector/event -d  \'' + nccApiJson + '\'').read()
    nccApiLog('cmts_monitor_nccApi.log',rst)


def get_nccSiteid_Desc():
    siteid_Desc = {}
    ora = ORA('nms@cnis')
    sql = "SELECT s_id,s_name FROM site_engine WHERE stopyn='N' AND s_id NOT IN('%-%')"
    rst = ora.execall(sql)
    if  rst!=None and len(rst)>0:
        for getRow in rst:
            siteid = getRow[0]
            siteid_Desc[siteid] = getRow[1]
    ora.se_close()
    return siteid_Desc

# 2018-09-13byDavis：新增ncc api告警機制，so 與 NccCode mapping 少 106 和 820
so2NccCode = {'026':'020','240':'021','210':'022','810':'023','410':'024','330':'025','250':'026','310':'027','420':'028','230':'029','220':'030','260':'031','610':'032','820':'033','106':'034','500':'040','104':'041','701':'042','300':'043','101':'044','103':'045'}
nccSiteid_Desc = get_nccSiteid_Desc()


so_mapping = {}
'''
def SMS_alert(s):
    print 'Sending short message:'+s
    sys.stdout.flush()
    smsg = string.replace(s[:100],"'", "*")
    smsg = string.replace(smsg,'"', "*")
    oraconnect = ORA('COSS@KBRO_NMSDB')
    if not oraconnect.db:
        return -1
    sql = "insert into oss_sms(sys,sender,target,msg) values('NOC','IPMON','0935449386','%s')" % (smsg)
    try:
        oraconnect.execone(sql)
        oraconnect.commit()
        oraconnect.se_close()
    except Exception, e:
        print '- SMS_alert() ERROR:',
        print str(e)
        pass
'''

def SMS_IP_alert(so, ne, ext, status):
    global so_mapping
    if status==1:
        smsg = "[告警發生]-%s CMTS設備:%s,CM上線數因降低%s%%異常!" % (so_mapping[so], ne, ext)
    else:
        smsg = "[解除]-%s CMTS設備:%s,CM上線數已恢復正常!" % (so_mapping[so], ne)
    if 1:
        oraconnect = ORA('COSS@KBRO_NMSDB')
        if not oraconnect.db:
            return -1
        SMSSQL = "select mobile from v_sms_grp where gid='142' and (so='%s' or so is null)" % (so)
        sms_arr = oraconnect.execall(SMSSQL)
        for sms in sms_arr:
            sql = "insert into oss_sms(sys,sender,target,msg) values('NOC','CMTSMON','%s','%s')" % (sms[0], smsg)
            oraconnect.execone(sql)
        oraconnect.commit()
        if status==1 or status==0:
            ora_oems = ORA('OEMS@KBRO_NMSDB')
            if not ora_oems.db:
                return -1
            so_name = {}
            oraqrysql = "select name,id from oems_mapping where type='OPERATOR' and name is not null"
            rs = ora_oems.execall(oraqrysql)
            if rs != None and len(rs) > 0:
                for a_row in rs:
                    if a_row[0]=='220':
                        so_name['026'] = int(a_row[1])
                    so_name[a_row[0]] = int(a_row[1])
            ostatus = 5120
            oraqrysql = "select sid,status from oems_tickets_main where ((type in (3111) and subtype in (311106)) or ticket_id is not null) and status in (5120,5121) and impact_list='%s'" % (ne)
            sid = -1
            rs = ora_oems.execall(oraqrysql)
            if rs is not None and len(rs) > 0:
                for a_row in rs:
                    sid = int(a_row[0])
                    ostatus = a_row[1]
            print sid
            if sid<0:
                oraupdsql = "begin insert into oems_tickets_main(status,type,subtype,reason,descr,create_date,operator,account,normal_flag,impact_list) values('5120',3111,311106,'CMTS CM上線數異常','%s',sysdate,'%s','CMTSMON','A','%s') return to_char(sid) into :1 ; end;" % (smsg, so_name[so], ne)
                oems_sid_ary = ora_oems.db.BindingArray(1,12,'SQLT_STR')
                ora_oems.c.execute(oraupdsql, oems_sid_ary)
                sid = int(oems_sid_ary[0])
            oraupdsql = "insert into oems_tickets_log(sid,status_date,orig_status,status,descr,account) values(%d,sysdate,%d,%d,'%s','CMTSMON')" % (sid,ostatus,ostatus,smsg)
            print oraupdsql
            ora_oems.execone(oraupdsql)
            ora_oems.commit()
            ora_oems.se_close()
        tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print "[%s]: %s" % (tme, smsg)
        oraconnect.se_close()

def SMS_CPU_alert(so, ne, ext, status):
    global so_mapping
    if status==1:
        smsg = "[告警發生]-%s CMTS設備:%s,CPU使用率為%s%%異常!" % (so_mapping[so], ne, ext)
    else:
        smsg = "[解除]-%s CMTS設備:%s,CPU使用率已恢復正常!" % (so_mapping[so], ne)
    if 1:
        oraconnect = ORA('COSS@KBRO_NMSDB')
        if not oraconnect.db:
            return -1
        SMSSQL = "select mobile from v_sms_grp where gid='142' and (so='%s' or so is null)" % (so)
        sms_arr = oraconnect.execall(SMSSQL)
        for sms in sms_arr:
            sql = "insert into oss_sms(sys,sender,target,msg) values('NOC','CMTSMON','%s','%s')" % (sms[0], smsg)
            oraconnect.execone(sql)
        oraconnect.commit()
        if status==1 or status==0:
            ora_oems = ORA('OEMS@KBRO_NMSDB')
            if not ora_oems.db:
                return -1
            so_name = {}
            oraqrysql = "select name,id from oems_mapping where type='OPERATOR' and name is not null"
            rs = ora_oems.execall(oraqrysql)
            if rs != None and len(rs) > 0:
                for a_row in rs:
                    if a_row[0]=='220':
                        so_name['026'] = a_row[1]
                    so_name[a_row[0]] = a_row[1]
            ostatus = 5120
            oraqrysql = "select sid,status from oems_tickets_main where ((type in (3111) and subtype in (311106)) or ticket_id is not null) and status in (5120,5121) and impact_list='%s-CPU'" % (ne)
            sid = -1
            rs = ora_oems.execall(oraqrysql)
            if rs is not None and len(rs) > 0:
                for a_row in rs:
                    sid = int(a_row[0])
                    ostatus = a_row[1]
            print sid
            if sid<0:
                oraupdsql = "begin insert into oems_tickets_main(status,type,subtype,reason,descr,create_date,operator,account,normal_flag,impact_list) values('5120',3111,311106,'CMTS CPU使用率異常','%s',sysdate,'%s','CMTSMON','A','%s-CPU') return to_char(sid) into :1 ; end;" % (smsg, so_name[so], ne)
                oems_sid_ary = ora_oems.db.BindingArray(1,12,'SQLT_STR')
                ora_oems.c.execute(oraupdsql, oems_sid_ary)
                sid = int(oems_sid_ary[0])
            oraupdsql = "insert into oems_tickets_log(sid,status_date,orig_status,status,descr,account) values(%d,sysdate,%d,%d,'%s','CMTSMON')" % (sid,ostatus,ostatus,smsg)
            print oraupdsql
            ora_oems.execone(oraupdsql)
            ora_oems.commit()
            ora_oems.se_close()
        tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print "[%s]: %s" % (tme, smsg)
        oraconnect.se_close()

def SMS_TEMP_alert(so, ne, ext, status):
    global so_mapping
    if status==1:
        smsg = "[告警發生]-%s CMTS設備:%s,溫度為%s異常!" % (so_mapping[so], ne, ext)
    else:
        smsg = "[解除]-%s CMTS設備:%s,溫度已恢復正常!" % (so_mapping[so], ne)
    if 1:
        oraconnect = ORA('COSS@KBRO_NMSDB')
        if not oraconnect.db:
            return -1
        SMSSQL = "select mobile from v_sms_grp where gid='142' and (so='%s' or so is null)" % (so)
        sms_arr = oraconnect.execall(SMSSQL)
        for sms in sms_arr:
            sql = "insert into oss_sms(sys,sender,target,msg) values('NOC','CMTSMON','%s','%s')" % (sms[0], smsg)
            oraconnect.execone(sql)
        oraconnect.commit()
        if status==1 or status==0:
            ora_oems = ORA('OEMS@KBRO_NMSDB')
            if not ora_oems.db:
                return -1
            so_name = {}
            oraqrysql = "select name,id from oems_mapping where type='OPERATOR' and name is not null"
            rs = ora_oems.execall(oraqrysql)
            if rs != None and len(rs) > 0:
                for a_row in rs:
                    if a_row[0]=='220':
                        so_name['026'] = a_row[1]
                    so_name[a_row[0]] = a_row[1]
            ostatus = 5120
            oraqrysql = "select sid,status from oems_tickets_main where ((type in (3111) and subtype in (311106)) or ticket_id is not null) and status in (5120,5121) and impact_list='%s-TEMP'" % (ne)
            sid = -1
            rs = ora_oems.execall(oraqrysql)
            if rs is not None and len(rs) > 0:
                for a_row in rs:
                    sid = int(a_row[0])
                    ostatus = a_row[1]
            print sid
            if sid<0:
                oraupdsql = "begin insert into oems_tickets_main(status,type,subtype,reason,descr,create_date,operator,account,normal_flag,impact_list) values('5120',3111,311106,'CMTS 溫度異常','%s',sysdate,'%s','CMTSMON','A','%s-TEMP') return to_char(sid) into :1 ; end;" % (smsg, so_name[so], ne)
                oems_sid_ary = ora_oems.db.BindingArray(1,12,'SQLT_STR')
                ora_oems.c.execute(oraupdsql, oems_sid_ary)
                sid = int(oems_sid_ary[0])
            oraupdsql = "insert into oems_tickets_log(sid,status_date,orig_status,status,descr,account) values(%d,sysdate,%d,%d,'%s','CMTSMON')" % (sid,ostatus,ostatus,smsg)
            print oraupdsql
            ora_oems.execone(oraupdsql)
            ora_oems.commit()
            ora_oems.se_close()
        tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print "[%s]: %s" % (tme, smsg)
        oraconnect.se_close()

def SMS_NODE_alert(so, ne, node, remark, pid, status):
    global so_mapping
    if status==1:
        smsg = "[告警發生]-%s CMTS設備:%s,Node: %s離線率過高異常!" % (so_mapping[so], ne, node)
    else:
        smsg = "[解除]-%s CMTS設備:%s,Node: %s離線率已恢復正常!" % (so_mapping[so], ne, node)
    if 1:
        if status==1 or status==0:
            ora_oems = ORA('OEMS@KBRO_NMSDB')
            if not ora_oems.db:
                return -1
            so_name = {}
            oraqrysql = "select name,id from oems_mapping where type='OPERATOR' and name is not null"
            rs = ora_oems.execall(oraqrysql)
            if rs != None and len(rs) > 0:
                for a_row in rs:
                    if a_row[0]=='220':
                        so_name['026'] = a_row[1]
                    so_name[a_row[0]] = a_row[1]
            ostatus = 5120
            sid = -1
            if pid<=0:
                oraqrysql = "select sid,status from oems_tickets_main where ((type in (3111) and subtype in (311106)) or ticket_id is not null) and status in (5120,5121) and impact_list='%s-%s'" % (ne, node)
            else:
                oraqrysql = "select sid,status from oems_tickets_main where sid=%d" % (pid)
                rs = ora_oems.execall(oraqrysql)
                if rs is not None and len(rs) > 0:
                    for a_row in rs:
                        sid = int(a_row[0])
                        ostatus = a_row[1]
                if ostatus==5123:
                    oraqrysql = "select sid,status from oems_tickets_main where ((type in (3111) and subtype in (311106)) or ticket_id is not null) and status in (5120,5121) and impact_list='%s-%s'" % (ne, node)
                else:
                    oraqrysql = ''
            if oraqrysql!='':
                rs = ora_oems.execall(oraqrysql)
                if rs is not None and len(rs) > 0:
                    for a_row in rs:
                        sid = int(a_row[0])
                        ostatus = a_row[1]
            print sid
            nccStatus = 'Update'
            if sid<=0:
                SQL = "select sid,status from v_oems_impact_node where status=5013 and node='%s'" % (node)
                rs = ora_oems.execall(SQL)
                if rs is not None and len(rs) > 0:
                    for a_row in rs:
                        sid = int(a_row[0])
                        ostatus = a_row[1]
                if sid<=0:
                    nccStatus = 'New'
                    oraupdsql = "begin insert into oems_tickets_main(status,type,subtype,reason,descr,create_date,operator,account,normal_flag,impact_list) values('5120',3111,311106,'NODE 離線率異常','%s %s',sysdate,'%s','CMTSMON','A','%s-%s') return to_char(sid) into :1 ; end;" % (smsg, remark, so_name[so], ne, node)
                    oems_sid_ary = ora_oems.db.BindingArray(1,12,'SQLT_STR')
                    ora_oems.c.execute(oraupdsql, oems_sid_ary)
                    sid = int(oems_sid_ary[0])
                    # Sending SMS
                    oraconnect = ORA('COSS@KBRO_NMSDB')
                    if not oraconnect.db:
                        return -1
                    SMSSQL = "select mobile from v_sms_grp where gid='162' and (so='%s' or so is null)" % (so)
                    sms_arr = oraconnect.execall(SMSSQL)
                    for sms in sms_arr:
                        sql = "insert into oss_sms(sys,sender,target,msg) values('NOC','CMTSMON','%s','%s')" % (sms[0], smsg)
                        oraconnect.execone(sql)
                    oraconnect.commit()
                    oraconnect.se_close()
            oraupdsql = "insert into oems_tickets_log(sid,status_date,orig_status,status,descr,account) values(%d,sysdate,%d,%d,'%s. %s','CMTSMON')" % (sid,ostatus,ostatus,smsg, remark)
            print oraupdsql
            ora_oems.execone(oraupdsql)
            ora_oems.commit()
            ora_oems.se_close()

            # 2019-01-10-byDavis：因需求者認為Node離線率的告警太多，不需要丟到NCC，請協助停用
            '''
            # 2018-09-13byDavis：新增ncc api告警機制
            if  status==1:
                print '[ncc api告警機制][status=%d][sid=%d,nccStatus=%s,so=%s,neid=%s,alarm_msg=%s]'%(status,sid,nccStatus,so,ne,smsg)
                nccApiMsg ='[status=%d]'%(status)
                nccApiMsg+='[sid=%d,nccStatus=%s,so=%s,neid=%s,alarm_msg=%s]'%(sid,nccStatus,so,ne,smsg)
                try:
                    global so2NccCode,nccSiteid_Desc
                    # 取得業者編號
                    nccCode = so2NccCode[so]
                    # 取得機房名稱 ex ne=YMS_CBR8_001 -> YMS -> 陽明山頭端
                    nccSiteid = ne.split('_')[0]
                    try:
                        nccSiteid = nccSiteid_Desc[nccSiteid]
                    except:
                        nccSiteid = '--' + nccSiteid
                    triggerNccApi(sid,nccStatus,nccCode,nccSiteid,ne,smsg)
                    nccApiMsg+='[nccSiteid=%s]'%(nccSiteid)
                except Exception,e:
                    nccApiMsg+='[exception=%s]'%(str(e))
                nccApiLog('cmts_monitor_nccApi.log',nccApiMsg)
            '''
        
        tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print "[%s]: %s" % (tme, smsg)
        return sid


nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print '['+nowdate+'] START'

oracon = ORA('nms@cnis')
if not oracon.db:
    print 'Error: Unable to connect to server [CNIS]'
    sys.exit(0)

SQL = "select companyno,shortname from so order by companyno"
rst = oracon.execall(SQL)
if rst is not None and len(rst) > 0:
    for aw in rst:
        so = aw[0]
        soname = aw[1]
        so_mapping[so] = soname
        print so, soname
else:
    print "Error: SO is empty"
    if oracon is not None:
        oracon.se_close()
    sys.exit(0)


SQL = "SELECT companyno,cmts_id,ip,cmactive,diff_cmactive,sms,cmtotal FROM V_CNIS_CMTS_CNT_MONITOR order by companyno"
rst = oracon.execall(SQL)
if rst is not None and len(rst) > 0:
    for aw in rst:
        try:
            so      = aw[0]
            cmts_id = aw[1]
            ip      = aw[2]
            online  = int(aw[3]) if(aw[3] is not None) else 0
            dx      = int(aw[4]) if(aw[4] is not None) else 0
            sms     = aw[5]
            total   = aw[6]
            if sms is None or sms=='':
                sms = 'N'
            if online>0:
                remark = "%d" % ((float(dx)/online)*100.0)
                #print remark
            else:
                remark = "0"
        except Exception, e:
            print 'Error:',e
            continue

        print so, cmts_id, ip, online, dx, sms, remark

        updflag = 0
        if (float(dx)>=(float(online)*0.15)) and sms=='N' and total>0:
            SMS_IP_alert(so, cmts_id, remark, 1)
            updflag = 1
        elif ((float(dx)<(float(online)*0.15)) or total==0) and sms=='Y':
            SMS_IP_alert(so, cmts_id, remark, 0)
            updflag = 2
        updSQL = 'X'
        if updflag==1:
            updSQL = "update cmts set sms='Y',errortime=sysdate where companyno='%s' and cmts_id='%s'" % (so, cmts_id)
        elif updflag==2:
            updSQL = "update cmts set sms='N',ceasetime=sysdate where companyno='%s' and cmts_id='%s'" % (so, cmts_id)
        if updflag and updSQL!='X':
            try:
                oracon.execone(updSQL)
                oracon.commit()
            except Exception, detail:
                print 'Error: %s -> %s' % (updSQL, detail)

        sys.stdout.flush()
    print 'Check V_CNIS_CMTS_CNT_MONITOR done'
else:
    print 'Error: V_CNIS_CMTS_CNT_MONITOR is empty'


SQL = "SELECT companyno,cmts_id,ip,cpu,prev_cpu,sms_cpu,case when type='UBR' then 70 else 80 end load,tpt,prev_tpt,sms_tpt,case when type='UBR' then 55 else 60 end errtmp FROM CMTS order by companyno"
rst = oracon.execall(SQL)
if rst is not None and len(rst) > 0:
    for aw in rst:
        try:
            so       = aw[0]
            cmts_id  = aw[1]
            ip       = aw[2]
            cpu      = int(aw[3]) if(aw[3] is not None) else 0
            prev_cpu = int(aw[4]) if(aw[4] is not None) else 0
            sms      = aw[5]
            ths      = int(aw[6]) if(aw[6] is not None) else 0
            try:
                tpt      = int(aw[7]) if(aw[7] is not None) else 0
                prev_tpt = int(aw[8]) if(aw[8] is not None) else 0
                sms_tpt  = aw[9]
                ths_tpt  = int(aw[10]) if(aw[10] is not None) else 0
            except:
                tpt      = -1
                prev_tpt = -1
                ths_tpt  = 60
                sms_tpt  = 'N'
            if sms is None or sms=='':
                sms = 'N'
            if sms_tpt is None or sms_tpt=='':
                sms_tpt = 'N'
            remark = "%d / %d" % (cpu, ths)
            remark_tpt = "%d / %d" % (tpt, ths_tpt)
        except Exception, e:
            print 'Error:',e
            continue

        print so, cmts_id, ip, cpu, prev_cpu, sms, ths,' - ',tpt,prev_tpt,sms_tpt,ths_tpt

        updflag = 0
        if cpu>=ths and prev_cpu>=ths and sms=='N':
            SMS_CPU_alert(so, cmts_id, remark, 1)
            updflag = 1
        elif cpu<ths and prev_cpu<ths and sms=='Y':
            SMS_CPU_alert(so, cmts_id, remark, 0)
            updflag = 2
        updSQL = 'X'
        if updflag==1:
            updSQL = "update cmts set sms_cpu='Y',errortime_cpu=sysdate where companyno='%s' and cmts_id='%s'" % (so, cmts_id)
        elif updflag==2:
            updSQL = "update cmts set sms_cpu='N',ceasetime_cpu=sysdate where companyno='%s' and cmts_id='%s'" % (so, cmts_id)
        if updflag and updSQL!='X':
            try:
                oracon.execone(updSQL)
                oracon.commit()
            except Exception, detail:
                print 'Error: %s -> %s' % (updSQL, detail)

        updflag = 0
        if tpt>=ths_tpt and prev_tpt>=ths_tpt and sms_tpt=='N':
            SMS_TEMP_alert(so, cmts_id, remark_tpt, 1)
            updflag = 1
        elif tpt<ths_tpt and prev_tpt<ths_tpt and sms_tpt=='Y':
            SMS_TEMP_alert(so, cmts_id, remark_tpt, 0)
            updflag = 2
        updSQL = 'X'
        if updflag==1:
            updSQL = "update cmts set sms_tpt='Y',errortime_tpt=sysdate where companyno='%s' and cmts_id='%s'" % (so, cmts_id)
        elif updflag==2:
            updSQL = "update cmts set sms_tpt='N',ceasetime_tpt=sysdate where companyno='%s' and cmts_id='%s'" % (so, cmts_id)
        if updflag and updSQL!='X':
            try:
                oracon.execone(updSQL)
                oracon.commit()
            except Exception, detail:
                print 'Error: %s -> %s' % (updSQL, detail)

        sys.stdout.flush()
    print 'Check CMTS done'
else:
    print 'Error: CMTS is empty'


SQL = "SELECT companyno,cmts_id,ifindex,node,sms,offline_cnt,prev_offline_cnt,error_offline,oems_id from V_CNIS_NODE_CMTSIF_ONLINE order by companyno"
rst = oracon.execall(SQL)
if rst is not None and len(rst) > 0:
    for aw in rst:
        try:
            so = aw[0]
            cmts_id          = aw[1]
            ifidx            = aw[2]
            node_id          = aw[3]
            sms              = aw[4]
            offline_cnt      = int(aw[5]) if(aw[5] is not None) else 0
            prev_offline_cnt = int(aw[6]) if(aw[6] is not None) else 0
            error_offline    = aw[7]
            oems_id          = aw[8]
            if sms is None or sms=='':
                sms = 'N'
            if error_offline is None:
                error_offline = -1
            if oems_id is None:
                oems_id = 0
            remark1 = "CM離線數(%d->%d)" % (prev_offline_cnt, offline_cnt)
            remark2 = "CM離線數(%d->%d,%d)" % (prev_offline_cnt, offline_cnt, error_offline)
        except Exception, e:
            print 'Error6',e
            continue

        print '--',so, cmts_id, node_id, sms

        updflag = 0
        if offline_cnt-prev_offline_cnt>=10 and sms=='N':
            oems_id = SMS_NODE_alert(so, cmts_id, node_id, remark1, oems_id, 1)
            updflag = 1
        elif (offline_cnt-error_offline<5 or error_offline<0) and sms=='Y':
            oems_id = SMS_NODE_alert(so, cmts_id, node_id, remark2, oems_id, 0)
            updflag = 2
        updSQL = 'X'
        if updflag==1:
            updSQL = "update cmts_if set sms='Y',oems_id=%d,error_offline=%d,errortime=sysdate where companyno='%s' and cmts_id='%s' and ifindex=%d" % (oems_id, prev_offline_cnt, so, cmts_id, ifidx)
        elif updflag==2:
            updSQL = "update cmts_if set sms='N',error_offline=to_number(null),ceasetime=sysdate where companyno='%s' and cmts_id='%s' and ifindex=%d" % (so, cmts_id, ifidx)
        if updflag and updSQL!='X':
            try:
                oracon.execone(updSQL)
                oracon.commit()
            except Exception, detail:
                print 'Error: %s -> %s' % (updSQL, detail)

        sys.stdout.flush()
    print 'Check V_CNIS_NODE_CMTSIF_ONLINE done'
else:
    print 'Error: V_CNIS_NODE_CMTSIF_ONLINE is empty'


if oracon is not None:
    oracon.se_close()

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print '['+nowdate+'] END'
