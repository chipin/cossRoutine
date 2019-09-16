#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,sys,time,string,re
from oraclass import ORA
import pexpect

def conn(type,host):
    connCnr = None
    try:
        nrcmd = '/opt/nwreg2/' if type=='cnr' else '/opt/nwreg3/local/'
        nrcmd = nrcmd + 'usrbin/nrcmd -C ' + host + ' -N provgw -P pv#1176' 
        connCnr = pexpect.spawn(nrcmd,timeout=15)
        connCnr.expect('nrcmd>',timeout=15)
        return connCnr
    except Exception,e:
        if  connCnr is not None:
            connCnr.close(True)
        return None

def strip_rtn_cmd(msg):
    return msg.replace(" ","").replace("'","").replace(chr(13),"").strip()

class CnrBackup:
    # 初始化
    cnrShell = None
    oracon   = None

    # 建構
    def __init__(self,type,host):
        self.type = type
        self.host = host
        self.getConnect()

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
                    self.cnrShell = conn(self.type,self.host)
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

    # update備援結果
    def result_upt_db(self,status,msg,sid):
        try:
            sid = str(int(sid))
            msg = "OK" if(status=='OK') else strip_rtn_cmd(msg)
            msg = msg[0:400].replace(chr(10),"")
            upd_sql = "UPDATE cnr_queue SET backup_status='%s',backup_result='%s',backup_status_date=SYSDATE WHERE sid=%s"%(status,msg,sid)
            self.oracon.execone(upd_sql)
            self.oracon.commit()
            print upd_sql
            print '[sid-%s-backup_upt_ok]'%(sid)
        except Exception,errMsg:
            errMsg = re.sub("'",'',str(errMsg))
            print '[sid-%s-backup_upt_err:%s]'%(sid,errMsg)

    def active(self,mac,profilename,sid):
        fnName = sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                self.cnrShell.sendline('client ' + mac + ' delete')
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = ''
                if  profilename.find("MTA-") >= 0:
                    self.cnrShell.sendline('client ' + mac + ' create client-class-name=' + profilename + ' host-name=' + mac)
                else:
                    self.cnrShell.sendline('client ' + mac + ' create client-class-name=' + profilename)
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = self.cnrShell.before
                self.cnrShell.sendline('save')
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    print '{"ok"   :"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,profilename,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def modify(self,mac,profilename,sid):
        fnName = sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                cmdResult = ''
                if  profilename.find("MTA-") >= 0:
                    self.cnrShell.sendline('client ' + mac + ' set client-class-name=' + profilename + ' host-name=' + mac)
                else:
                    self.cnrShell.sendline('client ' + mac + ' set client-class-name=' + profilename)
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = self.cnrShell.before
                self.cnrShell.sendline('save')
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    print '{"ok"   :"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,mac=%s,profilename=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,profilename,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def delete(self,mac,sid):
        fnName = sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                cmdResult = ''
                self.cnrShell.sendline('client ' + mac + ' delete')
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = self.cnrShell.before
                self.cnrShell.sendline('save')
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    print '{"ok"   :"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,mac=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,sid,e)

    def ip2scopeName(self,ip,sid):
        fnName = sys._getframe().f_code.co_name
        scopename = ''
        try:
            if  self.getConnect():
                self.cnrShell.sendline('lease ' + ip + ' get-scope-name')
                self.cnrShell.expect('nrcmd>', timeout=60)
                scopename = self.cnrShell.before.splitlines()[3]
                if  scopename is None or len(scopename)<=0:
                    cmdResult = '{"error":"host=%s,fnName=%s,ip=%s,sid=%s,rst=ip2scopeName failure"}'%(self.host,fnName,ip,sid)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            cmdResult = '{"error":"host=%s,fnName=%s,ip=%s,sid=%s,Exception=%s"}'%(self.host,fnName,ip,sid,e)
            self.result_upt_db('ERROR',cmdResult,sid)
        return scopename

    def addfixip(self,scopename,ip,mac,vip,sid,fnType=None):
        fnName = fnType if(fnType) else sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                cmdResult = ''
                self.cnrShell.sendline('force-lock')
                if  fnType is None:
                    # cmd=addfixip
                    if  scopename=='':
                        # 正式機master：由ip抓取scopename
                        scopename = self.ip2scopeName(ip,sid)
                        if  scopename=='' or scopename==None:
                            return False
                self.cnrShell.sendline('scope ' + scopename + ' addReservation ' + ip + ' ' + mac)
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = self.cnrShell.before
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    self.cnrShell.sendline('lease ' + ip + ' send-reservation')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    self.cnrShell.sendline('save')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    self.cnrShell.sendline('dhcp reload')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    self.cnrShell.sendline('lease ' + ip + ' force-available')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    if  vip == 1:
                        self.cnrShell.sendline('lease ' + ip + ' activate')
                        self.cnrShell.expect('nrcmd>', timeout=60)
                    self.cnrShell.sendline('save')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    self.cnrShell.sendline('dhcp reload')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    print '{"ok"   :"host=%s,fnName=%s,scopename=%s,ip=%s,mac=%s,vip=%s,sid=%s,rst=%s"}'%(self.host,fnName,scopename,ip,mac,vip,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,scopename=%s,ip=%s,mac=%s,vip=%s,sid=%s,rst=%s"}'%(self.host,fnName,scopename,ip,mac,vip,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,scopename=%s,ip=%s,mac=%s,vip=%s,sid=%s,Exception=%s"}'%(self.host,fnName,scopename,ip,mac,vip,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def delfixip(self,ip,scopename,vip,sid):
        fnName = sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                cmdResult = ''
                if  scopename=='':
                    # 正式機master：由ip抓取scopename
                    scopename = self.ip2scopeName(ip,sid)
                    if  scopename=='' or scopename==None:
                        return False
                else:
                    # 備援機slave
                    self.cnrShell.sendline('force-lock')
                self.cnrShell.sendline('lease ' + ip + ' delete-reservation')
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = ''
                self.cnrShell.sendline('scope ' + scopename + ' removeReservation ' + ip)
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = self.cnrShell.before
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0 or cmdResult.find("315ImportFailure") >= 0:
                    self.cnrShell.sendline('save')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    self.cnrShell.sendline('dhcp reload')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    if  vip == 1:
                        self.cnrShell.sendline('lease ' + ip + ' deactivate')
                        self.cnrShell.expect('nrcmd>', timeout=60)
                    self.cnrShell.sendline('lease ' + ip + ' force-available')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    self.cnrShell.sendline('save')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    self.cnrShell.sendline('dhcp reload')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    print '{"ok"   :"host=%s,fnName=%s,ip=%s,scopename=%s,vip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,scopename,vip,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,ip=%s,scopename=%s,vip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,scopename,vip,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,ip=%s,scopename=%s,vip=%s,sid=%s,Exception=%s"}'%(self.host,fnName,ip,scopename,vip,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def deactiveip(self,ip,sid):
        fnName = sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                cmdResult = ''
                self.cnrShell.sendline('lease ' + ip + ' deactivate')
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = self.cnrShell.before
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    print '{"ok"   :"host=%s,fnName=%s,ip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,ip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,ip=%s,sid=%s,Exception=%s"}'%(self.host,fnName,ip,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def activeip(self,ip,sid):
        fnName = sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                cmdResult = ''
                self.cnrShell.sendline('lease ' + ip + ' activate')
                self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = self.cnrShell.before
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                if  cmdResult.find("100Ok") >= 0:
                    print '{"ok"   :"host=%s,fnName=%s,ip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,ip=%s,sid=%s,rst=%s"}'%(self.host,fnName,ip,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,ip=%s,sid=%s,Exception=%s"}'%(self.host,fnName,ip,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def fixpublic(self,mac,tag,sid):
        fnName = sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                _get_str = ''
                cmdResult = ''
                self.cnrShell.sendline('client ' + mac )
                self.cnrShell.expect('nrcmd>', timeout=60)
                _get_str = self.cnrShell.before
                if  _get_str.find("302 Not Found") >=0:
                    self.cnrShell.sendline('client ' + mac + ' create selection-criteria=%s'%(tag))
                    self.cnrShell.expect('nrcmd>', timeout=60)
                else:
                    self.cnrShell.sendline('client ' + mac + ' set selection-criteria=%s'%(tag))
                    self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = self.cnrShell.before
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                self.cnrShell.sendline('save')
                self.cnrShell.expect('nrcmd>', timeout=60)
                self.cnrShell.sendline('dhcp reload')
                self.cnrShell.expect('nrcmd>', timeout=60)
                if  cmdResult.find("100Ok") >= 0:
                    print '{"ok"   :"host=%s,fnName=%s,mac=%s,tag=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,tag,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,mac=%s,tag=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,tag,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,mac=%s,tag=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,tag,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def fixprivate(self,mac,policy,sid):
        fnName = sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                _get_str = ''
                cmdResult = ''
                self.cnrShell.sendline('client ' + mac )
                self.cnrShell.expect('nrcmd>', timeout=60)
                _get_str = self.cnrShell.before
                if  _get_str.find("302 Not Found") >=0:
                    cmdResult = '100Ok'
                else:
                    if  policy=='' or policy==None:
                        # for deltagscope設定cpemac 及 CGNAT 轉privateIP
                        self.cnrShell.sendline('client ' + mac + ' delete')
                    else:
                        # for deltagscope設定cmmac
                        self.cnrShell.sendline('client ' + mac + ' unset selection-criteria' )
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    cmdResult = self.cnrShell.before
                    cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                self.cnrShell.sendline('save')
                self.cnrShell.expect('nrcmd>', timeout=60)
                self.cnrShell.sendline('dhcp reload')
                self.cnrShell.expect('nrcmd>', timeout=60)
                if  cmdResult.find("100Ok") >= 0:
                    print '{"ok"   :"host=%s,fnName=%s,mac=%s,policy=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,policy,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,mac=%s,policy=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,policy,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,mac=%s,policy=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,policy,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def ddos(self,mac,sid):
        fnName = sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                _get_str = ''
                cmdResult = ''
                self.cnrShell.sendline('client ' + mac )
                self.cnrShell.expect('nrcmd>', timeout=60)
                _get_str = self.cnrShell.before
                if _get_str.find("302 Not Found") >=0:
                   self.cnrShell.sendline('client ' + mac + ' create selection-criteria=Scope-ddos')
                   self.cnrShell.expect('nrcmd>', timeout=60)
                else:
                   self.cnrShell.sendline('client ' + mac + ' set selection-criteria=Scope-ddos')
                   self.cnrShell.expect('nrcmd>', timeout=60)
                cmdResult = self.cnrShell.before
                cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                self.cnrShell.sendline('save')
                self.cnrShell.expect('nrcmd>', timeout=60)
                self.cnrShell.sendline('dhcp reload')
                self.cnrShell.expect('nrcmd>', timeout=60)
                if  cmdResult.find("100Ok") >= 0:
                    print '{"ok"   :"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,mac=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def delddos(self,mac,sid):
        fnName = sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                _get_str = ''
                cmdResult = ''
                self.cnrShell.sendline('client ' + mac )
                self.cnrShell.expect('nrcmd>', timeout=60)
                _get_str = self.cnrShell.before
                if  _get_str.find("302 Not Found") >=0:
                    cmdResult = '100Ok'
                else:
                    self.cnrShell.sendline('client ' + mac + ' delete')
                    self.cnrShell.expect('nrcmd>', timeout=60)
                    cmdResult = self.cnrShell.before
                    cmdResult = strip_rtn_cmd(cmdResult).replace(chr(10),"")
                self.cnrShell.sendline('save')
                self.cnrShell.expect('nrcmd>', timeout=60)
                self.cnrShell.sendline('dhcp reload')
                self.cnrShell.expect('nrcmd>', timeout=60)
                if  cmdResult.find("100Ok") >= 0:
                    print '{"ok"   :"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,mac=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,mac=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,sid,e)
            self.result_upt_db('ERROR',e,sid)

    def addcmbsn(self,mac,profilename,subsid,sid):
        fnName = sys._getframe().f_code.co_name
        try:
            if  self.getConnect():
                addcmbsn_rst = True
                # 0.刪除頻寬
                self.cnrShell.sendline('client ' + mac + ' delete')
                self.cnrShell.expect('nrcmd>', timeout=60)
                # 1.設定頻寬
                ret_str1 = ''
                rtnMsg   = 'cmd=addcmbsn '
                self.cnrShell.sendline('client ' + mac + ' create client-class-name=' + profilename)
                self.cnrShell.expect('nrcmd>', timeout=60)
                ret_str1 = self.cnrShell.before
                self.cnrShell.sendline('save')
                self.cnrShell.expect('nrcmd>', timeout=60)
                ret_str1 = strip_rtn_cmd(ret_str1)
                if  ret_str1.find("100Ok")<0:
                    addcmbsn_rst = False
                # 2.設定 packet-file-name
                ret_str2 = ''
                self.cnrShell.sendline('force-lock')
                self.cnrShell.expect('nrcmd>', timeout=60)
                self.cnrShell.sendline('client-policy ' + mac + ' set packet-file-name=' + str(subsid) + '.cm')
                self.cnrShell.expect('nrcmd>', timeout=60)
                ret_str2= self.cnrShell.before
                self.cnrShell.sendline('save')
                self.cnrShell.expect('nrcmd>', timeout=60)
                ret_str2 = strip_rtn_cmd(ret_str2)
                if  ret_str2.find("100Ok")<0:
                    addcmbsn_rst = False
                # 3.設定 selection-criteria
                _get_str = ''
                ret_str3 = ''
                self.cnrShell.sendline('force-lock')
                self.cnrShell.expect('nrcmd>', timeout=60)
                self.cnrShell.sendline('client ' + mac )
                self.cnrShell.expect('nrcmd>', timeout=60)
                _get_str = self.cnrShell.before
                if  _get_str.find("302 Not Found")>=0:
                    self.cnrShell.sendline('client ' + mac + ' create selection-criteria=Scope-CM')
                else:
                    self.cnrShell.sendline('client ' + mac + ' set selection-criteria=Scope-CM')
                self.cnrShell.expect('nrcmd>', timeout=60)
                ret_str3 = self.cnrShell.before
                self.cnrShell.sendline('save')
                self.cnrShell.expect('nrcmd>', timeout=60)
                self.cnrShell.sendline('dhcp reload')
                self.cnrShell.expect('nrcmd>', timeout=60)
                ret_str3 = strip_rtn_cmd(ret_str3)
                if  ret_str3.find("100Ok")<0:
                    addcmbsn_rst = False
                # 寫入table
                cmdResult = "[%s,%s,%s]"%(ret_str1,ret_str2,ret_str3)
                if  addcmbsn_rst:
                    print '{"ok"   :"host=%s,fnName=%s,mac=%s,profilename=%s,subsid=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,subsid,sid,cmdResult)
                    self.result_upt_db('OK',cmdResult,sid)
                else:
                    print '{"error":"host=%s,fnName=%s,mac=%s,profilename=%s,subsid=%s,sid=%s,rst=%s"}'%(self.host,fnName,mac,profilename,subsid,sid,cmdResult)
                    self.result_upt_db('ERROR',cmdResult,sid)
            else:
                self.errorMsg(fnName,sid)
                self.result_upt_db('ERROR','db conn failure',sid)
        except Exception, e:
            e = re.sub("'",'',str(e))
            print '{"error":"host=%s,fnName=%s,mac=%s,profilename=%s,subsid=%s,sid=%s,Exception=%s"}'%(self.host,fnName,mac,profilename,subsid,sid,e)
            self.result_upt_db('ERROR',e,sid)

    # 錯誤訊息
    def errorMsg(self,fnName,sid):
        print '{"error":"host=%s,fnName=%s",sid=%s}'%(self.host,fnName,sid)
