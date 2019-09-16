#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
import cossdb,pymssql
import urllib2,MultipartPostHandler
from oraclass import ORA
from pysnmpclass import snmpclass

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

##################
# 函式
##################
def v_link_alert_sql(natureStopYN,natureOperator,type,dayHour,alertType,setvalue):
    soArrayTxt = soArrayTxtN = ''
    if  natureStopYN=='N' and natureOperator:
        if  type=='Nature':
            soArrayTxt  = "AND companyno IN(%s)"%(natureOperator)
            soArrayTxtN = "AND companyno NOT IN(%s)"%(natureOperator)
        else:
            soArrayTxt = "AND companyno NOT IN(%s)"%(natureOperator)
    if  dayHour=='days':
        dayHourTxt = "AND createtime >= getdate()-1"
    else:
        dayHourTxt = "AND createtime >= getdate()-(63.0/(24*60))"
    if  alertType=='alertNode':
        field = 'node'
    else:
        field = 'link'
    if  dayHour=='days' and alertType=='alertNode':
        query = '''
            select companyno,%s,sum(score) cnt 
              from v_link_alert 
             where substring(servicename,1,1) <> '8' %s %s
             group by companyno,%s having sum(score) >= %d 
             union select companyno,cast(subsid as varchar),-1 cnt 
                     from v_link_alert 
                    where substring(servicename,1,1) = '8' %s %s
                    group by companyno,subsid
        '''%(field,dayHourTxt,soArrayTxt,field,setvalue,dayHourTxt,soArrayTxtN)
    else:
        query = '''
            select companyno,%s,sum(score) cnt 
              from v_link_alert 
             where substring(servicename,1,1) <> '8' %s %s
             group by companyno,%s having sum(score) >= %d 
        '''%(field,dayHourTxt,soArrayTxt,field,setvalue)
    print query
    return query

def v_link_alert_sql_info(dayHour,companyno,alertType,netid):
    if  dayHour=='days':
        dayHourTxt = "AND createtime >= getdate()-1"
    else:
        dayHourTxt = "AND createtime >= getdate()-(63.0/(24*60))"
    if  alertType=='alertNode':
        field = 'node'
    else:
        field = 'link'
    query = '''
        SELECT servicename,worksheet,city,district,node 
          FROM v_link_alert 
         WHERE substring(servicename,1,1) <> '8' 
           %s
           AND companyno='%s' 
           AND %s='%s'
    '''%(dayHourTxt,companyno,field,netid)
    print query
    return query

# 連接 mssql
def connDB(so,query,type):
    if  so == 'KBRO':
        host='kbroCossMS'
    elif so == 'CG':
        host='CossMS_CG'
    elif so == 'TFM':
        host='TFMCossMS'
    else:
        print "Usage: %s [KBRO|CG|TFM]" % (sys.argv[0])
        sys.exit(0)
    try:
        if so == 'CG':
          con = pymssql.connect(host,user=cossdb.account,password=cossdb.passwd,database='cossdb_cg')
        else:
          con = pymssql.connect(host,user=cossdb.account,password=cossdb.passwd,database='cossdb')
        cur = con.cursor()
    except:
        print "Exception: Unable to connect CossMS [%s]"%(host)
        sys.exit(0)
    cur.execute(query)
    if  type=='all':
        rst = cur.fetchall()
    else:
        rst = cur.fetchmany(100)
    cur.close()        
    return rst

# 主程式 
def main(so,alertType,dayHour,query,linkOffRate=None):
    global node_arr,agent
    curarrays = connDB(so,query,'all')
    if  not curarrays:
        print 'select empty!'
        return False
    # query rst process
    if  dayHour=='days':
        EE='1天'
    else:  
        EE='1小時'
    for curarr in curarrays:
        companyno = curarr[0]
        netid = curarr[1]
        alert_cnt = curarr[2]
        print '--------------------------------------------'
        print companyno,netid,alert_cnt # ex => 420 CC122 3
        worksheet_arr = []
        worksheet_str = ''
        service_count = {}
        if  companyno and netid and alert_cnt>0: # for non LS
            impact_str = "%s-%s" % (companyno, netid)

            # linkid格式錯誤
            if  alertType == 'alertLink':
                ma = re.match(r"^(\w{5}\-\d{6,11})$", netid)
                if  ma is None:
                    print "%s LINKID格式錯誤 => PASS" % (impact_str)
                    continue

            # 已有區障
            if  node_arr.has_key(impact_str)==True:
                print "%s 已有區障 => PASS" % (impact_str)
                continue

            # 需等震江工單結案, 才會自動結案
            node_arr[impact_str] = 9 
            query = v_link_alert_sql_info(dayHour,companyno,alertType,netid)

            # query rst process
            sidarr = connDB(so,query,'all')
            for ssid in sidarr:
                srv = ssid[0]
                wrk = ssid[1]
                district = "%s-%s" % (ssid[2], ssid[3])
                nodeno = ssid[4]
                if  service_count.has_key(srv) == False:
                    service_count[srv] = 0
                service_count[srv] = service_count[srv] + 1
                if  wrk not in worksheet_arr:
                    worksheet_arr.append(wrk)
            impact_str2 = "%s-%s" % (companyno, nodeno)
            if  alertType == 'alertLink':
                if  node_arr.has_key(impact_str2) == True:
                    print "%s => %s 已有區障 => PASS" % (impact_str, impact_str2)
                    continue
            reason_str = "網點# %s %s內已有[%d]戶報修" % (netid, EE, alert_cnt)
            for kk, vv in service_count.items():
                reason_str = "%s, %s共%d件" % (reason_str, kk, vv)

            # 新增障礙單
            sid = 0
            if  alertType == 'alertLink':
                subtype = 310702
                oraqrysql = "select sid from oems_tickets_main where ((type='3107' and subtype in (310701,310702,310703)) or ticket_id is not null) and status<=5104 and (impact_list='%s' or impact_list='%s') and account='COSSv2'" % (impact_str, impact_str2)
            else:
                subtype = 310701
                oraqrysql = "select sid from oems_tickets_main where ((type='3107' and subtype in (310701,310702,310703)) or ticket_id is not null) and status<=5104 and impact_list='%s' and account='COSSv2'" % (impact_str)
            print oraqrysql
            rs = oracon_oems.execall(oraqrysql)
            if rs != None and len(rs) > 0:
                for a_row in rs:
                    sid = a_row[0]
            else:
                descr_str = reason_str
                # 檢查離線率
                if  alertType=='alertLink' and sid==0:
                    try:
                        ma = re.match(r"^(\w{5}\-[1-9]{1,11})", netid)
                        if  ma is not None:
                            mat = ma.group(1)
                            p_subsid_arr = []
                            p_subsid_str = ''

                            query = "select distinct A.companyno,A.subsid,A.servicename,B.nodeno,B.linkid from ms0200 A with (nolock) inner join ms0102 B with (nolock) on A.custid = B.custid and A.companyno=B.companyno where A.companyno='%s' and substring(A.servicename,1,1) in ('2','3','9') and substring(A.custstatus,1,1) not in ('3','4','5') and len(A.singlesn) > 0  and B.addrno = 0 and B.nodeno='%s' and B.linkid like '%s%%'" % (companyno, nodeno, mat)
                            print query
                            qry3arr = connDB(so,query,'all')
                            for qry3row in qry3arr:
                                p_subsid = str(qry3row[1])
                                p_subsid_arr.append(p_subsid)

                            if p_subsid_arr is not None and len(p_subsid_arr) > 0:
                                p_subsid_str = "','".join(p_subsid_arr)

                            if p_subsid_str is not None and len(p_subsid_str) > 0:
                                p_total_cm = p_online_cm = 0
                                oraqrysql = "select subsid,cmmac,ip,idx,cmts_ip,snmp_ro from v_cnis_cmmac_intf where companyno='%s' and subsid in ('%s')" % (companyno, p_subsid_str)
                                print oraqrysql
                                rs = oracon_nms.execall(oraqrysql)
                                if rs != None and len(rs) > 0:
                                    for a_row in rs:
                                        p_subsid = int(a_row[0])
                                        p_cmmac = a_row[1]
                                        p_cmip = a_row[2]
                                        p_cmidx = int(a_row[3])
                                        p_cmtsip = a_row[4]
                                        p_snmpro = a_row[5]
                                        p_cmoid = '.1.3.6.1.2.1.10.127.1.3.3.1.9.' + str(p_cmidx)

                                        rets = agent.snmpget([p_cmtsip, '-c', p_snmpro, p_cmoid])
                                        print p_subsid,p_cmmac,p_cmip,rets
                                        if rets is not None and rets[0][1]!='':
                                            p_online = int(rets[0][1])
                                            if p_online == 6:
                                                p_online_cm = p_online_cm+1
                                        p_total_cm = p_total_cm+1

                                if p_total_cm > 0:
                                    if p_online_cm > 0:
                                        p_online_cm = float(p_online_cm)
                                        p_total_cm = float(p_total_cm)
                                        p_offline = round(100-(p_online_cm*100/p_total_cm),2)

                                        if p_offline >= linkOffRate:
                                            print "離線率 %s%% 已達KPI %s%% => ALARM" % (p_offline, linkOffRate)
                                        else:
                                            print "離線率 %s%% 未達KPI %s%% => PASS" % (p_offline, linkOffRate)
                                            continue
                                    else:
                                        p_offline = 100
                                    descr_str = descr_str + ', 離線率%s%%' % (p_offline)
                    except Exception, e:
                        print 'offline - except: '+str(e)

                taipower_sid = ''
                oraqrysql = "select sid from oems_tickets_main where reason='台電計畫性停電' and normal_flag='P' and sysdate between impact_bg_date and impact_end_date and operator='%d' and descr like '%%%s%%' order by create_date desc" % (so_name[companyno], nodeno)
                print oraqrysql
                rs = oracon_oems.execall(oraqrysql)
                if rs != None and len(rs) > 0:
                    for a_row in rs:
                        taipower_sid = (int)(a_row[0])
                        subtype = 310703
                        break
                oraupdsql = "insert into oems_tickets_main(status,type,subtype,reason,descr,create_date,operator,account,normal_flag,impact_list,location) \
                             values('5100',3107,'%d','%s','%s',sysdate,'%s','COSSv2','B','%s','%s')" % (subtype, reason_str, descr_str, so_name[companyno], impact_str, taipower_sid)
                print oraupdsql
                try:
                    oracon_oems.execone(oraupdsql)
                    oracon_oems.commit()
                    pass
                except:
                    print 'Exception: Unable to insert OEMS_TICKETS_MAIN'

            # 新增影響範圍
            if sid == 0:
                oraqrysql = "select sid from oems_tickets_main where type='3107' and subtype in (310701,310702,310703) and status <= 5104 and impact_list='%s' and account='COSSv2' order by create_date desc" % (impact_str)
                rs = oracon_oems.execall(oraqrysql)
                if rs != None and len(rs) > 0:
                    for a_row in rs:
                        sid = a_row[0]
                        break
                    if  alertType == 'alertLink':
                        netid_type = 'LINK'
                    else:
                        netid_type = 'NODE'
                    oraupdsql = "insert into oems_impact (sid,type,value,companyno,node,area) values ('%d','%s','%s','%s','%s','%s')" % (sid, netid_type, netid, companyno, nodeno, district)
                    print oraupdsql
                    try:
                        oracon_oems.execone(oraupdsql)
                        oracon_oems.commit()
                        pass
                    except:
                        print 'Exception: Unable to insert OEMS_IMPACT'

            # update CTI020 via WorkSheetNo
            if worksheet_arr:
                worksheet_str = "','" . join(worksheet_arr)
            print 'worksheet:',worksheet_arr
            if worksheet_str != None and len(worksheet_str) > 0 and sid != None and sid > 0:
                oraupdsql = "update cti020 set oems_id='%d' where companyno='%d' and coss_id in ('%s') and coss_id is not null and (oems_id is null or oems_id = 0)" % (sid, int(companyno), worksheet_str)
                print oraupdsql
                try:
                    oracon_cti.execone(oraupdsql)
                    oracon_cti.commit()
                    pass
                except:
                    print 'Exception: Unable to update CTI020'

        elif companyno and netid and alert_cnt == -1: #  for 8 LS, 告警是以訂編為單位
            query2="select subsid,custname,worksheet,node,link from v_link_alert where substring(servicename,1,1) = '8' and createtime >= getdate()-1 and companyno='%s' and subsid='%s'" % (companyno, netid)
            sidarr = connDB(so,query2,'all')
            for ssid in sidarr:
                subsid = ssid[0]
                custname = ssid[1]
                nodeno = ssid[3]
                linkid = ssid[4]
                wrk = ssid[2]
                if wrk not in worksheet_arr:
                    worksheet_arr.append(wrk)

            reason_str = "網點# %s 已有專線用戶報修, 訂戶編號: %d, 名稱: %s" % (linkid, subsid, custname)
            impact_str = "%s-%s" % (companyno, subsid)
            #node_arr[impact_str] = 9 # LS障礙不需等震江工單結案, 就可以自動結案

            # 新增障礙單
            sid = 0
            oraqrysql = "select sid from oems_tickets_main where ((type='3110' and subtype in (311001,311003)) or ticket_id is not null) and status<=5104 and impact_list='%s' and account='COSSv2'" % (impact_str)
            print oraqrysql
            rs = oracon_oems.execall(oraqrysql)
            if rs != None and len(rs) > 0:
                for a_row in rs:
                    sid = a_row[0]
            else:
                taipower_sid = ''
                subtype = 311001
                oraqrysql = "select sid from oems_tickets_main where reason='台電計畫性停電' and normal_flag='P' and sysdate between impact_bg_date and impact_end_date and operator='%d' and descr like '%%%s%%' order by create_date desc" % (so_name[companyno], nodeno)
                print oraqrysql
                rs = oracon_oems.execall(oraqrysql)
                if rs != None and len(rs) > 0:
                    for a_row in rs:
                        taipower_sid = (int)(a_row[0])
                        subtype = 311003
                        break
                oraupdsql = "insert into oems_tickets_main(status,type,subtype,reason,descr,create_date,operator,account,normal_flag,impact_list,location) \
                             values('5100',3110,'%d','%s','%s',sysdate,'%s','COSSv2','B','%s','%s')" % (subtype, reason_str, reason_str, so_name[companyno], impact_str, taipower_sid)
                print oraupdsql
                try:
                    oracon_oems.execone(oraupdsql)
                    oracon_oems.commit()
                    pass
                except:
                    print 'Exception: Unable to insert OEMS_TICKETS_MAIN'

            # 新增影響範圍
            if sid == 0:
                oraqrysql = "select sid from oems_tickets_main where type='3110' and subtype in (311001,311003) and status<=5104 and impact_list='%s' and account='COSSv2'" % (impact_str)
                rs = oracon_oems.execall(oraqrysql)
                if rs != None and len(rs) > 0:
                    for a_row in rs:
                        sid = a_row[0]
                    oraupdsql = "insert into oems_impact (sid,type,value,companyno,node,area) values ('%d','SUBSID','%s','%s','%s','%s')" % (sid, subsid, companyno, nodeno, district)
                    print oraupdsql
                    try:
                        oracon_oems.execone(oraupdsql)
                        oracon_oems.commit()
                        pass
                    except:
                        print 'Exception: Unable to insert OEMS_IMPACT'

            # update CTI020 via WorkSheetNo
            if worksheet_arr:
                worksheet_str = "','" . join(worksheet_arr)
            print worksheet_str
            if worksheet_str != None and len(worksheet_str) > 0 and sid != None and sid > 0:
                oraupdsql = "update cti020 set oems_id='%d' where companyno='%d' and coss_id in ('%s') and coss_id is not null and (oems_id is null or oems_id = 0)" % (sid, int(companyno), worksheet_str)
                print oraupdsql
                try:
                    oracon_cti.execone(oraupdsql)
                    oracon_cti.commit()
                    pass
                except:
                    print 'Exception: Unable to update CTI020'

# 程式開始
timeS = time.localtime()

# 選擇 so
if  len(sys.argv) != 2:
    print "Usage: %s [KBRO|CG|TFM]" % (sys.argv[0])
    sys.exit(0)
so = sys.argv[1].upper()
print "######################################################################################################"
print "# [%s] %s start "%(time.strftime("%Y/%m/%d %H:%M:%S",timeS),so)
print "######################################################################################################"

# oracle 連線
oracon_oems = ORA('OEMS@KBRO_NMSDB')
oracon_cti  = ORA('CTI@CNIS')
oracon_nms  = ORA('NMS@CNIS')
if  not oracon_oems.db:
    sys.exit(0)
if  not oracon_cti.db:
    sys.exit(0)
if  not oracon_nms.db:
    sys.exit(0)

# 相關變數-so maping ID => ex => {'210': 13008.0, '300': 13029.0, '230': 13010.0, '610': 13020.0, '310': 13015.0, '701': 13027.0, '330': 13016.0, '260': 13013.0, '410': 13017.0, '240': 13011.0, '420': 13018.0, '810': 13021.0, '103': 13031.0, '250': 13012.0, '101': 13028.0, '106': 13026.0, '820': 13022.0, '104': 13030.0, '220': 13009.0}
oraqrysql = "select name,id from oems_mapping where type='OPERATOR' and name is not null and rank is not null"
rs = oracon_oems.execall(oraqrysql)
so_name = {}
if  rs!=None and len(rs)>0:
    for row in rs:
        so_name[row[0]] = row[1]

# 相關變數-其他
node_arr = {}
agent = snmpclass(version='v1',ptimeout=3,pretries=3,debug=0)

# kpi_coss_bomb 告警值及預設告警值
default_nodeDays = 6
default_nodeHour = 4
default_linkDays = 4
default_linkHour = 2
default_OffRate  = 50
oraqrysql = '''
    SELECT name,node_day,node_hour,link_day,link_hour,offline_rate,operator,stopyn
      FROM kpi_coss_bomb 
     WHERE name IN('Nature','NODE+LINK','NODE')
'''
rs = oracon_oems.execall(oraqrysql)
kpiBomb = {}
if  rs!=None and len(rs) > 0:
    for row in rs:
        name = row[0]
        kpiBomb[name] = {}
        kpiBomb[name]['stopyn'] = row[7]
        if  name=='Nature':
            kpiBomb[name]['operator'] = row[6]      if(row[6]) else ''
            kpiBomb[name]['nodeDays'] = int(row[1]) if(row[1]) else default_nodeDays 
            kpiBomb[name]['nodeHour'] = int(row[2]) if(row[2]) else default_nodeHour 
        elif name=='NODE+LINK':
            kpiBomb[name]['nodeDays'] = int(row[1]) if(row[1]) else default_nodeDays 
            kpiBomb[name]['nodeHour'] = int(row[2]) if(row[2]) else default_nodeHour 
            kpiBomb[name]['linkDays'] = int(row[3]) if(row[3]) else default_linkDays 
            kpiBomb[name]['linkHour'] = int(row[4]) if(row[4]) else default_linkHour 
            kpiBomb[name]['OffRate']  = int(row[5]) if(row[5]) else default_OffRate 
        elif name=='NODE':
            kpiBomb[name]['nodeDays'] = int(row[1]) if(row[1]) else default_nodeDays 
            kpiBomb[name]['nodeHour'] = int(row[2]) if(row[2]) else default_nodeHour 
        elif name=='Offline':
            kpiBomb[name]['operator'] = row[6]      if(row[6]) else ''
print 'Alarm condition:',kpiBomb
'''
Alarm condition:
{
  'Nature'    : {'stopyn': 'N', 'nodeDays': 15, 'nodeHour': 20 ,'operator': '026,101,103,104,106,210,220,230,240,250,260,300,310,330,410,420,500,610,701,810,820'},
  'NODE+LINK' : {'stopyn': 'N', 'nodeDays': 6,  'nodeHour': 4, 'linkDays': 4, 'linkHour': 2, 'OffRate': 50}, 
  'NODE'      : {'stopyn': 'N', 'nodeDays': 5,  'nodeHour': 3}, 
  'Offline'   : {'stopyn': 'N', 'operator': '100,80'},
}
'''

# 迴圈開始
isTime = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
natureStopYN   = kpiBomb['Nature']['stopyn']
natureOperator = kpiBomb['Nature']['operator']
linkOffRate    = None
isHour = time.strftime("%H", time.localtime()) # 24:00~07:59(NODE)、08:00~23:59(NODE+LINK)
isHour = int(isHour)

for(key,val) in kpiBomb.items():
    if  key=='Nature' and val['stopyn']=='N':
        # Nature
        print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
        alertType = 'alertNode'
        # 日
        print "[%s] => Nature-alertNode-Days"%(isTime)
        query = v_link_alert_sql(natureStopYN,natureOperator,key,'days',alertType,val['nodeDays'])
        main(so,alertType,'days',query)
        # 時
        print "[%s] => Nature-alertNode-Hour"%(isTime)
        query = v_link_alert_sql(natureStopYN,natureOperator,key,'hour',alertType,val['nodeHour'])
        main(so,alertType,'hour',query)

    elif key=='NODE+LINK' and val['stopyn']=='N' and isHour>=8:
        # NODE+LINK-node
        print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
        alertType = 'alertNode'
        # 日
        print "[%s] => NODE+LINK-alertNode-Days"%(isTime)
        query = v_link_alert_sql(natureStopYN,natureOperator,key,'days',alertType,val['nodeDays'])
        main(so,alertType,'days',query)
        # 時
        print "[%s] => NODE+LINK-alertNode-Hour"%(isTime)
        query = v_link_alert_sql(natureStopYN,natureOperator,key,'hour',alertType,val['nodeHour'])
        main(so,alertType,'hour',query)
        # NODE+LINK-link
        print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
        alertType = 'alertLink'
        # 日
        print "[%s] => NODE+LINK-alertLink-Days"%(isTime)
        query = v_link_alert_sql(natureStopYN,natureOperator,key,'days',alertType,val['linkDays'])
        main(so,alertType,'days',query)
        # 時
        print "[%s] => NODE+LINK-alertLink-Hour"%(isTime)
        query = v_link_alert_sql(natureStopYN,natureOperator,key,'hour',alertType,val['linkHour'])
        main(so,alertType,'hour',query,val['OffRate'])

    elif key=='NODE' and val['stopyn']=='N' and isHour<8:
        # NODE
        print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
        alertType = 'alertNode'
        # 日
        print "[%s] => NODE-alertNode-Days"%(isTime)
        query = v_link_alert_sql(natureStopYN,natureOperator,key,'days',alertType,val['nodeDays'])
        main(so,alertType,'days',query)
        # 時
        print "[%s] => NODE-alertNode-Hour"%(isTime)
        query = v_link_alert_sql(natureStopYN,natureOperator,key,'hour',alertType,val['nodeHour'])
        main(so,alertType,'hour',query)

print "@@@@@@@@@@@@@@@@@"
print "node_arr=%s"%(node_arr)
print "@@@@@@@@@@@@@@@@@"

# 針對修復完成, 且震江已結單, 更新狀態為結案
if  so == 'KBRO':
    oraqrysql = "select sid,impact_list from oems_tickets_main where account='COSSv2' and status=5104 and operator not in (13026,13028,13031,13030,13029,13027)"
elif so == 'CG':
    oraqrysql = "select sid,impact_list from oems_tickets_main where account='COSSv2' and status=5104 and operator in (13026)"
elif so == 'TFM':
    oraqrysql = "select sid,impact_list from oems_tickets_main where account='COSSv2' and status=5104 and operator in (13028,13031,13030,13029,13027)"
rs = oracon_oems.execall(oraqrysql)
ticket_arr = {}
sid_arr = {}
ii = 0
if  rs!=None and len(rs)>0:
    for a_row in rs:
        sid    = a_row[0]
        implst = a_row[1]
        ticket_arr[ii]  = implst
        sid_arr[implst] = sid
        ii = ii+1
jj = 0
while jj<ii:
    # 若全域變數 node_arr 無陣列值，則 except update db
    try:
        print ticket_arr[jj],node_arr[ticket_arr[jj]]
    except:
        oraupdsql = "update oems_tickets_main set status=5105,close_date = (case when close_date is null then status_date else close_date end) where sid='%d'" % (sid_arr[ticket_arr[jj]])
        print oraupdsql
        oracon_oems.execone(oraupdsql)
        #follow bomb close auto_alert tickets
        oraupdsql = "update oems_tickets_main set status='5123',close_date=sysdate where ticket_id='%d' and account='COSSv2'" % (sid_arr[ticket_arr[jj]])
        print oraupdsql
        oracon_oems.execone(oraupdsql)
        oracon_oems.commit()
        #結案發送簡訊
        url = 'https://v2.kbro.com.tw/portal/oems/bomb/bomb_close_sendsms.php'
        post_data = {}
        post_data['sid'] = sid_arr[ticket_arr[jj]]
        opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
        jsonstr = opener.open(url, post_data).read()
        
    jj = jj+1

# 關閉oracle
if  oracon_oems.db:
    oracon_oems.se_close()
if  oracon_cti.db:
    oracon_cti.se_close()
if  oracon_nms.db:
    oracon_nms.se_close()
tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] %s END\n" % (tme, so)
