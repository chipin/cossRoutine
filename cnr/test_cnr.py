#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# CMMAC: xxxSTB   CPEMAC: xxxSTBdefault
# CMMAC: xxxTV10M CPEMAC: xxxTVSTB
# CMMAC: xxxCPzz  CPEMAC: xxxMTA-yy
import os,sys,time,string,re
from oraclass import ORA
import pexpect
import MySQLdb
from cnr_cmd_class_davis import CnrBackup


reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'
'''
  python /ap/home/coss/bin/cnr/test_run_cnr.py
  240	10.222.40.79  
  240	10.222.44.79  
'''

def mac_fmt_conv(mac = ''):
    mac_fmt = ''
    try:
        ma = re.match(r"^([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$", mac)
        if ma is not None:
            mac_fmt = '1,6,' + ma.group(1) + ':' + ma.group(2) + ':' + ma.group(3) + ':' + ma.group(4) + ':' + ma.group(5) + ':' + ma.group(6)
    except Exception, e:
        print 'mac_fmt_conv() - ERROR: '+str(e)
    return mac_fmt.lower()
soIpMaping = {
    'GS0_CCNR_001'   :'192.168.152.32',
    'MD1_CCNR_001'   :'192.168.144.32',
    'CG_CNR1_001'    :'10.222.112.79',
    'DA_CNR1_001'    :'10.222.40.79',
    'WS_CNR1_001'    :'10.222.44.79',
    'TC_CNR1_001'    :'10.222.48.79',
    'UI0_CCNR_001'   :'192.168.160.32',
    'CT_CNR1_001'    :'10.222.72.79',
    'NTY_CNR1_001'   :'10.222.64.79',
    'FM_CNR1_001'    :'10.222.80.79',
    'FM-HL_CNR1_001' :'10.223.20.25',
    'NCC_CNR1_001'   :'10.222.88.79',
    'NT_CNR1_001'    :'10.220.96.79',
    'PL0_CCNR_001'   :'192.168.169.32',
    'PN_CNR1_001'    :'10.222.104.79'
}




print '''
###############
# 測試開始
###############
'''
if  len(sys.argv)!=2:
    print '[Error]usage:',sys.argv[0],',Please input sid'
    sys.exit(0)


production = None # True None
execSql    = None # True None
getSid     = sys.argv[1] # '28219997'
oracon     = ORA('nms@cnis')
sql        = "select companyno,command,sid,policy,cpemac,ip,cnr_id from cnr_queue where sid='%s'"%(getSid)
result     = oracon.execall(sql)
if  result is not None and len(result)>0:
    so         = result[0][0]
    cmdType    = result[0][1]
    sid        = int(result[0][2])
    newCpemac  = result[0][3]
    oldCpemac  = result[0][4]
    ip         = result[0][5]
    cnr_id     = result[0][6]
    connIP     = soIpMaping[cnr_id]
    #print so,connIP,cmdType,sid,newCpemac,oldCpemac,ip

cnr_shell = CnrBackup('cnr',connIP,'MASTER','provgw','pv#1176',production,execSql)
# 測試：
print '[測試]'
rtnData = cnr_shell.get_scopeNameByIP(ip)
if  rtnData:
    print 'scopeName=%s'%(rtnData)
else:    
    print 'query error!'
