#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,sys,time,string,re
from oraclass import ORA
import pexpect
import MySQLdb

def cnr_cmd_class_Log(msg):
    fp     = open('/ap/home/coss/log/cnr/new/newipConflictByNewscope/cnr_cmd_class.log','a')
    isTime = time.strftime("%Y/%m/%d %H:%M:%S",time.localtime())
    msg    = "[%s]:%s\n"%(isTime,msg)
    fp.write(msg)
    fp.close()
    
def conn(type,host,cnrUID,cnrPWD):
    connCnr = None
    try:
        path  = '/opt/nwreg2' if type=='cnr' else '/opt/nwreg3/local'
        nrcmd = '%s/usrbin/nrcmd -C %s -N %s -P %s'%(path,host,cnrUID,cnrPWD)
        connCnr = pexpect.spawn(nrcmd,timeout=15)
        connCnr.expect('nrcmd>',timeout=15)
        return connCnr
    except Exception,e:
        if  connCnr is not None:
            connCnr.close(True)
        return None

def strip_rtn_cmd(msg):
    return msg.replace(" ","").replace("'","").replace(chr(13),"").strip()

def arr2Obj(rstArr):
    rtnObj = {}
    rtnObj['command'] = rstArr.pop(0)
    rtnObj['status'] = rstArr.pop(0)
    rtnObj['ip'] = rstArr.pop(0)
    for obj in rstArr:
        arrays = re.split('=',obj)
        index = arrays[0]
        value = arrays[1]
        rtnObj[index] = value
    return rtnObj

def ip2num(ip = ''):
    ipnum = 0
    try:
        ma = re.match(r"^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})$", ip)
        if ma is not None:
            ipnum = int(ma.group(1)) * pow(256,3) + int(ma.group(2)) * pow(256,2) + int(ma.group(3)) * pow(256,1) + int(ma.group(4))
    except Exception, e:
        print 'ip2num() - ERROR: '+str(e)
    return ipnum

def mac_fmt_conv(mac = ''):
    mac_fmt = ''
    try:
        ma = re.match(r"^([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$", mac)
        if ma is not None:
            mac_fmt = '1,6,' + ma.group(1) + ':' + ma.group(2) + ':' + ma.group(3) + ':' + ma.group(4) + ':' + ma.group(5) + ':' + ma.group(6)
    except Exception, e:
        print 'mac_fmt_conv() - ERROR: '+str(e)
    return mac_fmt.lower()

class CnrBackup:
    # 初始化
    cnrShell = None
    oracon   = None
    type     = ''
    host     = ''
    execType = 'MASTER'

    # 建構
    def __init__(self,type,host,execType,cnrUID,cnrPWD,production,execSql):
        self.type       = type
        self.host       = host
        self.execType   = execType.upper()
        self.cnrUID     = cnrUID
        self.cnrPWD     = cnrPWD
        self.production = production
        self.execSql    = execSql
        self.connect    = self.getConnect()

    # 解構
    def __del__(self):
        if  self.cnrShell is not None:
            self.cnrShell.sendline('exit')
            self.cnrShell.close()
            self.cnrShell = None
        if  self.oracon is not None:
            self.oracon.se_close()

    # 自動連接 cnr
    def getConnect(self):
        rst     = False
        connMax = 3
        if  self.cnrShell is not None:
            rst = True
        else:
            for connNum in range(connMax):
                try:
                    self.cnrShell = conn(self.type,self.host,self.cnrUID,self.cnrPWD)
                    if  self.cnrShell is not None:
                        rst = True
                        break
                except Exception,msg:
                    msg = re.sub("'",'',str(msg))
                    print '{"error-%s":"[host=%s][msg=%s]"}'%(connNum,self.host,msg)
                    sys.stdout.flush()
                    time.sleep(5)
        if  self.oracon is None:
            self.oracon = ORA('nms@cnis')
        return rst

    # 執行 cnr 命令，並返回結果
    def sendCnrShell(self,txt):
        print '[cnrCmd]'+txt
        self.cnrShell.sendline(txt)
        self.cnrShell.expect('nrcmd>', timeout=60)
        return self.cnrShell.before

    # update結果
    def result_upt_db(self,status,msg,sid,policy=False):
        try:
            setPolicy = ",policy='%s'"%(policy) if(policy) else ''
            sid = str(sid)
            msg = strip_rtn_cmd(msg)
            msg = msg[0:400].replace(chr(10),"")
            if  self.execType=='MASTER':
                setTxt = "status='%s',result='%s',status_date=SYSDATE%s"%(status,msg,setPolicy)
            else:
                setTxt = "backup_status='%s',backup_result='%s',backup_status_date=SYSDATE%s"%(status,msg,setPolicy)
            upd_sql = "UPDATE cnr_queue SET %s WHERE sid=%s"%(setTxt,sid)
            print '[sql]',upd_sql
            if  self.execSql:
                self.oracon.execone(upd_sql)
                self.oracon.commit()
            print '[sid-%s-result_upt_db ok]'%(sid)
        except Exception,errMsg:
            errMsg = re.sub("'",'',str(errMsg))
            print '[sid-%s-result_upt_db error:%s]'%(sid,errMsg)

    # update結果
    def upt_db(self,upd_sql,sid):
        print '[sql]',upd_sql
        if  self.execSql:
            self.oracon.execone(upd_sql)
            self.oracon.commit()
        print '[sid-%s-upt_db ok]'%(sid)

    # 錯誤訊息
    def errorMsg(self,fnName,sid):
        print '{"x-error":"host=%s,fnName=%s",sid=%s}'%(self.host,fnName,sid)
    ###################################
    # cmd:querymac,querybw
    ###################################
    def querymac(self,ip,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),ip
            return False
        try:
            if  ip is None or len(ip)<=0:
                cmdResult = 'querymac error：ip is null'
                print '{"x-error":"host=%s,fnName=%s,ip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,sid,cmdResult)
                self.result_upt_db('ERROR',cmdResult,sid)
            else:
                cmdResult = self.sendCnrShell('lease ' + ip)
                cmdResult = strip_rtn_cmd(cmdResult)
                cmmac = cpemac = None
                if  cmdResult.find("100Ok") >= 0:
                    arr_res = cmdResult.splitlines()
                    for s in arr_res:
                        if  s.find("relay-agent-remote-id")>=0:
                            ts = s.split('=')
                            if  len(ts) >= 2:
                                cmmac = ts[1].replace(":","")
                        elif s.find("client-mac-addr")>=0:
                            ts = s.split('=')
                            if  len(ts) >= 2:
                                ts1 = ts[1].replace(":","")
                                ts2 = ts1.split(',')
                                if  len(ts2) >= 3:
                                    cpemac = ts2[2]
                cmdResult = cmdResult.replace(chr(10),"")
                if  cmmac is not None and cpemac is not None:
                    if  self.execType=='MASTER':
                        setTxt = "status='%s',result='%s',status_date=SYSDATE"%('OK','querymac OK')
                    else:
                        setTxt = "backup_status='%s',backup_result='%s',backup_status_date=SYSDATE"%('OK','querymac OK')
                    upd_sql = "UPDATE cnr_queue SET cmmac=upper('%s'),cpemac=upper('%s'),%s WHERE sid=%d" % (cmmac,cpemac,setTxt,sid)
                    print '{"success":"host=%s,fnName=%s,cmmac=%s,cpemac=%s,sid=%s,rst=%s"}'%(self.host,fnName,cmmac,cpemac,sid,'querymac ok')
                    self.upt_db(upd_sql,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,cmmac=%s,cpemac=%s,sid=%s,rst=%s"}'%(self.host,fnName,cmmac,cpemac,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,sid=%s,Exception=%s"}'%(self.host,fnName,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def querybw(self,cmmac,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),cmmac
            return False
        try:
            if  cmmac is None or len(cmmac)<=0:
                cmdResult = 'querybw error：mac is null'
                print '{"x-error":"host=%s,fnName=%s,cmmac=%s,sid=%s,rst=%s"}'%(self.host,fnName,cmmac,sid,cmdResult)
                self.result_upt_db('ERROR',cmdResult,sid)
            else:
                cmdResult = self.sendCnrShell('client ' + cmmac)
                cmdResult = strip_rtn_cmd(cmdResult)
                profile = None
                if  cmdResult.find("100Ok") >= 0:
                    arr_res = cmdResult.splitlines()
                    for s in arr_res:
                        if  s.find("client-class-name")>=0:
                            ts = s.split('=')
                            if  len(ts) >= 2 and ts[1] is not None:
                                profile = ts[1]
                                break
                    cmdResult = cmdResult.replace(chr(10),"")
                if  profile is not None:
                    if  self.execType=='MASTER':
                        setTxt = "status='%s',result='%s',status_date=SYSDATE"%('OK','querybw OK')
                    else:
                        setTxt = "backup_status='%s',backup_result='%s',backup_status_date=SYSDATE"%('OK','querybw OK')
                    upd_sql = "UPDATE cnr_queue SET policy='%s',%s WHERE sid=%d" % (profile,setTxt,sid)
                    print '{"success":"host=%s,fnName=%s,cmmac=%s,profile=%s,sid=%s,rst=%s"}'%(self.host,fnName,cmmac,profile,sid,'querybw ok')
                    self.upt_db(upd_sql,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,cmmac=%s,sid=%s,rst=%s"}'%(self.host,fnName,cmmac,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,sid=%s,Exception=%s"}'%(self.host,fnName,sid,e)
            self.result_upt_db('ERROR',e,sid)
    ###################################
    # cmd:active,modify,delete
    ###################################
    def active(self,mac,profilename,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),mac,profilename
            return False
        try:
            if  self.getConnect():
                self.sendCnrShell('client ' + mac + ' delete')
                cmdResult = ''
                if  profilename.find("MTA-") >= 0:
                    cmdResult = self.sendCnrShell('client ' + mac + ' create client-class-name=' + profilename + ' host-name=' + mac)
                else:
                    cmdResult = self.sendCnrShell('client ' + mac + ' create client-class-name=' + profilename)
                self.sendCnrShell('save')
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    print '{"success":"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,sid,cmdResult)
                    cmdResult = cmdResult if(self.execType=='MASTER') else 'active OK'
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,profilename,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def modify(self,mac,profilename,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),mac,profilename
            return False
        try:
            if  self.getConnect():
                cmdResult = ''
                if  profilename.find("MTA-") >= 0:
                    cmdResult = self.sendCnrShell('client ' + mac + ' set client-class-name=' + profilename + ' host-name=' + mac)
                else:
                    cmdResult = self.sendCnrShell('client ' + mac + ' set client-class-name=' + profilename)
                self.sendCnrShell('save')
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    print '{"success":"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,sid,cmdResult)
                    cmdResult = cmdResult if(self.execType=='MASTER') else 'modify OK'
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,profilename,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def delete(self,mac,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),mac
            return False

        try:
            if  self.getConnect():
                cmdResult = ''
                cmdResult = self.sendCnrShell('client ' + mac + ' delete')
                self.sendCnrShell('save')
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    print '{"success":"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    cmdResult = cmdResult if(self.execType=='MASTER') else 'delete OK'
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,mac=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,sid,e)
    ###################################
    # cmd:ddos,delddos
    ###################################
    def ddos(self,mac,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),mac
            return False
        try:
            if  self.getConnect():
                _get_str = ''
                cmdResult = ''
                _get_str = self.sendCnrShell('client ' + mac)
                if  _get_str.find("302 Not Found") >=0:
                    cmdResult = self.sendCnrShell('client ' + mac + ' create selection-criteria=Scope-ddos')
                else:
                    cmdResult = self.sendCnrShell('client ' + mac + ' set selection-criteria=Scope-ddos')
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                self.sendCnrShell('save')
                self.sendCnrShell('dhcp reload')
                if  cmdResult.find("100Ok") >= 0:
                    print '{"success":"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    cmdResult = cmdResult if(self.execType=='MASTER') else 'ddos OK'
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,mac=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def delddos(self,mac,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),mac
            return False
        try:
            if  self.getConnect():
                _get_str = ''
                cmdResult = ''
                _get_str = self.sendCnrShell('client ' + mac)
                if  _get_str.find("302 Not Found") >=0:
                    cmdResult = '100Ok'
                else:
                    cmdResult = self.sendCnrShell('client ' + mac + ' delete')
                    cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                self.sendCnrShell('save')
                self.sendCnrShell('dhcp reload')
                if  cmdResult.find("100Ok") >= 0:
                    print '{"success":"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    cmdResult = cmdResult if(self.execType=='MASTER') else 'delddos OK'
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,mac=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,sid,e)
            self.result_upt_db('ERROR',e,sid)
    ###################################
    # cmd:addcmbsn,fixpublic,fixprivate,addtagscope,deltagscope
    ###################################
    def addcmbsn(self,mac,profilename,subsid,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),mac,profilename,subsid,fnName
            return False
        try:
            if  self.getConnect():
                addcmbsn_rst = True
                # 0.刪除頻寬
                self.sendCnrShell('client ' + mac + ' delete')
                # 1.設定頻寬
                ret_str1 = ''
                rtnMsg   = 'cmd=addcmbsn '
                ret_str1 = self.sendCnrShell('client ' + mac + ' create client-class-name=' + profilename)
                self.sendCnrShell('save')
                ret_str1 = strip_rtn_cmd(ret_str1)
                if  ret_str1.find("100Ok")<0:
                    addcmbsn_rst = False
                # 2.設定 packet-file-name
                ret_str2 = ''
                self.sendCnrShell('force-lock')
                ret_str2 = self.sendCnrShell('client-policy ' + mac + ' set packet-file-name=' + str(subsid) + '.cm')
                self.sendCnrShell('save')
                ret_str2 = strip_rtn_cmd(ret_str2)
                if  ret_str2.find("100Ok")<0:
                    addcmbsn_rst = False
                # 3.設定 selection-criteria
                _get_str = ''
                ret_str3 = ''
                self.sendCnrShell('force-lock')
                _get_str = self.sendCnrShell('client ' + mac)
                if  _get_str.find("302 Not Found")>=0:
                    ret_str3 = self.sendCnrShell('client ' + mac + ' create selection-criteria=Scope-CM')
                else:
                    ret_str3 = self.sendCnrShell('client ' + mac + ' set selection-criteria=Scope-CM')
                self.sendCnrShell('save')
                self.sendCnrShell('dhcp reload')
                ret_str3 = strip_rtn_cmd(ret_str3)
                if  ret_str3.find("100Ok")<0:
                    addcmbsn_rst = False
                # 寫入table
                cmdResult = "[%s,%s,%s]"%(ret_str1,ret_str2,ret_str3)
                if  addcmbsn_rst:
                    print '{"success":"host=%s,fnName=%s,mac=%s,profilename=%s,subsid=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,subsid,sid,cmdResult)
                    cmdResult = cmdResult if(self.execType=='MASTER') else 'addcmbsn OK'
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,mac=%s,profilename=%s,subsid=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,subsid,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,mac=%s,profilename=%s,subsid=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,profilename,subsid,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def fixpublic(self,mac,tag,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),mac,tag
            return False
        try:
            if  self.getConnect():
                _get_str = ''
                _get_str = self.sendCnrShell('client ' + mac)
                if  _get_str.find("302 Not Found") >=0:
                    cmdResult = self.sendCnrShell('client ' + mac + ' create selection-criteria=%s'%(tag))
                else:
                    cmdResult = self.sendCnrShell('client ' + mac + ' set selection-criteria=%s'%(tag))
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                self.sendCnrShell('save')
                self.sendCnrShell('dhcp reload')
                if  cmdResult.find("100Ok") >= 0:
                    print '{"success":"host=%s,fnName=%s,mac=%s,tag=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,tag,sid,cmdResult)
                    cmdResult = cmdResult if(self.execType=='MASTER') else 'fixpublic OK'
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,mac=%s,tag=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,tag,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,mac=%s,tag=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,tag,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def fixprivate(self,mac,policy,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),mac,policy
            return False
        try:
            if  self.getConnect():
                cmdResult = ''
                _get_str = ''
                _get_str = self.sendCnrShell('client ' + mac)
                if  _get_str.find("302 Not Found") >=0:
                    cmdResult = '100Ok'
                else:
                    if  policy=='' or policy==None:
                        # for deltagscope設定cpemac 及 CGNAT 轉privateIP
                        cmdResult = self.sendCnrShell('client ' + mac + ' delete')
                    else:
                        # for deltagscope設定cmmac
                        cmdResult = self.sendCnrShell('client ' + mac + ' unset selection-criteria')
                    cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                self.sendCnrShell('save')
                self.sendCnrShell('dhcp reload')
                if  cmdResult.find("100Ok") >= 0:
                    print '{"success":"host=%s,fnName=%s,mac=%s,policy=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,policy,sid,cmdResult)
                    cmdResult = cmdResult if(self.execType=='MASTER') else 'fixprivate OK'
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,mac=%s,policy=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,policy,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,mac=%s,policy=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,policy,sid,e)
            self.result_upt_db('ERROR',e,sid)
    ###################################
    # cmd:addfixip,addfixip2,addnatip,delfixip,deactiveip,activeip
    ###################################
    def ip2scopeName(self,ip,sid):
        fnName = sys._getframe().f_code.co_name
        rst = {'status':False,'msg':''}
        scopename = ''
        try:
            if  self.getConnect():
                scopename = self.get_scopeNameByIP(ip)
                if  scopename:
                    rst = {'status':True,'msg':scopename}
                else:
                    rst['msg'] = '{"error":"host=%s,fnName=%s,ip=%s,sid=%s,rst=ip2scopeName failure(%s)"}'%(self.host,fnName,ip,sid,cmdResult)
            else:
                self.errorMsg(fnName,sid)
                rst['msg'] = 'db conn failure'
        except Exception, e:
            e = re.sub("'",'',str(e))
            rst['msg'] = '{"error":"host=%s,fnName=%s,ip=%s,sid=%s,Exception=%s"}'%(self.host,fnName,ip,sid,e)
        return rst

    def getNewIpScopeName(self,ip,mac,cmdType,sid):
        searchIP = False
        # 由 mac 查詢是否有重覆綁定
        rstArr = self.sendCnrShell('lease '+ ip)
        rstArr = strip_rtn_cmd(rstArr)
        if  rstArr.find("100Ok")>=0:
            rstArr = re.split(chr(10),rstArr)
            rstArr = arr2Obj(rstArr) 
            if  rstArr['flags'].find("reserved")>=0:
                if  mac==rstArr['client-mac-addr']:
                    rstMsg = '[解決cpemac重覆綁定-flags為reserved且client-mac-addr=cpemac] => [lease %s][status=%s][flags=%s][mac=%s][rtn-mac=%s]'%(ip,rstArr['status'],rstArr['flags'],mac,rstArr['client-mac-addr'])
                    self.result_upt_db('OK',rstMsg,sid,ip)
                    return None
                else:
                    rstMsg = '[解決cpemac重覆綁定問題-ERROR] => [lease %s][status=%s][mac=%s][rtn-mac=%s]'%(ip,rstArr['status'],mac,rstArr['client-mac-addr'])
                    self.result_upt_db('ERROR',rstMsg,sid)
                    return None
            else:
                searchIP = True
        else:
            searchIP = True

        # 由 ip 取得 scope
        if  searchIP:    
            scopeName = self.get_scopeNameByIP(ip)
            if  scopeName:
                if  cmdType=="addfixip2":
                    # addfixip2
                    ma = re.match(r"^(.+)B[0-6|8-9][0-9]$", scopeName)
                else:
                    # addnatip
                    ma = re.match(r"^(.+)P\d\d$", scopeName)
                if  ma is not None:
                    scopeName = ma.group(1)
                    rSQL = "select companyno,scope from cnr_scope_iprange where regexp_like(scope,'^%sB[0-6|8-9][0-9]$') order by companyno,scope" % (scopeName)
                else:
                    # 搜尋scope為C
                    ma = re.match(r"^(.+)C[0-9]{2}$", scopeName) # ex. ANTK24S500C03 -> ANTK24S500
                    if  ma is not None:
                        scopeName = ma.group(1)
                        rSQL = "select companyno,scope from cnr_scope_iprange where regexp_like(scope,'^%sC[0-9]{2}$') order by companyno,scope" % (scopeName)
                    else:
                        scopeName = ''
            if  scopeName=='' or scopeName==False:
                rstMsg ='[sid=%s,cmd=%s,ip=%s,mac=%s]-ERROR-cannot find scopename'%(sid,cmdType,ip,mac)
                print rstMsg
                self.result_upt_db('ERROR',rstMsg,sid)
                return None
            self.sendCnrShell('force-lock')
            self.sendCnrShell('session set default-format=script')
            # 取得 newScope 再取得 newIP
            newip = newscope = ''
            rst = self.oracon.execall(rSQL)
            print '[sql]',rSQL
            if  rst is not None and len(rst)>0:
                for aw in rst:
                    companyno = aw[0] # 2019-05-31-byDavis
                    newscope  = aw[1]
                    print '[newscope=%s]'%(newscope),
                    rstStr = ''
                    rstStr = self.sendCnrShell('scope ' + newscope + ' listleases')
                    if  rstStr is not None and len(rstStr)>0:
                        arr_res = rstStr.splitlines()
                        i = 0
                        for line in arr_res:
                            i = i+1
                            newip1 = ''
                            ma = re.match(r"^([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}): ", line)
                            if  ma is not None:
                                newip1 = ma.group(1)
                                if  line.find("reserved") >= 0 or line.find("deactivated") >= 0: # 保留, 關閉
                                    continue
                                else:
                                    # 2019-05-02-byDavis：若查詢newscope內，被reservations的IP list，包含 newip1 => 則代表異常
                                    IPreservations = False
                                    cmdResult = self.sendCnrShell('scope ' + newscope + ' listreservations')
                                    cmdResult = strip_rtn_cmd(cmdResult)
                                    if  cmdResult.find("100Ok") >= 0:
                                        scopeIpList = cmdResult.splitlines()
                                        for ipInfo in scopeIpList:
                                            if  ipInfo.find(newip1 + ":mac")>=0:
                                                IPreservations = True
                                                conflictMsg = '[異常狀態]查詢 newscope(%s)內，被reservations的IP list(%s)，包含 newip1(%s)'%(newscope,ipInfo,newip1)
                                                cnr_cmd_class_Log(conflictMsg)
                                                break
                                    if  IPreservations:            
                                        continue     
                                    else:
                                        # 2019-05-31-byDavis：查詢新IP，是否在 V2 已被綁定，有綁定則繼續搜尋新IP
                                        rtnIP = self.check_v2_reservedIP_status(companyno,newip1)
                                        if  rtnIP is not None:
                                            continue
                                        print '[newIP，在 V2 未被綁定]'
                                        newip = newip1
                                        print i,'> find IP:',newip
                                        break
                    if  newip is not None and len(newip)>0:
                        break
            self.sendCnrShell('session set default-format=user')
            # 搜尋結果
            if  newip=='' or newscope=='':
                rstMsg ='[sid=%s,cmd=%s,ip=%s,mac=%s]-ERROR-cannot find newIP=%s/newScope=%s'%(sid,cmdType,ip,mac,newip,newscope)
                print rstMsg
                self.result_upt_db('ERROR',rstMsg,sid)
                return None
            else:
                return [newscope,newip]
    def addfixip(self,scopename,so,ip,mac,sid,fnType=None):
        rst = {'status':False,'msg':''}
        fnName = fnType if(fnType) else sys._getframe().f_code.co_name
        newMac = mac_fmt_conv(mac)
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),scopename,ip,mac
            return False
        try:
            if  self.getConnect():
                cmdResult = ''
                vip       = 0
                self.sendCnrShell('force-lock')
                if  fnType is None:
                    # cmd=addfixip
                    if  scopename=='':
                        # 正式機master：由ip抓取scopename
                        getScopeName = self.ip2scopeName(ip,sid)
                        if  getScopeName['status']:
                            scopename = getScopeName['msg']
                        else:
                            print '[sid=%s,cmd=%s,ip=%s]-ERROR-ip cannot find scopename'%(sid,fnName,ip)
                            rst['msg'] = getScopeName['msg']
                            return rst
                else:
                    # cmd=addfixip2,addnatip
                    if  scopename=='':
                        # 2019-05-31-byDavis：檢查 mysql.cpemac 是否已被綁定其他IP
                        rtnData = self.check_cpemac_reservedIP_status(so,mac)
                        if  rtnData is not None:
                            # 有則返回該IP及scopename
                            ip        = rtnData[0]
                            scopename = rtnData[1]
                            cmdResult = '[檢查 mysql.cpemac 已被綁定其他IP，返回該綁定IP,so=%s,cpemac=%s,rtnIP=%s,rtnScope=%s]'%(so,mac,ip,scopename)
                            cnr_cmd_class_Log(cmdResult)
                            search = re.match(r"^.+B7[0-9]$",scopename)
                            vip    = 1 if search is not None else 0
                            print '{"success":"host=%s,fnName=%s,scopename=%s,ip=%s,newMac=%s,vip=%s,sid=%s,rst=%s"}'%(self.host,fnName,scopename,ip,newMac,vip,sid,cmdResult)
                            self.result_upt_db('OK',cmdResult,sid,ip)
                            return False
                        else:
                            # 無則尋找newIP和newScope
                            rst = self.getNewIpScopeName(ip,newMac,fnType,sid)
                            if  rst==None:
                                # 函式 getNewIpScopeName 處理 None 失敗的邏輯
                                return False
                            else:
                                scopename,ip = rst[0],rst[1]
                search = re.match(r"^.+B7[0-9]$",scopename)
                vip    = 1 if search is not None else 0
                cmdResult = self.sendCnrShell('scope ' + scopename + ' addReservation ' + ip + ' ' + newMac)
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    self.sendCnrShell('lease ' + ip + ' send-reservation')
                    self.sendCnrShell('save')
                    self.sendCnrShell('dhcp reload')
                    self.sendCnrShell('lease ' + ip + ' force-available')
                    if  vip == 1:
                        self.sendCnrShell('lease ' + ip + ' activate')
                    self.sendCnrShell('save')
                    self.sendCnrShell('dhcp reload')
                    print '{"success":"host=%s,fnName=%s,scopename=%s,ip=%s,newMac=%s,vip=%s,sid=%s,rst=%s"}'%(self.host,fnName,scopename,ip,newMac,vip,sid,cmdResult)
                    if  fnType is None:
                        # cmd=addfixip
                        rst['status'] = True
                        rst['msg']    = cmdResult
                        return rst
                    else:
                        # cmd=addfixip2,addnatip
                        self.result_upt_db('OK',cmdResult,sid,ip)
                else:
                    if  fnType is None:
                        # cmd=addfixip
                        rst['msg'] = cmdResult
                        return rst
                    else:
                        print '{"x-error":"host=%s,fnName=%s,scopename=%s,ip=%s,newMac=%s,vip=%s,sid=%s,rst=%s"}'%(self.host,fnName,scopename,ip,newMac,vip,sid,cmdResult)
                        self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                if  fnType is None:
                    # cmd=addfixip
                    rst['msg'] = 'db conn failure'
                    return rst
                else:
                    self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,scopename=%s,ip=%s,newMac=%s,vip=%s,sid=%s,Exception=%s"}'%(self.host,fnName,scopename,ip,newMac,vip,sid,e)
            if  fnType is None:
                # cmd=addfixip
                rst['msg'] = e
                return rst
            else:
                self.result_upt_db('ERROR',e,sid)

    def delfixip(self,ip,scopename,sid):
        fnName = sys._getframe().f_code.co_name
        rst = {'status':False,'msg':''}
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),ip,scopename
            return False
        try:
            if  self.getConnect():
                cmdResult = ''
                if  scopename=='':
                    # 正式機master：由ip抓取scopename
                    getScopeName = self.ip2scopeName(ip,sid)
                    if  getScopeName['status']:
                        scopename = getScopeName['msg']
                    else:
                        print '[sid=%s,cmd=%s,ip=%s]-ERROR-ip cannot find scopename'%(sid,fnName,ip)
                        rst['msg'] = getScopeName['msg']
                        return rst                    
                search = re.match(r"^.+B7[0-9]$",scopename)
                vip    = 1 if search is not None else 0
                self.sendCnrShell('force-lock')
                self.sendCnrShell('lease ' + ip + ' delete-reservation')
                cmdResult = ''
                cmdResult = self.sendCnrShell('scope ' + scopename + ' removeReservation ' + ip)
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0 or cmdResult.find("315ImportFailure") >= 0:
                    self.sendCnrShell('save')
                    self.sendCnrShell('dhcp reload')
                    if  vip == 1:
                        self.sendCnrShell('lease ' + ip + ' deactivate')
                    self.sendCnrShell('lease ' + ip + ' force-available')
                    self.sendCnrShell('save')
                    self.sendCnrShell('dhcp reload')
                    print '{"success":"host=%s,fnName=%s,ip=%s,scopename=%s,vip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,scopename,vip,sid,cmdResult)
                    rst['status'] = True
                    rst['msg']    = cmdResult
                    return rst
                else:
                    print '{"x-error":"host=%s,fnName=%s,ip=%s,scopename=%s,vip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,scopename,vip,sid,cmdResult)
                    rst['msg'] = cmdResult
                    return rst
            else:
                self.errorMsg(fnName,sid)
                rst['msg'] = 'db conn failure'
                return rst
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,ip=%s,scopename=%s,vip=%s,sid=%s,Exception=%s"}'%(self.host,fnName,ip,scopename,vip,sid,e)
            rst['msg'] = e
            return rst

    def deactiveip(self,ip,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),ip
            return False
        try:
            if  self.getConnect():
                cmdResult = ''
                cmdResult = self.sendCnrShell('lease ' + ip + ' deactivate')
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    print '{"success":"host=%s,fnName=%s,ip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,ip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,ip=%s,sid=%s,Exception=%s"}'%(self.host,fnName,ip,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def activeip(self,ip,sid):
        fnName = sys._getframe().f_code.co_name
        # 測試
        if  self.production is None:
            print '[測試][%s][%s]'%(sid,fnName),ip
            return False
        try:
            if  self.getConnect():
                cmdResult = ''
                cmdResult = self.sendCnrShell('lease ' + ip + ' activate')
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    print '{"success":"host=%s,fnName=%s,ip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"x-error":"host=%s,fnName=%s,ip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"x-error":"host=%s,fnName=%s,ip=%s,sid=%s,Exception=%s"}'%(self.host,fnName,ip,sid,e)
            self.result_upt_db('ERROR',e,sid)

    # 2019-05-31-byDavis：檢查 mysql.cpemac 是否已被綁定其他IP，有則返回該IP為新IP
    def check_cpemac_reservedIP_status(self,companyno,cpemac):
        mysqldb = None
        rtn     = None
        cpemac  = cpemac.lower()
        try:
            mysqldb  = MySQLdb.connect(host="172.16.13.151",user="root",passwd="Kbro654Tfm",db="ecnis")
            mysqlcur = mysqldb.cursor()
            sql      = "SELECT ip,scope FROM COSS_FIXIP WHERE companyno='%s' AND mac='%s'"%(companyno,cpemac);
            print sql
            mysqlcur.execute(sql)
            result = mysqlcur.fetchall()
            if  result is not None and len(result)>0:
                return [result[0][0],result[0][1]]
        except Exception, msg:
            msg = '[check_cpemac_reservedIP_status: connect MYSQL failure!][companyno=%s,mac=%s]'%(companyno,cpemac)
            print msg
            cnr_cmd_class_Log(msg)
        if  mysqldb is not None:
            mysqldb.close()
        return rtn

    # 2019-05-31-byDavis：查詢新IP，是否在 V2 已被綁定，有綁定則繼續搜尋新IP
    def check_v2_reservedIP_status(self,companyno,ip):
        rtn    = None
        sql    = "SELECT subsid,mac from cnr_fixip_coss WHERE companyno='%s' AND ip='%s' AND stopyn='N'"%(companyno,ip)
        result = self.oracon.execall(sql)
        if  result is not None and len(result)>0:
            rtn = ip
            msg = '[check_v2_reservedIP_status: 查詢新IP在 V2 已被綁定，繼續搜尋新IP!,companyno=%s,findIP=%s,subsid=%s,mac=%s]'%(companyno,ip,result[0][0],result[0][1])
            print msg
            cnr_cmd_class_Log(msg)
        return rtn

    # 函式2019-08-28-byDavis：ip反查 cnr_scope_iprange talbe，撈取scopeName
    def get_scopeNameByIP(self,ip):
        matchIP = re.match(r"^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})$", ip)
        ipnum = int(matchIP.group(1))*pow(256,3) + int(matchIP.group(2))*pow(256,2) + int(matchIP.group(3))*pow(256,1) + int(matchIP.group(4))
        get_scope_sql = "select scope from cnr_scope_iprange where %d between ip_bgv and ip_endv order by updtime desc" % (ipnum)
        get_scope = self.oracon.execall(get_scope_sql)
        if  get_scope is None:
            return False
        else:
            return get_scope[0][0]

'''測試 python cnr_cmd_class.py
ip      = '10.14.161.206'
mac     = mac_fmt_conv('64777DD25223')
cmdType = 'addnatip'
so_cnrBackup = CnrBackup('cnr','10.222.72.110','MASTER','provgw','pv#1176',None,None)
print so_cnrBackup.getNewIpScopeName(ip,mac,cmdType,'11111')
'''