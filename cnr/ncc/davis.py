#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# CMMAC: xxxSTB   CPEMAC: xxxSTBdefault
# CMMAC: xxxTV10M CPEMAC: xxxTVSTB
# CMMAC: xxxCPzz  CPEMAC: xxxMTA-yy
import os,sys,time,string,re,requests

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

##################
# 參數
##################
dateTime = time.strftime("%Y/%m/%d %H:%M:%S",time.localtime())
alarmID  = time.strftime("%Y%m%dx%H%M",time.localtime())
print '[程式開始：%s]'%(dateTime)
'''
##################
# 方法1：use PyHEC
##################
payload  = '{"source":"HEC_TEST","event":{"EventTime":"%s","AlarmID":"AC020FE%s","NetworkType":"AC","Status":"New","Operator":"020","SiteID":"Neihu","ObjectID":"CMTS-01","Severity":"Critical","Identify":"T2-FP1-LTU-N01;COM/LTU;13;16;CL#01#016#1","Alarm":"small restart(%s測試)"}}'%(dateTime,alarmID,'PyHEC')
headers = {'Authorization': 'Splunk 47491100-5C99-4228-85FA-C009FB8AC803'}
r = requests.post('https://211.22.193.184:8088/services/collector/event',data=payload, headers=headers, verify=False)
# print r.status_code
print '[PyHEC->',r.text
'''

##################
# 方法2：use linux command
##################
'''
命令列加上 -s 即不顯示下列訊息
%   Total   %   Received   %   Xferd   AverageDload   SpeedUpload   TimeTotal   TimeSpent   TimeLeft   CurrentSpeed
0      27   0         27   0     296            207          2272    --:--:--    --:--:--   --:--:--              0
'''
#payload = '{"source":"catv_dev","event":{"EventTime":"2018/09/17 17:08:03","AlarmID":"AC020FE2018091709171","NetworkType":"AC","Status":"New","Operator":"020","SiteID":"辛亥頭端機房","ObjectID":"WS_CBR8_001","Severity":"Critical","Identify":"3009171","Alarm":"[告警發生]-大安文 CMTS設備:WS_CBR8_001,Node: LW73A離線率過高異常!"}}'
#payload = '{"source":"catv_dev","event":{"EventTime":"2018/09/17 17:08:03","AlarmID":"AC020FE2018091709171","NetworkType":"AC","Status":"New","Operator":"021","SiteID":"光復機房","ObjectID":"CMTS-01","Severity":"Critical","Identify":"3009171","Alarm":"[告警發生]-大安文 CMTS設備:WS_CBR8_001,Node: LW73A離線率過高異常!"}}'
#payload = '{"source":"catv_dev","event":{"EventTime":"2018/09/18 05:03:03","AlarmID":"AC020FE2018091862784","NetworkType":"AC","Status":"New","Operator":"022","SiteID":"陽明山機房","ObjectID":"CMTS-01","Severity":"Critical","Identify":"3162784","Alarm":"[告警發生]-陽明山 CMTS設備:YMS_CBR8_001,Node: PT29G離線率過高異常!"}}'
#payload  = '{"source":"catv_dev","event":{"EventTime":"2018/09/18 14:37:45","AlarmID":"AC020FE2018081350041","NetworkType":"AC","Status":"New","Operator":"023","SiteID":"觀昇機房"  ,"ObjectID":"CMTS-01","Severity":"Critical","Identify":"T3-FP3-LTU-N01_shelf 0/slot 0/port 0/card_event NE","Alarm":"網管設備重大告警"}}'
payload = '{"source":"catv_dev","event":{"EventTime":"2018/09/18 15:04:03","AlarmID":"AC020FE2018091862001","NetworkType":"AC","Status":"New","Operator":"022","SiteID":"陽明山機房","ObjectID":"CMTS-03","Severity":"Critical","Identify":"3162784","Alarm":"[告警發生]-test陽明山 CMTS設備:YMS_CBR8_001,Node: PT29G離線率過高異常!"}}'
print payload
print '[command->',
print os.popen('curl -s -k --tlsv1.2 -H "Authorization: Splunk 47491100-5C99-4228-85FA-C009FB8AC803" https://211.22.193.184:8088/services/collector/event -d  \'' + payload + '\'').read()     # 调用read()方法可以得到命令的结果  