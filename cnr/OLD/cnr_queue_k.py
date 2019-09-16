#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# CMMAC: xxxSTB   CPEMAC: xxxSTBdefault
# CMMAC: xxxTV10M CPEMAC: xxxTVSTB
# CMMAC: xxxCPzz  CPEMAC: xxxMTA-yy
import os,sys,time,string,re,urllib2,pexpect
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

###################################################################
# 測試post,put,delete
import os,sys,time,string,re,urllib2,urllib,pexpect,base64
# 初始化
posturl = 'http://10.222.2.104:8080/web-services/rest/resource/Reservation'
cs_user = 'provgw'
cs_pawd = 'pv#1176'
print '----handler1.read(POST)(',posturl,')v1.3--------------------------------'
print '---',time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
data = {'name': 'B1','objectOid': 'OID-78:8D:F7:C5:70:10','policy': 'default','embeddedPolicy': '','vpnId':'', 'subnet':'','rangeList': '','selectionTagList':''}  
data = urllib.urlencode(data)  


# 設定
handler = urllib2.HTTPHandler()
opener = urllib2.build_opener(handler)
request = urllib2.Request(posturl, data)
request.add_header('Accept', 'application/json')
request.add_header('Content-Type', 'application/json')
request.get_method = lambda: 'POST'

# 認證
base64string = base64.b64encode('%s:%s' % (cs_user, cs_pawd))
request.add_header("Authorization", "Basic %s" % base64string)  

# 執行
handler1 = urllib2.urlopen(request)
if handler1.getcode() == 200:
    from pprint import pprint
    text = handler1.read()
    print(json.loads(text))
################################################################### 
