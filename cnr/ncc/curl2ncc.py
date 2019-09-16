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
payload  = '{"source":"HEC_TEST","event":{"EventTime":"%s","AlarmID":"AC020FE%s","NetworkType":"AC","Status":"Information","Operator":"020","SiteID":"HEC-TEST","ObjectID":"HEC-TEST","Severity":"HEC-TEST","Identify":"HEC-TEST","Alarm":"HEC-TEST(%s測試)"}}'%(dateTime,alarmID,'COMMAND')
print '[command->',
# 2019-03-26-將ip更換domain
# print os.popen('curl -s -k --tlsv1.2 -H "Authorization: Splunk 47491100-5C99-4228-85FA-C009FB8AC803" https://211.22.193.184:8088/services/collector/event -d  \'' + payload + '\'').read()     # 调用read()方法可以得到命令的结果  
print os.popen('curl -s -k --tlsv1.2 -H "Authorization: Splunk 47491100-5C99-4228-85FA-C009FB8AC803" https://hec.nccsc.ncc.gov.tw:8088/services/collector/event -d  \'' + payload + '\'').read()     # 调用read()方法可以得到命令的结果  