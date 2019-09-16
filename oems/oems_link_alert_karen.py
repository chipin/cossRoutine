#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
import urllib2,MultipartPostHandler
import cossdb,pymssql
from oraclass import ORA
from pysnmpclass import snmpclass


reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'


#URL = 'https://v2.kbro.com.tw/portal/oems/bomb/bomb_close_sendsms.php'
#header = {'Content-Type' : 'application/json', 'Accept-charset' : 'UTF-8'}
#payload = "{'sid' : '200603350360'}"
#response = requests.post(URL, data=payload, headers=header, verify=False)
#print response.text
url = 'https://v2.kbro.com.tw/portal/oems/bomb/bomb_close_sendsms.php'
post_data = {}
post_data['sid'] = '3367990'
opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
jsonstr = opener.open(url, post_data).read()
print 'RESULT:',jsonstr