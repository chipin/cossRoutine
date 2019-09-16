#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# CMMAC: xxxSTB   CPEMAC: xxxSTBdefault
# CMMAC: xxxTV10M CPEMAC: xxxTVSTB
# CMMAC: xxxCPzz  CPEMAC: xxxMTA-yy
import os,sys,time,string,re
from oraclass import ORA
import pexpect
from cnr_backup import CnrBackup

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'
'''執行範例
python bin/cnr/cnr_queue_backup.py debug 103,104 2018/07/31-14:00:00 2018/07/31-15:20:00 none
python bin/cnr/cnr_queue_backup.py debug 103,104 2018/07/31-14:00:00 2018/07/31-15:20:00 22506618,22506615,22506417
python bin/cnr/cnr_queue_backup.py debug 300,701 2018/08/01-14:00:00 2018/08/01-15:30:00 none >> 20180801.log
'''
if  len(sys.argv)!=6:
    print 'please keyin:',sys.argv[0],' debug soTxt sdate edate sidArr'
    sys.exit(0)

debug  = sys.argv[1].lower()
soTxt  = sys.argv[2]
sdate  = sys.argv[3]
edate  = sys.argv[4]
sidArr = sys.argv[5].lower()

def printLog(i,msg):
    print '[no.%s]: %s'%(i,msg)

def mac_fmt_conv(mac = ''):
    mac_fmt = ''
    try:
        ma = re.match(r"^([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$", mac)
        if ma is not None:
            mac_fmt = '1,6,' + ma.group(1) + ':' + ma.group(2) + ':' + ma.group(3) + ':' + ma.group(4) + ':' + ma.group(5) + ':' + ma.group(6)
    except Exception, e:
        print 'mac_fmt_conv() - ERROR: '+str(e)
    return mac_fmt.lower()
 
def main(debug,soTxt,sdate,edate,sidArr):
    cnrBackupData = {}
    # 撈取 cnr ip4 備援ip
    oracon = ORA('nms@cnis')
    sql = "SELECT companyno,apiuser,apipwd,ip4 FROM cnr WHERE stopyn='N' AND companyno IN(%s) AND ip4 IS NOT NULL ORDER BY companyno"%(soTxt)
    rst = oracon.execall(sql)
    if  rst is not None and len(rst)>0:
        for aw in rst:
            so = aw[0]
            cnrBackupData[so] = {}
            cnrBackupData[so]['backupIP'] = aw[3] # ip4
            cnrBackupData[so]['data']     = []
    print sql
    # 撈取 cnr_queue
    if  sidArr=='none':
        sql = '''
        SELECT companyno,sid,TO_CHAR(create_date,'YYYY-MM-DD-HH24:MI:SS') dateTime,cnr_id,command,cmmac,policy,ip,cpemac,status,result,subsid
          FROM cnr_queue 
         WHERE companyno IN(%s) 
           AND command NOT IN('querybw','querymac','rebootcm') 
           AND create_date BETWEEN to_date('%s','yyyy/mm/dd-HH24:mi:ss') AND to_date('%s','yyyy/mm/dd-HH24:mi:ss') 
         ORDER BY companyno
        '''%(soTxt,sdate,edate)
    else:
        sql = '''
        SELECT companyno,sid,TO_CHAR(create_date,'YYYY-MM-DD-HH24:MI:SS') dateTime,cnr_id,command,cmmac,policy,ip,cpemac,status,result,subsid
          FROM cnr_queue 
         WHERE sid IN(%s) 
         ORDER BY companyno
        '''%(sidArr)

    rst = oracon.execall(sql)
    if  rst is not None and len(rst)>0:
        for aw in rst:
            so = aw[0]
            cnrBackupData[so]['data'].append(aw)
    print sql
    # exec command 備援
    for(so,val) in cnrBackupData.items():
        totalNum = len(val['data'])
        if  totalNum>0:
            print '口口口口口口口口口口口口口口口口口口口口'
            print "口  %s-備援%s開始-總筆數%s"%(so,val['backupIP'],totalNum)
            print '口口口口口口口口口口口口口口口口口口口口'
            so_cnrBackup = None
            so_cnrBackup = CnrBackup('cnr',val['backupIP'])
            if  so_cnrBackup is None:
                print 'backup conn fail!'
            else:
                i = 1
                for cnrData in val['data']:
                    company,sid,date,cnrid,command,cmmac,policy,ip,cpemac,status = cnrData[0],str(int(cnrData[1])),cnrData[2],cnrData[3],cnrData[4],cnrData[5],cnrData[6],cnrData[7],cnrData[8],cnrData[9]
                    result = cnrData[10].replace(chr(10),"")
                    subsid = cnrData[11]
                    msg = "%s,%s,date=%s,cnrid=%s,command=%s,cmmac=%s,policy=%s,cpemac=%s,ip=%s,status=%s"%(company,sid,date,cnrid,command,cmmac,policy,cpemac,ip,status)
                    printLog(i,msg)
                    i+=1
                    # 依 command 執行
                    if  command=='active':
                        if  debug=='production':
                            so_cnrBackup.active(cmmac,policy,sid)
                        msg = '[%s]%s %s %s'%(command,cmmac,policy,sid)
                    elif command=='modify':
                        if  debug=='production':
                            so_cnrBackup.modify(cmmac,policy,sid)
                        msg = '[%s]%s %s %s'%(command,cmmac,policy,sid)
                    elif command=='delete':
                        if  debug=='production':
                            so_cnrBackup.delete(cmmac,sid)
                        msg = '[%s]%s %s'%(command,cmmac,sid)
                    elif command=='addfixip':
                        if  result.find("cpemac重覆綁定")>=0:
                            msg = '[%s]該cpemac重覆綁定'%(command)
                        else:
                            scopename = re.match(r"scope(.+)addReservation",result).group(1)
                            mac       = mac_fmt_conv(cpemac)
                            search    = re.match(r"^.+B7[0-9]$",scopename)
                            vip       = 1 if search is not None else 0
                            if  debug=='production':
                                so_cnrBackup.addfixip(scopename,ip,mac,vip,sid)
                            msg = '[%s]%s %s %s %s %s'%(command,scopename,ip,mac,vip,sid)
                    elif command=='addfixip2' or command=='addnatip':
                        if  result.find("cpemac重覆綁定")>=0:
                            msg = '[%s]該cpemac重覆綁定'%(command)
                        else:
                            newscope = re.match(r"scope(.+)addReservation",result).group(1)
                            newip    = policy
                            mac      = mac_fmt_conv(cpemac)
                            search   = re.match(r"^.+B7[0-9]$",newscope)
                            vip      = 1 if search is not None else 0
                            if  debug=='production':
                                so_cnrBackup.addfixip(newscope,newip,mac,vip,sid,'addfixip2')
                            msg = '[%s]%s %s %s %s %s %s'%(command,newscope,newip,mac,vip,sid,'addfixip2')
                    elif command== 'delfixip':
                        scopename = re.match(r"scope(.+)remove",result).group(1)
                        search    = re.match(r"^.+B7[0-9]$",scopename)
                        vip       = 1 if search is not None else 0
                        if  debug=='production':
                            so_cnrBackup.delfixip(ip,scopename,vip,sid)
                        msg = '[%s]%s %s %s %s'%(command,ip,scopename,vip,sid)
                    elif command== 'deactiveip':
                        if  debug=='production':
                            so_cnrBackup.deactiveip(ip,sid)
                        msg = '[%s]%s %s'%(command,ip,sid)
                    elif command== 'activeip':
                        if  debug=='production':
                            so_cnrBackup.activeip(ip,sid)
                        msg = '[%s]%s %s'%(command,ip,sid)
                    elif command == 'fixpublic':
                        addTag = 'Scope-PUB'
                        if  debug=='production':
                            so_cnrBackup.fixpublic(cpemac,addTag,sid)
                        msg = '[%s]%s %s %s'%(command,cpemac,addTag,sid)
                    elif command == 'fixprivate':
                        if  debug=='production':
                            so_cnrBackup.fixprivate(cpemac,policy,sid)
                        msg = '[%s]%s %s %s'%(command,cpemac,policy,sid)
                    elif command == 'ddos':
                        if  debug=='production':
                            so_cnrBackup.ddos(cpemac,sid)
                        msg = '[%s]%s %s'%(command,cpemac,sid)
                    elif command == 'delddos':
                        if  debug=='production':
                            so_cnrBackup.delddos(cpemac,sid)
                        msg = '[%s]%s %s'%(command,cpemac,sid)
                    elif command == 'addcmbsn':
                        if  debug=='production':
                            so_cnrBackup.addcmbsn(cmmac,policy,subsid,sid)
                        msg = '[%s]%s %s %s %s'%(command,cmmac,policy,subsid,sid)
                    elif command == 'addtagscope':
                        addTag = policy
                        if  debug=='production':
                            so_cnrBackup.fixpublic(cpemac,addTag,sid)
                        msg = '[%s]%s %s %s'%(command,cpemac,addTag,sid)
                    elif command == 'deltagscope':
                        if  debug=='production':
                            so_cnrBackup.fixprivate(cpemac,policy,sid)
                        msg = '[%s]%s %s %s'%(command,cpemac,policy,sid)
                    else:
                        msg = '[%s]Unknown command'%(command)
                    print '\t%s'%(msg)
                # 釋放object
                del so_cnrBackup


nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
try:
    print '口口口口口口口口口口口口口口口口口口口口'
    print '口  %s'%(nowdate)
    print '口口口口口口口口口口口口口口口口口口口口'
    main(debug,soTxt,sdate,edate,sidArr)
except KeyboardInterrupt, e: # Ctrl-C
    raise e
except SystemExit, e: # sys.exit()
    raise e
except Exception, e:
    print '['+nowdate+'] Except-05: '+str(e)
    sys.exit()
'''
口cmd == 'addfixip'
  --> registip
  print so_cnrBackup.addfixip(scopename,ip,mac,vip,sid)

口cmd == 'addfixip2'
  --> registip2
  print so_cnrBackup.addfixip(newscope,newip,mac,vip,sid,'addfixip2')

口cmd == 'delfixip'
  --> deregistip
  print so_cnrBackup.delfixip(ip,scopename,vip,sid)

口cmd == 'active'
  --> activate
  print so_cnrBackup.active(mac,profilename,sid)

口cmd == 'modify'
  --> modify
  print so_cnrBackup.modify(mac,profilename,sid)

口cmd == 'delete'
  --> delete
  print so_cnrBackup.delete(mac,sid)

口cmd == 'deactiveip' 
  --> ipdeact
  print so_cnrBackup.deactiveip(ip,sid)

口cmd == 'activeip'
  --> ipact
  print so_cnrBackup.activeip(ip,sid)

口cmd == 'fixpublic'
  cmd == 'addtagscope'
  --> fixip_to_public
  print so_cnrBackup.fixpublic(mac,addTag,sid)

口cmd == 'fixprivate'
  cmd == 'deltagscope'
  --> fixip_to_private
    print so_cnrBackup.fixprivate(mac,policy,sid)

口cmd == 'ddos'
  --> add_ddosflag
  print so_cnrBackup.ddos(mac,sid)

口cmd == 'delddos'
  --> del_ddosflag
  print so_cnrBackup.delddos(mac,sid)

口cmd == 'addcmbsn'
  --> addCMBSN
  print so_cnrBackup.addcmbsn(mac,profilename,subsid,sid)
'''