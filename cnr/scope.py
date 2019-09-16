#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
from oraclass import ORA
import pexpect

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

def conn(host, uid, pwd):
    try:
        nrcmd = "/opt/nwreg2/usrbin/nrcmd -C " + host + " -N " + uid + " -P " + pwd
        print nrcmd
        cnr_shell = pexpect.spawn(nrcmd)
        cnr_shell.expect('nrcmd>')
        return cnr_shell
    except Exception, detail:
        print 'conn Exception: %s' % (detail)
        return None


def ScopeList(cnr_shell, cnr_host, companyno, cnr_id, oracon):
    try:
        cnr_shell.sendline("force-lock")
        cnr_shell.expect('nrcmd>', timeout=None)
        #print cnr_shell.before

        cnr_shell.sendline("scope list")
        cnr_shell.expect('nrcmd>', timeout=None)
        #print cnr_shell.before

        result = cnr_shell.before
        arr_res = result.splitlines()
	print arr_res
        code_no, code_name = arr_res[2].split(' ',1)
        print 'codeno:',code_no, code_name

        scopename = None
        addr = None
        mask = None
        if code_no == '100' or code_no == '101':
            for element in arr_res[3:] :
		list_scopename = re.split('[\:]', element)
                print 'scopename:',list_scopename
                if len(list_scopename) == 2:
                    scopename = list_scopename[0]
                    continue
                else:
                    list_properties = re.split('[\=]', element)
                    if ('addr' == list_properties[0].strip()):
                        addr = list_properties[1].strip()
                    elif ('mask' == list_properties[0].strip()):
                        mask = list_properties[1].strip()

                    if (scopename is not None) and (addr is not None) and (mask is not None):
                        cidr = gen_cidr(mask)
                        hosts = get_hosts(cidr)
                        ipnum_start = ip2num(addr)+1
                        ipnum_end = ipnum_start + hosts
                        upd2oradb(companyno, scopename, cnr_host, addr, hosts, cidr, ipnum_start, ipnum_end, cnr_id, oracon)
                        scopename = None
                        addr = None
                        mask = None

            return cnr_shell
        elif code_no.isalnum():
            return cnr_shell,code_name
        else:
            return cnr_shell,-1
    except Exception, detail:
        print 'ScopeList Exception: %s' % (detail)
        return cnr_shell,-1


oracnis = ORA('nms@cnis')
if not oracnis.db:
    print 'Error: Unable to connect to server [CNIS]'
    sys.exit(0)

cnr_shell = None
cnr_shell = conn('10.222.40.101', 'provgw', 'pv#1176')

cnr_shell = ScopeList(cnr_shell, '10.222.40.101', '240', 'DA_CNR1_001', oracnis)

