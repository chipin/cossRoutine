#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# CMMAC: xxxSTB   CPEMAC: xxxSTBdefault
# CMMAC: xxxTV10M CPEMAC: xxxTVSTB
# CMMAC: xxxCPzz  CPEMAC: xxxMTA-yy
import os,sys,time,string,re
from oraclass import ORA
import pexpect
from pysnmpclass import snmpclass

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

# 函式：取日期時間
def get_exec_datetime():
    return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())

# 函式：執行 ftth snmpset
def exec_ftth_set(setOid,setOltIP,setNum,setType,setVal):
    global agent,comm,line,uptResult
    Oid = '%s.%s'%(setOid,setNum) # ex -> .1.3.6.1.4.1.6296.101.23.3.2.6
    result = agent.snmpset([setOltIP,'-c',comm,Oid,setType,setVal])
    # result = True
    if  result is not None:
        msg = '[step-%d:SET %s-> %s %s %s]'%(line,'OK',Oid,setType,setVal)
        errStatus = 0
    else:
        msg = '[step-%d:SET %s-> %s %s %s]'%(line,'ERROR',Oid,setType,setVal)
        errStatus = 1
    # uptResult += msg
    print msg
    line+=1
    return errStatus


# 函式：系統存檔
def ftth_set_systemSave(setOltIP):
    global line,uptResult
    msg = '[系統存檔systemSave-%s]'%(get_exec_datetime())
    uptResult += msg
    print msg
    line = 1
    errStatus = 0
    errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.1.1.2',setOltIP,'1' ,'i','11')
    errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.1.1.2',setOltIP,'29','i','1')
    errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.1.1.2',setOltIP,'3' ,'i','300')
    uptResult += '[errStatus=%s]'%(errStatus)
    return errStatus

# 函式：設定 profile
def ftth_set_profile(setOid,setOltIP,ponPort,ontId,ontSn,profile):
    global line,uptResult
    msg = '[設定 profile-%s]'%(get_exec_datetime())
    uptResult += msg
    print msg
    line = 1
    errStatus = 0
    errStatus+=exec_ftth_set(setOid,setOltIP,'1' ,'i','3')
    errStatus+=exec_ftth_set(setOid,setOltIP,'6' ,'i',ponPort)
    errStatus+=exec_ftth_set(setOid,setOltIP,'7' ,'i',ontId)
    errStatus+=exec_ftth_set(setOid,setOltIP,'8' ,'s',ontSn)
    errStatus+=exec_ftth_set(setOid,setOltIP,'12','s',profile)
    errStatus+=exec_ftth_set(setOid,setOltIP,'3','i','0')
    uptResult += '[errStatus=%s]'%(errStatus)
    return errStatus

# 函式：重啟 ont
def ftth_reset_ont(ponPort,ontId,setOltIP):
    global line,uptResult
    msg = '[重啟 ont-%s]'%(get_exec_datetime())
    uptResult += msg
    print msg
    line = 1
    errStatus = 0
    errStatus+=exec_ftth_set(setOid,setOltIP,'1','i','8')
    errStatus+=exec_ftth_set(setOid,setOltIP,'6','i',ponPort)
    errStatus+=exec_ftth_set(setOid,setOltIP,'7','i',ontId)
    errStatus+=exec_ftth_set(setOid,setOltIP,'3','i','0')
    uptResult += '[errStatus=%s]'%(errStatus)
    return errStatus

# 函式：移除 ont
def ftth_remove_ont(ponPort,ontId,setOltIP):
    global line,uptResult
    msg = '[移除 ont-%s]'%(get_exec_datetime())
    uptResult += msg
    print msg
    line = 1
    errStatus = 0
    errStatus+=exec_ftth_set(setOid,setOltIP,'1','i','2')
    errStatus+=exec_ftth_set(setOid,setOltIP,'6','i',ponPort)
    errStatus+=exec_ftth_set(setOid,setOltIP,'7','i',ontId)
    errStatus+=exec_ftth_set(setOid,setOltIP,'3','i','0')
    uptResult += '[errStatus=%s]'%(errStatus)
    return errStatus

# 函式：設定 RF介面開關
def ftth_rf_switch(ponPort,ontId,setOltIP,ontSn,switch):
    global line,uptResult
    msg = '[設定 RF介面開關-%s]'%(get_exec_datetime())
    uptResult += msg
    print msg
    line = 1
    if  switch=='on':
        turn = '1'
    else:
        turn = '2'
    msg = '[turn=%s(on=1,off=2)]'%(turn)
    uptResult+=msg
    print msg
    errorNum = 0
    while True:
        errStatus = 0
        errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.1.2',setOltIP,'1' ,'i','1')
        errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.1.2',setOltIP,'6' ,'i',ponPort)
        errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.1.2',setOltIP,'7' ,'i',ontId)
        errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.1.2',setOltIP,'8' ,'i','4')
        errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.1.2',setOltIP,'9' ,'i','1')
        errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.1.2',setOltIP,'11','s',ontSn)
        errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.1.2',setOltIP,'10','i',turn)
        errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.1.2',setOltIP,'3' ,'i','0')
        if  errStatus:
            # errStatus=1，表示執行錯誤
            time.sleep(10)
            msg = '[ftth_rf_switch-try-again-errStatus=%s]'%(errStatus)
            uptResult+=msg
            print msg
            errorNum+=1
            if  errorNum>=3:
                return True
            continue
        else:
            # RF介面開關設定成功，需更新RF狀態表 
            errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.8.2',setOltIP,'1' ,'i','1')
            errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.8.2',setOltIP,'6' ,'i',ponPort)
            errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.8.2',setOltIP,'7' ,'i',ontId)
            errStatus+=exec_ftth_set('.1.3.6.1.4.1.6296.101.23.6.8.2',setOltIP,'3' ,'i','0')
            return False

def upt_ftth_status(oracon,sid,result,status):
    sql = "UPDATE ftth_port_prov_queue SET status='%s',result='%s' WHERE sid='%s'"%(status,result,sid)
    print sql
    oracon.execone(sql)
    oracon.commit()

def main():
    global setOid,uptResult
    oracon = None
    sql    = "select * from v_ftth_prov_queue"
    print sql
    force_clean = 0
    while 1:
        if  oracon is None:
            oracon = ORA('nms@cnis')
        if  oracon.db is None:
            sys.exit('error:資料庫連接錯誤')
        rst = None
        if  oracon.cexist():
            rst = oracon.execall(sql)
            if  rst==None or len(rst)==0:
                # 無資料則sleep三秒
                print 'Wating 3s....',
                time.sleep(3)
                force_clean+=1
                if  force_clean>=500:
                    force_clean = 0
                    sys.stdout.flush()
            else:
                for row in rst:
                    # 變數
                    setOid    = '.1.3.6.1.4.1.6296.101.23.3.2'
                    sid       = int(row[0])
                    companyno = int(row[1])
                    subsid    = int(row[2])
                    ne_id     = row[3]
                    setOltIP  = row[4]
                    ponPort   = str(int(row[5]))
                    ontId     = str(int(row[6]))
                    ontSn     = row[7]
                    profile   = row[8]
                    command   = row[9]
                    # 測試 profile = 'FH12M3M'
                    # 測試 command = 'ACTIVE'
                    print '\n[start sid=%s,companyno=%s,subsid=%s,ne_id=%s,setOltIP=%s,ponPort=%s,ontId=%s,ontSn=%s,profile=%s,command=%s]'%(sid,companyno,subsid,ne_id,setOltIP,ponPort,ontId,ontSn,profile,command)
                    if  command=='ACTIVE':
                        # 設定 profile
                        uptResult = ''
                        errRst = ftth_set_profile(setOid,setOltIP,ponPort,ontId,ontSn,profile)
                        if  errRst:
                            upt_ftth_status(oracon,sid,uptResult,'ERROR')
                        else:
                            # 重啟 ont
                            ftth_reset_ont(ponPort,ontId,setOltIP)
                            # 執行存檔
                            ftth_set_systemSave(setOltIP)
                            upt_ftth_status(oracon,sid,uptResult,'OK')
                    elif command=='DEACTIVE':
                        # 移除 ont
                        uptResult = ''
                        errRst = ftth_remove_ont(ponPort,ontId,setOltIP)
                        if  errRst:
                            upt_ftth_status(oracon,sid,uptResult,'ERROR')
                        else:
                            # 執行存檔
                            ftth_set_systemSave(setOltIP)
                            upt_ftth_status(oracon,sid,uptResult,'OK')
                    elif command=='RFON':
                        # 設定 RF介面ON
                        uptResult = ''
                        errRst = ftth_rf_switch(ponPort,ontId,setOltIP,ontSn,'on')
                        if  errRst:
                            upt_ftth_status(oracon,sid,uptResult,'ERROR')
                        else:
                            # 執行存檔
                            ftth_set_systemSave(setOltIP)
                            upt_ftth_status(oracon,sid,uptResult,'OK')
                    elif command=='RFOFF':
                        # 設定 RF介面OFF
                        uptResult = ''
                        errRst = ftth_rf_switch(ponPort,ontId,setOltIP,ontSn,'off')
                        if  errRst:
                            upt_ftth_status(oracon,sid,uptResult,'ERROR')
                        else:
                            # 執行存檔
                            ftth_set_systemSave(setOltIP)
                            upt_ftth_status(oracon,sid,uptResult,'OK')
                    else:
                        print 'command不在執行範圍內'
        sys.stdout.flush()
        # 測試：僅執行一次
        # break

##############
# 開始
##############
# 全域變數
line  = 1
comm  = 'NMS_Snmp'
agent = snmpclass(version='v2c',community=comm,ptimeout=3,pretries=5)
if  agent is None:
    print 'ERROR: except snmpclass NMS_Snmp'
    sys.exit()

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print '\n#####################################################################################################################################'
print '# 程式開始'
print '#',nowdate

setOid    = None
uptResult = ''
try:
    main()
except KeyboardInterrupt, e:
    # Ctrl-C
    raise e
    if  oracon.db is not None:
        oracon.se_close()
