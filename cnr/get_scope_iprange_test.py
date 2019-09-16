#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
from oraclass import ORA
import pexpect

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

# PORT: 2785, 2786

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
        code_no, code_name = arr_res[2].split(' ',1)
        print code_no, code_name

        scopename = None
        addr = None
        mask = None
        if code_no == '100':
            for element in arr_res[3:] :
                list_scopename = re.split('[\:]', element)
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

def upd2oradb(companyno, scopename, cnr_host, addr, hosts, cidr, ipnum_start, ipnum_end, cnr_id, oracon) :
    try:
        ins_cnr_scope_iprange = "insert into cnr_scope_iprange (companyno, scope, cnrip, subnet, hosts, prefix, ip_bgv, ip_endv, cnr_id, updtime, lastest) values ('" + str(companyno) + "','" + scopename + "','" + cnr_host + "','" + addr + "','" + str(hosts) + "','" + str(cidr) + "','" + str(ipnum_start) + "','" + str(ipnum_end) + "','" + cnr_id + "',sysdate,'1')"
        print ins_cnr_scope_iprange
        oracon.execone(ins_cnr_scope_iprange)
    except Exception, detail:
        upd_cnr_scope_iprange = "update cnr_scope_iprange set companyno='" + str(companyno) + "', scope='" + scopename + "', cnrip='" + cnr_host + "', subnet='" + addr + "', hosts='" + str(hosts) + "', prefix='" + str(cidr) + "', ip_bgv='" + str(ipnum_start) + "', ip_endv='" + str(ipnum_end) + "', cnr_id='" + cnr_id + "', updtime=sysdate, lastest='1' where scope='" + scopename + "'"
        print upd_cnr_scope_iprange
        oracon.execone(upd_cnr_scope_iprange)
    finally:
        oracon.commit()
        return

def ip2num(addr):
    try:
        inQuads = addr.split(".")
        idx = -1
        num = 0
        for q in inQuads:
            idx += 1
            num += int(int(q) * pow(256, 3-idx))
        return num
    except Exception, detail:
        print 'ip2num Exception: %s' % (detail)
        return -1

def get_hosts(mask):
    try:
        hosts = pow(2, 32-int(mask)) - 2
        return hosts
    except Exception, detail:
        print 'get_hosts Exception: %s' % (detail)
        return -1

def gen_cidr(mask):
    try:
        import math
        cidr = None
        list_mask = mask.split('.',3)
        for val_mask in list(list_mask):
            if val_mask != '255': #(256 - int(val_mask)) > 1:
                #print list_mask.index(val_mask), val_mask
                cidr = (8 * list_mask.index(val_mask)) + (8 - int(math.log(256-int(val_mask), 2)))
            if cidr is not None:
                return cidr
    except Exception, detail:
        print 'gen_cidr Exception: %s' % (detail)
        return -1

if len(sys.argv) != 2:
    print 'usage:',sys.argv[0],'[CompanyNo | KBRO | TFM | ALL]'
    sys.exit(0)

qrysql = "select ip,apiuser,apipwd,companyno,cnr_id from cnr where cnr_id='UC_CPNR_001' and ip is not null"
so = sys.argv[1].upper()
if so == 'ALL':
    qrysql = qrysql + " and companyno not in ('820')"
elif so == 'KBRO':
    qrysql = qrysql + " and companyno not in ('101','103','104','300','701','820')"
elif so == 'TFM':
    qrysql = qrysql + " and companyno in ('101','103','104','300','701')"
elif len(so) == 3:
  qrysql = qrysql + " and companyno='%s'" % (so)
else:
    print 'usage:',sys.argv[0],'[CompanyNo | KBRO | TFM | ALL]'
    sys.exit(0)

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] START\n" % (nowdate)

oracnis = ORA('nms@cnis')
if not oracnis.db:
    print 'Error: Unable to connect to server [CNIS]'
    sys.exit(0)

qrysql = qrysql + " order by 4 asc"
print qrysql
rs_cnr_info = oracnis.execall(qrysql)
for row_cnr_info in rs_cnr_info:
    try:
        cnr_host  = row_cnr_info[0]
        cnr_uid   = row_cnr_info[1]
        cnr_pwd   = row_cnr_info[2]
        companyno = row_cnr_info[3]
        cnr_id    = row_cnr_info[4]

        cnr_shell = None
        cnr_shell = conn(cnr_host, cnr_uid, cnr_pwd)
        if cnr_shell is None:
            print 'Error: Unable to connect to server [%s]' % (cnr_id)
            continue

        if companyno in ['810','820']:
            updsql = "update cnr_scope_iprange set lastest='0',cmts_id=null,bundle_name=null where lastest != '2' and companyno in ('810','820')"
        else:
            updsql = "update cnr_scope_iprange set lastest='0',cmts_id=null,bundle_name=null where lastest != '2' and cnr_id='" + cnr_id + "' and companyno='" + companyno + "'"
        print updsql
        oracnis.execone(updsql)
        oracnis.commit()

        cnr_shell = ScopeList(cnr_shell, cnr_host, companyno, cnr_id, oracnis)
        if cnr_shell is not None:
            cnr_shell.sendline('exit')
            cnr_shell.close()
            cnr_shell = None

        if companyno in ['810','820']:
            updsql = "delete from cnr_scope_iprange where lastest='0' and companyno in ('810','820')"
        else:
            updsql = "delete from cnr_scope_iprange where lastest='0' and cnr_id='" + cnr_id + "' and companyno='" + companyno + "'"
        print updsql
        oracnis.execone(updsql)
        oracnis.commit()

        # 對應Scope與CMTS_ID及Bundle
        if companyno in ['810','820']:
            qrysql2 = "select companyno,cmts_id,scope from cmts where companyno in ('810','820') and stopyn='N' and scope is not null order by scope asc"
        else:
            qrysql2 = "select companyno,cmts_id,scope from cmts where companyno='%s' and stopyn='N' and scope is not null order by scope asc" % (companyno)
        print qrysql2
        rs1 = oracnis.execall(qrysql2)
        for row1 in rs1:
            cmts_id = row1[1]
            cnr_scope = row1[2]
            bundle = 1

            scope_arr = cnr_scope.strip().split(',')
            for bb in scope_arr:
                if companyno in ['810','820']:
                    updsql2 = "update cnr_scope_iprange set cmts_id='%s',bundle_name='%d' where companyno in ('810','820') and scope like '%s%%'" % (cmts_id, bundle, bb)
                else:
                    updsql2 = "update cnr_scope_iprange set cmts_id='%s',bundle_name='%d' where companyno='%s' and scope like '%s%%'" % (cmts_id, bundle, companyno, bb)
                print updsql2
                oracnis.execone(updsql2)
                oracnis.commit()
                bundle = bundle + 1

    except Exception, detail:
        print 'Exception: %s' % (detail)

if oracnis is not None:
    oracnis.se_close()

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] END\n" % (nowdate)

sys.exit(0)
