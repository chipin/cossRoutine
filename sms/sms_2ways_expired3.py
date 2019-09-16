#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# CMMAC: xxxSTB   CPEMAC: xxxSTBdefault
# CMMAC: xxxTV10M CPEMAC: xxxTVSTB
# CMMAC: xxxCPzz  CPEMAC: xxxMTA-yy
import time,sys,os,re
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

def upt_db(dbName):
    # db 連接
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    oracon = None
    oracon = ORA(dbName)
    try:
        if  oracon.db is None:
            print "[contents=DB Connect Faile-%s]"%(dbName)
            sys.stdout.flush()
        else:
            # 更新oracle 欄位 rtn_msg 為 2ways => expired
            upd_sql = "UPDATE oss_sms SET rtn_msg='expired',UPDATE_RTN_TIME=SYSDATE WHERE rtn_msg='2ways' AND status='OK' AND STATUS_DATE <= sysdate-3"
            oracon.execone(upd_sql) # 執行不回傳，用execone
            oracon.commit()
            print "[update oss_sms-OK(%s)]%s\n"%(dbName,upd_sql)
    except Exception,msg:
        print '[%s][contents=UPDATE DB ERROR]%s'%(nowdate,msg)
        sys.stdout.flush()
    oracon.se_close()
    
##############################################
# 主程式開始
##############################################
print '\n# 主程式開始'
print '# kbro'
upt_db('coss@kbro_nmsdb') # 凱擘
upt_db('coss@cnis')       # 台媒
sys.exit(0)
