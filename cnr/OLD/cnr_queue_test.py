#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# CMMAC: xxxSTB   CPEMAC: xxxSTBdefault
# CMMAC: xxxTV10M CPEMAC: xxxTVSTB
# CMMAC: xxxCPzz  CPEMAC: xxxMTA-yy
import os,sys,time,string,re
from oraclass import ORA
import pexpect

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv) != 2:
    print 'usage:',sys.argv[0],'CNR_ID'
    sys.exit(0)

cnr = sys.argv[1].upper()

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

def registip2(cnr_shell, mac, ip, ora, sid):
    try:
        mac = mac_fmt_conv(mac)
        ipnum = ip2num(ip)
        if mac == '' or ipnum == 0:
            print 'registip2() - ERROR: cpemac/ip'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','CPEMAC/IP',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1

        scope = ''
        rSQL = "select companyno,scope from cnr_scope_iprange where %d between ip_bgv and ip_endv order by updtime desc" % (ipnum)
        print rSQL
        rst1 = ora.execall(rSQL)
        if rst1 is not None and len(rst1) > 0:
            for aw1 in rst1:
                scope = aw1[1]
                break

        if len(scope) > 0:
            ma = re.match(r"^(.+)B[0-6|8-9][0-9]$", scope)
            if ma is not None:
                scope = ma.group(1)
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
        rSQL = "select companyno,scope from cnr_scope_iprange where regexp_like(scope,'^%sB[0-6|8-9][0-9]$') order by companyno,scope" % (scope)
        print rSQL
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

                            if line.find("reserved") >= 0 or line.find("deactivated") >= 0 or line.find("leased") >= 0: # 保留, 關閉, 發放
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


def registip3(cnr_shell, mac, ip, ora, sid):
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

        cnr_shell.sendline('lease ' + ip + ' get-scope-name')
        cnr_shell.expect('nrcmd>', timeout=60)
	scope = cnr_shell.before.splitlines()[3]
	print scope
	
	if scope is None or len(scope) <= 0:
            print 'registip3() - ERROR: cannot find scope'
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR','cannot find scopename',sid)
            ora.execone(updateSql)
            ora.commit()
            return -1
	if len(scope) > 0:
	   #ma = re.match(r"^([^P]+)P\d\d$",scopename)
	   ma = re.match(r"^(.+)P\d\d$",scope)
	   if ma is not None:
	       scope =  ma.group(1)
	   else:
	       ma = re.match(r"^(.+)B[0-6|8-9][0-9]$", scope)
	       if ma is not None:
	          scope = ma.group(1)
               else:
	          scope = ''

	print scope
	cnr_shell.sendline('force-lock')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before

        cnr_shell.sendline('session set default-format=script')
        cnr_shell.expect('nrcmd>', timeout=60)
        print cnr_shell.before

        newip = newscope = ''
        rSQL = "select companyno,scope from cnr_scope_iprange where regexp_like(scope,'^%sB[0-6|8-9][0-9]$') order by companyno,scope" % (scope)
        print rSQL
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

                            if line.find("reserved") >= 0 or line.find("deactivated") >= 0 or line.find("leased") >= 0: # 保留, 關閉, 發放
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
            print 'registip3() - ERROR: cannot find newIP/newScope'
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

	    _get_str = ''
	    cnr_shell.sendline('client ' + mac )
	    cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before
            _get_str = cnr_shell.before 

            if _get_str.find("302 Not Found") >=0:
	       cnr_shell.sendline('client ' + mac + ' create selection-criteria=Scope-PUB')
               cnr_shell.expect('nrcmd>', timeout=60)
               print cnr_shell.before
            else:
               cnr_shell.sendline('client ' + mac + ' set selection-criteria=Scope-PUB')
               cnr_shell.expect('nrcmd>', timeout=60)
               print cnr_shell.before

            cnr_shell.sendline('save')
            cnr_shell.expect('nrcmd>', timeout=60)
	    print cnr_shell.before
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s',policy='%s' WHERE sid = %d" % ('OK',_result_str,newip,sid)
            print 'registip3() - %s %s %s => OK' % (mac,ip,newip)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'registip3() - %s %s %s => ERROR' % (mac,ip,newip)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1	

		
    except Exception, e:
	print 'registip3() - ERROR: '+str(e)
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

def deregistip3(cnr_shell, mac, ip, ora, sid):
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
	    
            _get_str = ''
            cnr_shell.sendline('client ' + mac )
            cnr_shell.expect('nrcmd>', timeout=60)
            print cnr_shell.before
            _get_str = cnr_shell.before
            
            if _get_str.find("302 Not Found") >=0:
	      _result_str = '100Ok'
            else:
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

def fixip_to_public(cnr_shell, mac, ora, sid): 
    try:
        #mac = mac_fmt_conv(mac)
        #print mac
        
        if mac == '':
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
        
        if _get_str.find("302 Not Found") >=0:
           cnr_shell.sendline('client ' + mac + ' create selection-criteria=Scope-PUB')
           cnr_shell.expect('nrcmd>', timeout=60)
	   print cnr_shell.before
        else:
       	   cnr_shell.sendline('client ' + mac + ' set selection-criteria=Scope-PUB')
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
        
        
def fixip_to_private(cnr_shell, mac, ora, sid): 
    try:
        #mac = mac_fmt_conv(mac)
        #print mac
        
        if mac == '':
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
	
	if _get_str.find("302 Not Found") >=0:
	    _result_str = '100Ok'
	else:
            cnr_shell.sendline('client ' + mac + ' delete')
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
            print 'fixip_private() - %s => OK' % (mac)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'fixip_private() - %s => ERROR' % (mac)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1
        
    except Exception, e:
        print 'fixip_private() - ERROR: '+str(e)
        return -2

def add_ddosflag(cnr_shell, mac, ora, sid):
    try:
        if mac == '':
            print 'add_ddosflag() - ERROR: cmmac is Null'
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

        if _get_str.find("302 Not Found") >=0:
           cnr_shell.sendline('client ' + mac + ' create selection-criteria=Scope-ddos')
           cnr_shell.expect('nrcmd>', timeout=60)
           print cnr_shell.before
        else:
           cnr_shell.sendline('client ' + mac + ' set selection-criteria=Scope-ddos')
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
            print 'add_ddosflag() - %s => OK' % (mac)
	else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
            print 'add_ddosflag() - %s => ERROR' % (mac)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1

    except Exception, e:
        print 'add_ddosflag() - ERROR: '+str(e)
        return -2


def del_ddosflag(cnr_shell, mac, ora, sid):
    try:
        if mac == '':
            print 'del_ddosflag() - ERROR: cmmac is Null'
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

        if _get_str.find("302 Not Found") >=0:
            _result_str = '100Ok'
        else:
            cnr_shell.sendline('client ' + mac + ' delete')
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
            print 'del_ddosflag() - %s => OK' % (mac)
        else:
            updateSql = "UPDATE cnr_queue SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % ('ERROR',_result_str,sid)
	    print 'del_ddosflag() - %s => ERROR' % (mac)
        print updateSql
        ora.execone(updateSql)
        ora.commit()
        return 1

    except Exception, e:
        print 'del_ddosflag() - ERROR: '+str(e)
        return -2
        
def main(cnr):
    for qq in range(4):
        oracon = ORA('nms@cnis')
        if oracon.db is not None:
            break
        else:
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print '['+nowdate+'] Error: Unable to connect to DB [CNIS][RETRY]'
            sys.stdout.flush()
            time.sleep(60)
    if oracon.db is None:
        sys.exit(0)
    print cnr
    so = cnrid = cnrid2 = cnrip = cnrip2 = uid = pwd = None
    SQL = "select '220' companyno,'NTP_CNR1_001' cnr_id,'' cnr_id2,'10.222.24.101' ip,ip2,apiuser,apipwd from cnr where stopyn='N' and rownum =1" 
    print SQL
    try:
        rst = oracon.execall(SQL)
        if rst is not None and len(rst) > 0:
            for aw in rst:
                so = aw[0]
                cnrid = aw[1]
                cnrid2 = aw[2]
                cnrip = aw[3]
                cnrip2 = aw[4]
                uid = aw[5]
                pwd = aw[6]
                break
    except Exception, msg:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+'] Except-01: '+str(msg)

    if so is None or cnrip is None or uid is None or pwd is None:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+'] Error: CNR is empty [CNIS]'
        if oracon.db is not None:
            oracon.se_close()
        sys.exit(0)

    print 'MAIN',so,cnrid,cnrid2,cnrip,cnrip2,uid,pwd

    for qq in range(4):
        if qq >= 2 and cnrip2 is not None and len(cnrip2) > 0:
            host = cnrip2
        else:
            host = cnrip
        try:
            cnr_shell_main = conn(host, uid, pwd)
            break
        except Exception, msg:
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print '['+nowdate+'] Error: Unable to connect to server [CNR][RETRY] '+str(msg)
            sys.stdout.flush()
            time.sleep(60)
    if cnr_shell_main is None:
        sys.exit(0)

    if so in ['810','820'] or cnrid in ['KS_CNR1_001','PN_CNR1_001','KS-CNR-01','PN-CNR-01'] or cnrid2 in ['KS_CNR1_001','PN_CNR1_001','KS-CNR-01','PN-CNR-01']:
        querySQL = "select sid,command,cmmac,policy,ip,cpemac,companyno,subsid from ( \
  select sid,command,cmmac,policy,ip,cpemac,companyno,subsid, \
    case \
      when command='active' and policy like '%%TV%%' then 1 \
      when command='active' and policy like '%%STB%%' then 2 \
      when command in ('querymac','querybw') then 3 else 1 \
    end seq \
  from cnr_queue where (companyno in ('810','820') or cnr_id in ('KS-CNR-01','PN-CNR-01','KS_CNR1_001','PN_CNR1_001')) and status='INIT' \
  and command in ('active','modify','delete','addfixip','addfixip2','delfixip','deactiveip','activeip','querymac','querybw') and sysdate >= book_date order by seq,book_date,sid \
) where rownum <= 30"
    elif so == '240' or cnrid in ['DA_CNR1_001','WS_CNR1_001','DW-CNR-01','DW-CNR-02'] or cnrid2 in ['DA_CNR1_001','WS_CNR1_001','DW-CNR-01','DW-CNR-02']:
        querySQL = "select sid,command,cmmac,policy,ip,cpemac,companyno,subsid from ( \
  select sid,command,cmmac,policy,ip,cpemac,companyno,subsid, \
    case \
      when command='active' and policy like '%%TV%%' then 1 \
      when command='active' and policy like '%%STB%%' then 2 \
      when command in ('querymac','querybw') then 3 else 1 \
    end seq \
  from cnr_queue where cnr_id in ('%s','%s') and status='INIT' \
  and command in ('active','modify','delete','addfixip','addfixip2','delfixip','deactiveip','activeip','querymac','querybw') and sysdate >= book_date order by seq,book_date,sid \
) where rownum <= 30" % (cnrid,cnrid2)
    elif so == '220':
    	querySQL = "select sid,command,cmmac,policy,ip,cpemac,companyno,subsid from ( \
  select sid,command,cmmac,policy,ip,cpemac,companyno,subsid, \
    case \
      when command='active' and policy like '%%TV%%' then 1 \
      when command='active' and policy like '%%STB%%' then 2 \
      when command in ('querymac','querybw') then 3 else 1 \
    end seq \
  from cnr_queue where (companyno='%s' or cnr_id in ('%s','%s')) and status='INIT' \
  and command in ('addfixip3') and sysdate >= book_date order by seq,book_date,sid \
) where rownum <= 30" % (so,cnrid,cnrid2)
    else:
        querySQL = "select sid,command,cmmac,policy,ip,cpemac,companyno,subsid from ( \
  select sid,command,cmmac,policy,ip,cpemac,companyno,subsid, \
    case \
      when command='active' and policy like '%%TV%%' then 1 \
      when command='active' and policy like '%%STB%%' then 2 \
      when command in ('querymac','querybw') then 3 else 1 \
    end seq \
  from cnr_queue where (companyno='%s' or cnr_id in ('%s','%s')) and status='INIT' \
  and command in ('active','modify','delete','addfixip','addfixip2','delfixip','deactiveip','activeip','querymac','querybw','ddos') and sysdate >= book_date order by seq,book_date,sid \
) where rownum <= 30" % (so,cnrid,cnrid2)
    print querySQL
    sys.stdout.flush()

    cnr_loop = cnr_loop_old = 0
    ipusage_flag = []
    while 1:
        try:
            oracon.execone('select sysdate from dual')
        except Exception, msg:
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print '['+nowdate+'] Error: Lost connection to DB [CNIS][RETRY] '+str(msg)

            for qq in range(4):
                oracon = ORA('nms@cnis')
                if oracon.db is not None:
                    break
                else:
                    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                    print '['+nowdate+'] Error: Unable to connect to DB [CNIS][RETRY]'
                    sys.stdout.flush()
                    time.sleep(60)
        if oracon.db is None:
            break

        try:
            cnr_shell_main.sendline('lease')
            cnr_shell_main.expect('nrcmd>', timeout=15)
            #print cnr_shell_main.before
        except Exception, msg:
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print '['+nowdate+'] Error: Lost connection to server [CNR][RETRY] '+str(msg)

            for qq in range(4):
                if qq >= 2 and cnrip2 is not None and len(cnrip2) > 0:
                    host = cnrip2
                else:
                    host = cnrip
                try:
                    cnr_shell_main = conn(host, uid, pwd)
                    break
                except Exception, msg:
                    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                    print '['+nowdate+'] Error: Unable to connect to server [CNR][RETRY] '+str(msg)
                    sys.stdout.flush()
                    time.sleep(60)
        if cnr_shell_main is None:
            break

        sys.stdout.flush()
        try:
            rst = oracon.execall(querySQL)
            if rst is not None and len(rst) > 0:
                for aw in rst:
                    try:
                        result = -1
                        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                        sid = int(aw[0])
                        cmd = aw[1]
                        cmmac = aw[2]
                        policy = aw[3]
                        ip = aw[4]
                        cpemac = aw[5]
                        so = aw[6]
                        if aw[7] is not None:
                            subsid = int(aw[7])
                        else:
                            subsid = ''
                        print '#'+str(cnr_loop),nowdate,'=> #'+str(sid),cmd,cmmac,policy,ip,cpemac,so,subsid
                        sys.stdout.flush()

                        if cmd == 'active': # 註冊方案
                            result = activate(cnr_shell_main, cmmac, policy, oracon, sid)
                        elif cmd == 'modify': # 修改方案
                            result = modify(cnr_shell_main, cmmac, policy, oracon, sid)
                        elif cmd == 'delete': # 刪除方案
                            result = delete(cnr_shell_main, cmmac, oracon, sid)
                        elif cmd == 'addfixip' or cmd == 'addfixip2' or cmd == 'addfixip3' or cmd == 'delfixip2' or cmd == 'delfixip' or cmd=='deactiveip' or cmd=='activeip': # 設定及解除固定IP
                            if cnr_shell_main is not None:
                                try:
                                    cnr_shell_main.sendline('exit')
                                    cnr_shell_main.close()
                                except:
                                    pass
                            cnr_shell_main = None
                            cnr_loop = cnr_loop_old = 0

                            for qq in range(4):
                                if qq >= 2 and cnrip2 is not None and len(cnrip2) > 0:
                                    host = cnrip2
                                else:
                                    host = cnrip
                                try:
                                    cnr_shell_main = conn(host, uid, pwd)
                                    break
                                except Exception, msg:
                                    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                                    print '['+nowdate+'] Error: Unable to connect to server [CNR][RETRY] '+str(msg)
                                    sys.stdout.flush()
                                    time.sleep(60)

                            if cnr_shell_main is not None:
                                if cmd == 'addfixip':
                                    result = registip(cnr_shell_main, cpemac, ip, oracon, sid)
                                elif cmd == 'addfixip2':
                                    result = registip2(cnr_shell_main, cpemac, ip, oracon, sid)
				elif cmd == 'addfixip3':
                                    result = registip3(cnr_shell_main, cpemac, ip, oracon, sid)
                                elif cmd == 'delfixip':
                                    result = deregistip(cnr_shell_main, ip, oracon, sid)
				elif cmd == 'delfixip2':
				    result = deregistip(cnr_shell_main, ip, oracon, sid)
                                elif cmd == 'deactiveip':
                                    result = ipdeact(cnr_shell_main, ip, oracon, sid)
                                elif cmd == 'activeip':
                                    result = ipact(cnr_shell_main, ip, oracon, sid)

                                try:
                                    cnr_shell_main.sendline('exit')
                                    cnr_shell_main.close()
                                except:
                                    pass
                                cnr_shell_main = None

                                for qq in range(4):
                                    if qq >= 2 and cnrip2 is not None and len(cnrip2) > 0:
                                        host = cnrip2
                                    else:
                                        host = cnrip
                                    try:
                                        cnr_shell_main = conn(host, uid, pwd)
                                        break
                                    except Exception, msg:
                                        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                                        print '['+nowdate+'] Error: Unable to connect to server [CNR][RETRY] '+str(msg)
                                        sys.stdout.flush()
                                        time.sleep(60)
                        
                        elif cmd == 'querymac': # 查詢CMIP/CPEIP的CMMAC/CPEMAC
                            result = querymac_by_ip(cnr_shell_main, ip, oracon, sid)
                        elif cmd == 'querybw': # 查詢CMMAC的PROFILE
                            result = queryprofile_by_mac(cnr_shell_main, cmmac, oracon, sid)
                        elif cmd == 'fixpublic':
                            result = fixip_to_public(cnr_shell_main, cpemac, oracon, sid)
                        elif cmd == 'fixprivate':
                            result = fixip_to_private(cnr_shell_main, cpemac, oracon, sid)
			elif cmd == 'ddos':
			    result = add_ddosflag(cnr_shell_main, cpemac, oracon, sid)
			elif cmd == 'delddos':
			    result = del_ddosflag(cnr_shell_main, cpemac, oracon, sid)
                        else:
                            print "Unknown command: "+cmd
                        sys.stdout.flush()

                        '''
                        if result < 0:
                            print "Failed to execute command: "+cmd
                            try:
                                if cnr_shell_main is not None:
                                    cnr_shell_main.sendline('exit')
                                    cnr_shell_main.close()
                            except Exception, detail:
                                nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                                print '['+nowdate+'] Except-02: '+str(msg)
                            sys.stdout.flush()
                            cnr_shell_main = None
                            break
                        '''

                    except Exception, msg:
                        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                        print '['+nowdate+'] Except-03: '+str(msg)

                    cnr_loop = cnr_loop+1
            else:
                # IP使用率 - 每日執行乙次
                today = time.strftime("%Y%m%d", time.localtime())
                if today not in ipusage_flag:
                    result = get_ipusage(cnr_shell_main, oracon)
                    if result > 0:
                        ipusage_flag.append(today)

            print '.',
        except Exception, msg:
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print '['+nowdate+'] Except-04: '+str(msg)

        cnr_loop = cnr_loop+1
        sys.stdout.flush()
        time.sleep(10)

        if (cnr_loop - cnr_loop_old) >= 50:
            if cnr_shell_main is not None:
                nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                print '['+nowdate+'] CNR execute limit reached [RECONN]',cnr_loop,cnr_loop_old
                sys.stdout.flush()
                try:
                    cnr_shell_main.sendline('exit')
                    cnr_shell_main.close()
                except:
                    pass
            cnr_shell_main = None
            cnr_loop_old = cnr_loop

    try:
        if cnr_shell_main is not None:
            cnr_shell_main.sendline('exit')
            cnr_shell_main.close()
            cnr_shell_main = None
    except:
        pass
    try:
        if oracon.db is not None:
            oracon.se_close()
            oracon = None
    except:
        pass

try:
    print cnr
    main(cnr)
except KeyboardInterrupt, e: # Ctrl-C
    raise e
except SystemExit, e: # sys.exit()
    raise e
except Exception, e:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Except-05: '+str(e)
    sys.exit()
