#!/usr/bin/env python
# -*- coding: Big5 -*-
import sys,datetime,time
import cossdb,pymssql
from oraclass import ORA

#dbhost = 'TFMCossMS_CP950'
#dbname = 'cossdb'

if len(sys.argv)<2:
    sosql = "'101','103','104','300','701'"
else:
    sosql = "'%s'" % (sys.argv[1])

#con = pymssql.connect(host=dbhost,user='proguser',password='cossuser',database=dbname)
con = pymssql.connect(host='TFMCossMS_CP950',user=cossdb.account,password=cossdb.passwd,database='cossdb')
cur = con.cursor()

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print '----------'
print nowdate
print '----------'

loopsql = "select a.companyno,a.custid,a.subsid,a.singlesn from ms0200 a with (nolock),ms0210 b with (nolock) where a.companyno=b.companyno and a.subsid=b.subsid and a.companyno in (%s) and a.servicename in ('3 DSTB') and substring(a.custstatus,1,1) in ('0','1','8','9','7','A') and b.chargename like '%%聯網電視%%' and (b.expiredate is null or b.expiredate>getdate())" % (sosql)
cur.execute(loopsql)
curarr = cur.fetchall()
xlen = len(curarr)
mloop = xlen
print "Total %d subscribers(MS0210)" % (xlen)
sys.stdout.flush()

total_ms0210_so = {}
total_ms0210_cid = {}
total_ms0210_sid = {}
total_ms0210_stb = {}
i = 0
while i<xlen:
    companyno = curarr[i][0]
    custid = int(curarr[i][1])
    subsid = int(curarr[i][2])
    stbno = curarr[i][3]
    total_ms0210_so[i] = companyno
    total_ms0210_cid[i] = custid
    total_ms0210_sid[i] = subsid
    total_ms0210_stb[i] = stbno
    i = i+1

mloop = i
loopsql = "select a.companyno,a.custid,a.subsid,a.singlesn from ms0200 a with (nolock),ms0301 b with (nolock) where a.companyno=b.companyno and a.subsid=b.subsid and a.companyno in (%s) and a.servicename in ('3 DSTB') and substring(a.custstatus,1,1) in ('0','1','8','9','7','A') and b.chargename like '%%聯網電視%%' and substring(b.sheetstatus, 1, 1) not in ('4', 'A')" % (sosql)
cur.execute(loopsql)
curarr = cur.fetchall()
xlen = len(curarr)
print "Total %d subscribers(ms0301)" % (xlen)
sys.stdout.flush()
i = 0
while i<xlen:
    companyno = curarr[i][0]
    custid = int(curarr[i][1])
    subsid = int(curarr[i][2])
    stbno = curarr[i][3]
    total_ms0210_so[mloop] = companyno
    total_ms0210_cid[mloop] = custid
    total_ms0210_sid[mloop] = subsid
    total_ms0210_stb[mloop] = stbno
    i = i+1
    mloop = mloop+1

loopsql = "select a.companyno,a.custid,a.subsid,max(a.singlesn) singlesn from ms0200 a with (nolock),ms3200 b with (nolock) where a.companyno=b.companyno and a.subsid=b.subsid and a.companyno in (%s) and a.servicename in ('3 DSTB') and substring(a.custstatus,1,1) in ('0','1','8','9','7','A') and b.chargename like '%%聯網電視%%' and recvyn='Y' and recvdate>=getdate()-1 and substring(realrecv,1,1)<>'Y' group by a.companyno,a.custid,a.subsid" % (sosql)
cur.execute(loopsql)
curarr = cur.fetchall()
xlen = len(curarr)
print "Total %d subscribers(ms3200)" % (xlen)
i = 0
while i<xlen:
    companyno = curarr[i][0]
    custid = int(curarr[i][1])
    subsid = int(curarr[i][2])
    stbno = curarr[i][3]
    total_ms0210_so[mloop] = companyno
    total_ms0210_cid[mloop] = custid
    total_ms0210_sid[mloop] = subsid
    total_ms0210_stb[mloop] = stbno
    i = i+1
    mloop = mloop+1

ora_coss = ORA('coss@CNIS')
ora_cmms = ORA('cmms@TFM_NMSDB')

loopsql = "select so,subsid,flag from smod_info"
rst = ora_coss.execall(loopsql)
xlen = 0
if rst is not None:
    xlen = len(rst)
print "%s Total %d smod_info records" % (sosql, xlen)
sys.stdout.flush()

smod_sid = {}
smod_flag = {}
i = 0
while i<xlen:
    so = rst[i][0]
    subsid = int(rst[i][1])
    cflag = rst[i][2]
    key = "%s-%d" % (so, subsid)
    smod_sid[key] = i
    smod_flag[key] = cflag
    i = i+1

i = 0
while i<mloop:
    cid = total_ms0210_cid[i]
    sid = total_ms0210_sid[i]
    so = total_ms0210_so[i]
    stbno = total_ms0210_stb[i]
    try:
        key = "%s-%d" % (so, sid)
        xsid = smod_sid[key]
        xflag = smod_flag[key]
    except:
        pass
        SQL = "insert into smod_info(so,custid,subsid,stbno) values('%s','%d','%d','%s')" % (so, cid, sid, stbno)
        print SQL
        ora_coss.execone(SQL)
        ora_coss.commit()
    i = i+1

header_arr = {}
header_arr['101'] = 'YJL'
header_arr['103'] = 'GVC'
header_arr['104'] = 'MCT'
header_arr['300'] = 'UCT'
header_arr['701'] = 'PHC'

#loopsql = "select a.so,a.custid,a.subsid,b.stb_cm_mac from smod_info a, v_ivrmi0130@twm_nwis b where a.stbno=b.singlesn and b.mtkind='STB' and a.status='INIT'"
#rst = ora_coss.execall(loopsql)
xlen = 0
#if rst is not None:
#    xlen = len(rst)
#print "%s Total %d smod_info INIT records" % (sosql, xlen)
#sys.stdout.flush()

i = 0
while i<xlen:
    so = rst[i][0]
    custid = int(rst[i][1])
    subsid = int(rst[i][2])
    cmc_mac = rst[i][3]
    if cmc_mac is None:
        SQL = "select singlesn from ms0200 with (nolock) where companyno='%s' and custid=%d and servicename='9 CMC' and substring(custstatus,1,1) in ('0','1','8','9','7','A') and singlesn<>'' and singlesn is not null" % (so, custid)
        cur.execute(SQL)
        curarr = cur.fetchall()
        if curarr is not None:
            try:
                cmc_mac = curarr[0][0]
            except:
                cmc_mac = None
    if cmc_mac is not None:
        SQL = "update smod_info set cmc_mac='%s',status='CHECK' where so='%s' and subsid='%d'" % (cmc_mac, so, subsid)
        ora_coss.execone(SQL)
        header = header_arr[so]
        cnrid = "%s-DHCP-01" % (header)
        policy = "%sTV6M" % (header)
        SQL = "insert into dhcp_queue(dhcp_id,cmd,mac,bw,account) values('%s','MOD_BW','%s','%s','AUTO_CONNTV')" % (cnrid, cmc_mac, policy)
        print SQL
        ora_cmms.execone(SQL)
        sys.stdout.flush()
    if i%20==0:
        ora_coss.commit()
        ora_cmms.commit()
    i = i+1
ora_coss.se_close()
ora_cmms.se_close()
con.close()
