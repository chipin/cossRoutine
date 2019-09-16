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

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv) != 2:
    print 'usage:',sys.argv[0],'SO'
    sys.exit(0)

so = sys.argv[1].upper()

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
            mac_fmt = '1,6,' + ma.group(1) + ':' + ma.group(2) + ':' + ma.group(3) + ':' + ma.group(4) + ':' + ma.group(5) + ':' + ma.group(6) +':'
    except Exception, e:
        print 'mac_fmt_conv() - ERROR: '+str(e)
    return mac_fmt.lower()

def transJson(rstStr):
    rtnObj = {}
    rtnObj['command'] = rstStr.pop(0)
    rtnObj['status'] = rstStr.pop(0)
    rtnObj['ip'] = rstStr.pop(0)
    for obj in rstStr:
        arrays = re.split('=',obj)
        index = arrays[0]
        value = arrays[1]
        rtnObj[index] = value
    return rtnObj
    
def conn(host, uid, pwd):
    try:
        nrcmd = '/opt/nwreg2/usrbin/nrcmd -C ' + host + ' -N ' + uid + ' -P ' + pwd
        print nrcmd
        cnr_shell = pexpect.spawn(nrcmd, timeout=15)
        cnr_shell.expect('nrcmd>', timeout=15)
        print cnr_shell.before
        print 'conn() - OK'
        return cnr_shell
    except Exception, e:
        print 'conn() - ERROR: '+str(e)
        if cnr_shell is not None:
            cnr_shell.close(True)
        return None

def registip(cnr_shell, mac, ip, ora, sid):
    try:
        mac = mac_fmt_conv(mac)
        ipnum = ip2num(ip)
        if mac == '' or ipnum == 0:
            print 'registip() - ERROR: cpemac/ip'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','CPEMAC/IP',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        cnr_shell.sendline('force-lock')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before

        cnr_shell.sendline('lease ' + ip + ' get-scope-name')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        scopename = cnr_shell.before.splitlines()[3]

        if scopename is None or len(scopename) <= 0:
            print 'registip() - ERROR: cannot find scopename'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','cannot find scopename',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        vip = 0
        ma = re.match(r"^.+B7[0-9]$", scopename)
        if ma is not None:
            vip = 1

        _result_str = ''
        cnr_shell.sendline('scope ' + scopename + ' addReservation ' + ip + ' ' + mac)
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _result_str = cnr_shell.before

        _result_str = _result_str.replace(" ","")
        _result_str = _result_str.replace("'","")
        _result_str = _result_str.replace(chr(13),"")
        _result_str = _result_str.strip()

        if _result_str.find("100Ok") >= 0:
            cnr_shell.sendline('lease ' + ip + ' send-reservation')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            cnr_shell.sendline('save')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            cnr_shell.sendline('dhcp reload')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            cnr_shell.sendline('lease ' + ip + ' force-available')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            if vip == 1:
                cnr_shell.sendline('lease ' + ip + ' activate')
                cnr_shell.expect('nrcmd>', timeout=60)
                print cnr_shell.before

            cnr_shell.sendline('save')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            cnr_shell.sendline('dhcp reload')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('OK',_result_str,sid)
            print 'registip() - %s %s => OK' % (mac,ip)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'registip() - %s %s => ERROR' % (mac,ip)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1
    except Exception, e:
        print 'registip() - ERROR: '+str(e)
        return -2
        
def check_ip(cnr_shell, cpemac, ora, scope):
    try:
        mac = mac_fmt_conv(cpemac)
        #print mac
        print scope
        cnr_shell.sendline('force-lock')
        cnr_shell.expect('nrcmd>', timeout=60)
        
        cnr_shell.sendline('scope ' + scope + ' listreservations')
        cnr_shell.expect('nrcmd>', timeout=60)
        _result_str = cnr_shell.before
        if _result_str is not None and len(_result_str) > 0:
          arr_res = _result_str.splitlines()
          print arr_res
          #print arr_res
          #del arr_res[0]
          #del arr_res[1]
          #del arr_res[2]
          #arr_res.remove('100 Ok')
          #arr_res.remove('scope' + scope + ' listreservations')
          #print 'arr_res:',len(arr_res)
          
          #print type(arr_res)
          #i = 0
          #for line in arr_res:
          #  i = i+1
            #print line
            #print line
          #  print line
          #  ip_str = line.find(': mac=')
          #  ip = line[0,ip_str]
          #  print ip
        
       
    except Exception, e:
        print 'registip2() - ERROR: '+str(e)
        return -2       
        
def registip2(cnr_shell, mac, ip, ora, sid, cmdType):
    '''
    registip2流程
    lease ip ok->reserved存在Y->比對mac==rstStr['client-mac-addr']Y->[解決cpemac重覆綁定問題-314Duplicateobject] 
                                                                  N->[解決cpemac重覆綁定問題-ERROR] 
                 reserved存在N->[搜尋newscope > newip > addservation]
             er->[leas ip ERROR] 
    '''
    try:
        mac = mac_fmt_conv(mac)
        ipnum = ip2num(ip)
        if mac == '' or ipnum == 0:
            print 'registip2() - ERROR: cpemac/ip'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','CPEMAC/IP',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1
        # 解決cpemac重覆綁定問題
        
        cmd = 'lease ' + ip
        cnr_shell.sendline(cmd)
        cnr_shell.expect('nrcmd>', timeout=60)
        rstStr = cnr_shell.before
        rstStr = rstStr.replace(" ","").replace("'","").replace('"',"").replace(chr(13),"").strip()
        print rstStr
        if  rstStr.find("100Ok") >= 0:
            rstStr = re.split(chr(10),rstStr)
            rstStr = transJson(rstStr) # 結果範例1
            if  rstStr['flags'].find("reserved") >= 0:
                if  mac==rstStr['client-mac-addr']:
                    rstMsg = '[解決cpemac重覆綁定-flags為reserved且client-mac-addr=cpemac] => [lease %s][status=%s][flags=%s][mac=%s][rtn-mac=%s]'%(ip,rstStr['status'],rstStr['flags'],mac,rstStr['client-mac-addr'])
                    updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s',policy='%s' WHERE sid = %d" % ('OK',rstMsg,ip,sid)
                    print 'registip2() %s -OK' % (rstMsg)
                else:
                    rstMsg = '[解決cpemac重覆綁定問題-ERROR] => [lease %s][status=%s][mac=%s][rtn-mac=%s]'%(ip,rstStr['status'],mac,rstStr['client-mac-addr'])
                    updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',rstMsg,sid)
                    print 'registip2() %s -ERROR' % (rstMsg)
                runAddfixedIP = False
            else:
                runAddfixedIP = True
        else:
            '''
            rstMsg = '[leas ip ERROR] => [lease %s][mac=%s][error=%s]'%(ip,mac,rstStr)
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',rstMsg,sid)
            print 'registip2() %s -ERROR' % (rstMsg)
            runAddfixedIP = False
            '''
            runAddfixedIP = True
        if  runAddfixedIP:    
            scope = ''
            rSQL = "select companyno,scope from cnr_scope_iprange where %d between ip_bgv and ip_endv order by updtime desc" % (ipnum)
            print rSQL
            rst1 = ora.execall(rSQL)
            if rst1 is not None and len(rst1) > 0:
                for aw1 in rst1:
                    scope = aw1[1]
                    break

            if len(scope) > 0:
                # 20180201-byDavis-新增搜尋 addnatip 邏輯
                if  cmdType=="addfixip2":
                    ma = re.match(r"^(.+)B[0-6|8-9][0-9]$", scope)
                else:
                    ma = re.match(r"^(.+)P\d\d$", scope)
                if  ma is not None:
                    scope = ma.group(1)
                    rSQL = "select companyno,scope from cnr_scope_iprange where regexp_like(scope,'^%sB[0-6|8-9][0-9]$') order by companyno,scope" % (scope)
                    print rSQL
                else:
                    # 20170801-byDavis-新增搜尋scope為C的邏輯
                    ma = re.match(r"^(.+)C[0-9]{2}$", scope) # ex. ANTK24S500C03 -> ANTK24S500
                    if  ma is not None:
                        scope = ma.group(1)
                        rSQL = "select companyno,scope from cnr_scope_iprange where regexp_like(scope,'^%sC[0-9]{2}$')   order by companyno,scope" % (scope)
                        print rSQL
                    else:
                        scope = ''

            if scope == '':
                print 'registip2() - ERROR: cannot find scopename'
                updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','cannot find scopename',sid)
                ora.execone(updateSql)
                ora.commit()
                return -1
            cnr_shell.sendline('force-lock')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            cnr_shell.sendline('session set default-format=script')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before
            newip = newscope = ''
            rst1 = ora.execall(rSQL)
            if rst1 is not None and len(rst1) > 0:
                for aw1 in rst1:
                    newscope = aw1[1]
                    print 'search IP:',newscope

                    _result_str = ''
                    cnr_shell.sendline('scope ' + newscope + ' listleases')
                    cnr_shell.expect('nrcmd>', timeout=60)
                    #print cnr_shell.before
                    _result_str = cnr_shell.before
                    if _result_str is not None and len(_result_str) > 0:
                        arr_res = _result_str.splitlines()
                        i = 0
                        for line in arr_res:
                            #print i,'>',line
                            i = i+1
                            newip1 = ''
                            ma = re.match(r"^([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}): ", line)
                            if ma is not None:
                                newip1 = ma.group(1)

                                if line.find("reserved") >= 0 or line.find("deactivated") >= 0: # 保留, 關閉
                                    continue
                                else:
                                    newip = newip1
                                    print i,'> find IP:',newip
                                    break
                    if newip is not None and len(newip) > 0:
                        break
            cnr_shell.sendline('session set default-format=user')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            if newip == '' or newscope == '':
                print 'registip2() - ERROR: cannot find newIP/newScope'
                updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','cannot find newIP/newScope',sid)
                ora.execone(updateSql)
                ora.commit()
                return -1

            vip = 0
            ma = re.match(r"^.+B7[0-9]$", newscope)
            if ma is not None:
                vip = 1

            _result_str = ''
            cnr_shell.sendline('scope ' + newscope + ' addReservation ' + newip + ' ' + mac)
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before
            _result_str = cnr_shell.before

            _result_str = _result_str.replace(" ","")
            _result_str = _result_str.replace("'","")
            _result_str = _result_str.replace(chr(13),"")
            _result_str = _result_str.strip()

            if _result_str.find("100Ok") >= 0:
                cnr_shell.sendline('lease ' + newip + ' send-reservation')
                cnr_shell.expect('nrcmd>', timeout=60)
                print cnr_shell.before

                cnr_shell.sendline('save')
                cnr_shell.expect('nrcmd>', timeout=60)
                print cnr_shell.before

                cnr_shell.sendline('dhcp reload')
                cnr_shell.expect('nrcmd>', timeout=60)
                print cnr_shell.before

                cnr_shell.sendline('lease ' + newip + ' force-available')
                cnr_shell.expect('nrcmd>', timeout=60)
                print cnr_shell.before

                if vip == 1:
                    cnr_shell.sendline('lease ' + newip + ' activate')
                    cnr_shell.expect('nrcmd>', timeout=60)
                    print cnr_shell.before

                cnr_shell.sendline('save')
                cnr_shell.expect('nrcmd>', timeout=60)
                print cnr_shell.before

                cnr_shell.sendline('dhcp reload')
                cnr_shell.expect('nrcmd>', timeout=60)
                print cnr_shell.before

                updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s',policy='%s' WHERE sid = %d" % ('OK',_result_str,newip,sid)
                print 'registip2() - %s %s %s => OK' % (mac,ip,newip)
            else:
                updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
                print 'registip2() - %s %s %s => ERROR' % (mac,ip,newip)
   
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1
    except Exception, e:
        print 'registip2() - ERROR: '+str(e)
        return -2

        
    
def deregistip(cnr_shell, ip, ora, sid):
    try:
        ipnum = ip2num(ip)
        if ipnum == 0:
            print 'deregistip() - ERROR: ip'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','IP',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        cnr_shell.sendline('force-lock')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before

        cnr_shell.sendline('lease ' + ip + ' get-scope-name')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        scopename = cnr_shell.before.splitlines()[3]

        if scopename is None or len(scopename) <= 0:
            print 'deregistip() - ERROR: cannot find scopename'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','cannot find scopename',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        vip = 0
        ma = re.match(r"^.+B7[0-9]$", scopename)
        if ma is not None:
            vip = 1

        cnr_shell.sendline('lease ' + ip + ' delete-reservation')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before

        _result_str = ''
        cnr_shell.sendline('scope ' + scopename + ' removeReservation ' + ip)
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _result_str = cnr_shell.before

        _result_str = _result_str.replace(" ","")
        _result_str = _result_str.replace("'","")
        _result_str = _result_str.replace(chr(13),"")
        _result_str = _result_str.strip()

        if _result_str.find("100Ok") >= 0 or _result_str.find("315ImportFailure") >= 0:
            cnr_shell.sendline('save')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            cnr_shell.sendline('dhcp reload')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            if vip == 1:
                cnr_shell.sendline('lease ' + ip + ' deactivate')
                cnr_shell.expect('nrcmd>', timeout=60)
                print cnr_shell.before

            cnr_shell.sendline('lease ' + ip + ' force-available')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            cnr_shell.sendline('save')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            cnr_shell.sendline('dhcp reload')
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before

            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('OK',_result_str,sid)
            print 'deregistip() - %s => OK' % (ip)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'deregistip() - %s => ERROR' % (ip)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1
    except Exception, e:
        print 'deregistip() - ERROR: '+str(e)
        return -2

def activate(cnr_shell, mac, profilename, ora, sid):
    try:
        if mac is None or len(mac) <= 0 or profilename is None or len(profilename) <= 0:
            print 'activate() - ERROR: mac/profilename is null'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','CMMAC/POLICY is null',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        cnr_shell.sendline('client ' + mac + ' delete')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before

        _result_str = ''
        if profilename.find("MTA-") >= 0:
            cnr_shell.sendline('client ' + mac + ' create client-class-name=' + profilename + ' host-name=' + mac)
        else:
            cnr_shell.sendline('client ' + mac + ' create client-class-name=' + profilename)
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _result_str = cnr_shell.before

        cnr_shell.sendline('save')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before

        _result_str = _result_str.replace(" ","")
        _result_str = _result_str.replace("'","")
        _result_str = _result_str.replace(chr(13),"")
        _result_str = _result_str.strip()
        if _result_str.find("100Ok") >= 0:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('OK',_result_str,sid)
            print 'activate() - %s %s => OK' % (mac,profilename)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'activate() - %s %s => ERROR' % (mac,profilename)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1
    except Exception, e:
        print 'activate() - ERROR: '+str(e)
        return -2

def modify(cnr_shell, mac, profilename, ora, sid):
    try:
        if mac is None or len(mac) <= 0 or profilename is None or len(profilename) <= 0:
            print 'modify() - ERROR: mac/profilename is null'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','CMMAC/POLICY is null',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        _result_str = ''
        if profilename.find("MTA-") >= 0:
            cnr_shell.sendline('client ' + mac + ' set client-class-name=' + profilename + ' host-name=' + mac)
        else:
            cnr_shell.sendline('client ' + mac + ' set client-class-name=' + profilename)
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _result_str = cnr_shell.before

        cnr_shell.sendline('save')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before

        _result_str = _result_str.replace(" ","")
        _result_str = _result_str.replace("'","")
        _result_str = _result_str.replace(chr(13),"")
        _result_str = _result_str.strip()
        if _result_str.find("100Ok") >= 0:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('OK',_result_str,sid)
            print 'modify() - %s %s => OK' % (mac,profilename)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'modify() - %s %s => ERROR' % (mac,profilename)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1
    except Exception, e:
        print 'modify() - ERROR: '+str(e)
        return -2

def delete(cnr_shell, mac, ora, sid):
    try:
        if mac is None or len(mac) <= 0:
            print 'modify() - ERROR: mac is null'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','CMMAC is null',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        _result_str = ''
        cnr_shell.sendline('client ' + mac + ' delete')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _result_str = cnr_shell.before

        cnr_shell.sendline('save')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before

        _result_str = _result_str.replace(" ","")
        _result_str = _result_str.replace("'","")
        _result_str = _result_str.replace(chr(13),"")
        _result_str = _result_str.strip()
        if _result_str.find("100Ok") >= 0:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('OK',_result_str,sid)
            print 'delete() - %s => OK' % (mac)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'delete() - %s => ERROR' % (mac)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1
    except Exception, e:
        print 'delete() - ERROR: '+str(e)
        return -2

def querymac_by_ip(cnr_shell, ip, ora, sid):
    try:
        if ip is None or len(ip) <= 0:
            print 'querymac_by_ip() - ERROR: ip is null'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','IP is null',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        _result_str = ''
        cnr_shell.sendline('lease ' + ip)
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _result_str = cnr_shell.before

        _result_str = _result_str.replace(" ","")
        _result_str = _result_str.replace("'","")
        _result_str = _result_str.replace(chr(13),"")
        _result_str = _result_str.strip()
        cmmac = cpemac = None
        if _result_str.find("100Ok") >= 0:
            arr_res = _result_str.splitlines()
            for s in arr_res:
                if s.find("relay-agent-remote-id") >= 0:
                    ts = s.split('=')
                    if len(ts) >= 2:
                        cmmac = ts[1].replace(":","")
                elif s.find("client-mac-addr") >= 0:
                    ts = s.split('=')
                    if len(ts) >= 2:
                        ts1 = ts[1].replace(":","")
                        ts2 = ts1.split(',')
                        if len(ts2) >= 3:
                            cpemac = ts2[2]
        if cmmac is not None and cpemac is not None:
            updateSql = "UPDATE cnr_queue SET status='%s',cmmac=upper('%s'),cpemac=upper('%s'),status_date=sysdate,result='%s' WHERE sid = %d" % ('OK',cmmac,cpemac,_result_str,sid)
            print 'querymac_by_ip() - %s => OK' % (ip)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'querymac_by_ip() - %s => ERROR' % (ip)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1
    except Exception, e:
        print 'querymac_by_ip() - ERROR: '+str(e)
        return -2

def queryprofile_by_mac(cnr_shell, mac, ora, sid):
    try:
        if mac is None or len(mac) <= 0:
            print 'queryprofile_by_mac() - ERROR: mac is null'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','CMMAC is null',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        _result_str = ''
        cnr_shell.sendline('client ' + mac)
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _result_str = cnr_shell.before

        _result_str = _result_str.replace(" ","")
        _result_str = _result_str.replace("'","")
        _result_str = _result_str.replace(chr(13),"")
        _result_str = _result_str.strip()
        profile = None
        if _result_str.find("100Ok") >= 0:
            arr_res = _result_str.splitlines()
            for s in arr_res:
                if s.find("client-class-name") >= 0:
                    ts = s.split('=')
                    if len(ts) >= 2 and ts[1] is not None:
                        profile = ts[1]
                        break
        if profile is not None:
            updateSql = "UPDATE cnr_queue SET status='%s',policy='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('OK',profile,_result_str,sid)
            print 'queryprofile_by_mac() - %s => OK' % (mac)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'queryprofile_by_mac() - %s => ERROR' % (mac)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1
    except Exception, e:
        print 'queryprofile_by_mac() - ERROR: '+str(e)
        return -2

def get_ipusage(cnr_shell, ora):
    try:
        _result_str = ''
        cnr_shell.sendline('report')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _result_str = cnr_shell.before

        if _result_str.find("100 Ok") >= 0:
            array_data = _result_str.splitlines()
            for s in array_data:
                s = string.strip(s)
                array_line = string.split(s)

                if (len(array_line) == 16 and int(array_line[1]) > 16 and int(array_line[1]) < 32 and array_line[4] != 'LeaseQuery'):
                    scope = array_line[4]
                    used = int(array_line[6]) - int(array_line[8])
                    free = array_line[8]
                    reserved = array_line[9]
                    #print 'Scope: ' + array_line[4] + ', Used: ' + array_line[6] + '=' + array_line[8] + '+' + str(used) + ', Free: ' + free + ', Reserved: ' + reserved

                    if len(scope) > 0:
                        updateSql = "UPDATE cnr_scope_iprange SET used='%d',used_updtime=sysdate,free='%s',reserved='%s' WHERE scope = '%s'" % (used,free,reserved,scope)
                        print updateSql
                        ora.execone(updateSql)
                        ora.commit()
            print 'get_ipusage() - OK'
            return 1
        else:
            print 'get_ipusage() - FAIL'
            return -1
    except Exception, e:
        print 'get_ipusage() - ERROR: '+str(e)
        return -2

def ipdeact(cnr_shell, ip, ora, sid):
    try:
        ipnum = ip2num(ip)
        if ipnum == 0:
            print 'ipdeact() - ERROR: ip'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','IP',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        #cnr_shell.sendline('force-lock')
        #cnr_shell.expect('nrcmd>', timeout=60)
        #print cnr_shell.before

        _result_str = ''
        cnr_shell.sendline('lease ' + ip + ' deactivate')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _result_str = cnr_shell.before

        _result_str = _result_str.replace(" ","")
        _result_str = _result_str.replace("'","")
        _result_str = _result_str.replace(chr(13),"")
        _result_str = _result_str.strip()

        if _result_str.find("100Ok") >= 0:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('OK',_result_str,sid)
            print 'ipdeact() - %s => OK' % (ip)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'ipdeact() - %s => ERROR' % (ip)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1
    except Exception, e:
        print 'ipdeact() - ERROR: '+str(e)
        return -2

def ipact(cnr_shell, ip, ora, sid):
    try:
        ipnum = ip2num(ip)
        if ipnum == 0:
            print 'ipact() - ERROR: ip'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','IP',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        #cnr_shell.sendline('force-lock')
        #cnr_shell.expect('nrcmd>', timeout=60)
        #print cnr_shell.before

        _result_str = ''
        cnr_shell.sendline('lease ' + ip + ' activate')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _result_str = cnr_shell.before

        _result_str = _result_str.replace(" ","")
        _result_str = _result_str.replace("'","")
        _result_str = _result_str.replace(chr(13),"")
        _result_str = _result_str.strip()

        if _result_str.find("100Ok") >= 0:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('OK',_result_str,sid)
            print 'ipact() - %s => OK' % (ip)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'ipact() - %s => ERROR' % (ip)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1
    except Exception, e:
        print 'ipact() - ERROR: '+str(e)
        return -2   

def fixip_to_public(customizeTag,cnr_shell, mac, ora, sid):
    try:
        #mac = mac_fmt_conv(mac)
        #print mac

        if  mac == '':
            print 'fixip_public() - ERROR: cmmac is Null'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','CPEMAC/IP',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1
        _get_str = ''
        _result_str = ''
        cnr_shell.sendline('client ' + mac )
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        _get_str = cnr_shell.before

        # use cmd=addtagscope(自定tag=policy) 或 fixpublic(tag=Scope-PUB)
        addTag = 'Scope-PUB' if customizeTag=='' else customizeTag
        if _get_str.find("302 Not Found") >=0:
           cnr_shell.sendline('client ' + mac + ' create selection-criteria=%s'%(addTag))
           cnr_shell.expect('nrcmd>', timeout=60)
           print cnr_shell.before
        else:
           cnr_shell.sendline('client ' + mac + ' set selection-criteria=%s'%(addTag))
           cnr_shell.expect('nrcmd>', timeout=60)
           print cnr_shell.before
        _result_str = cnr_shell.before
        cnr_shell.sendline('save')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before
        cnr_shell.sendline('dhcp reload')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before

        _result_str = _result_str.replace(" ","")
        _result_str = _result_str.replace("'","")
        _result_str = _result_str.replace(chr(13),"")
        _result_str = _result_str.strip()

        if _result_str.find("100Ok") >= 0:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('OK',_result_str,sid)
            print 'fixip_public() - %s => OK' % (mac)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'fixip_public() - %s => ERROR' % (mac)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1

    except Exception, e:
        print 'fixip_public() - ERROR: '+str(e)
        return -2


def get_subsid(companyno,cmmac):
       

             
def get_cmmac(companyno,ip,cpemac):
    mysqldb  = MySQLdb.connect(host="172.16.13.127",user="root",passwd="Kbro654Tfm",db="cnrlog")
    mysqlcur = mysqldb.cursor()
    try:
      if companyno =='101' or companyno =='103' or companyno =='104' or companyno =='300' or companyno =='701':
        s_table = 'T2019'
      else:
        s_table = 'K2019'
      sql = "SELECT cpe_ip,cpe_mac,remote_id from %s where companyno='%s' and cpe_ip='%s' order by expire_time desc limit 0,1" %(s_table,companyno,ip)
      mysqlcur.execute(sql)
      result = mysqlcur.fetchall()
      if  result is not None and len(result)>0:
        for ak in result:
          try:
            cpeip = ak[0]
            cpemac = ak[1]
            remote_id = ak[2]
            print cpeip,':',cpemac,':',remote_id
          except Exception, msg:
            print '[Exception]while cnr_loop',msg
    except Exception, msg:
          print '[Exception]while cnr_loop',msg
    return sql
    
def main(so):
    mysqldb  = MySQLdb.connect(host="172.16.13.151",user="root",passwd="Kbro654Tfm",db="ecnis")
    mysqlcur = mysqldb.cursor()
    
    sql      = "SELECT companyno,ip,mac,scope,updatetime FROM COSS_FIXIP WHERE companyno='%s' limit 10"%(so)
    print sql
    mysqlcur.execute(sql)
    result = mysqlcur.fetchall()
    
    if  result is not None and len(result)>0:
      for aw in result:
        try:
          companyno = aw[0]
          ip = aw[1]
          mac = aw[2]
          scope = aw[3]
          print companyno,';',ip,';',scope
          print get_cmmac(companyno,ip,mac)
        except Exception, msg:
          print '[Exception]while cnr_loop'
try:
    main(so)
except KeyboardInterrupt, e: # Ctrl-C
    raise e
except SystemExit, e: # sys.exit()
    raise e
except Exception, e:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Except-05: '+str(e)
    sys.exit()
