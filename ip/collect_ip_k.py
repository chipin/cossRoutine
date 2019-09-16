#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
from pysnmpclass import snmpclass
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv)!=2:
    print 'Error: Argument error'
    sys.exit(0)

so = sys.argv[1]

if so.upper() != 'TFM' and so.upper() != 'KBRO1' and so.upper() != 'KBRO2':
    print 'Error: Argument error'
    sys.exit(0)

agent = snmpclass(version='v2c',ptimeout=1,pretries=3,debug=0)

def query_status(yneid, yip, ymodel, ycomm, yoid, ytype):
    global snmp_oid
    print yoid
    print yneid, yip, ymodel, ycomm, ytype

    if ymodel.find('QAM') >= 0:
        agentx = snmpclass(version='v1',ptimeout=1,pretries=3,debug=0)
        print 'v1'
    else:
        agentx = snmpclass(version='v2c',ptimeout=1,pretries=3,debug=0)
        print 'v2c'

    yresult = {}

    try:
        for oname in yoid:
            try:
		if ytype == 'CGNAT' and oname in ['ifSpeed']:
		   tmp_mib = '.1.3.6.1.2.1.31.1.1.1.15'
		elif ytype == 'CGNAT' and oname in ['ifAlias']:
		   tmp_mib = '.1.3.6.1.4.1.3375.2.100.1'
		else:
               	   tmp_mib = snmp_oid['%s-X' % (oname)]
            except:
                try:
                    tmp_mib = snmp_oid['%s-%s' % (oname, ymodel)]
                except:
                    continue
            rets = agentx.snmpwalk([yip, '-c', ycomm, tmp_mib])
            i = 0
            lens = len(rets)
            while i<lens:
		if oname in ['ifAlias']:
		    zid = rets[i][0].replace(tmp_mib+'.','')
		    zid = zid.replace('.0','')
		else:
                    zid = rets[i][0].replace(tmp_mib+'.','')
                try:
                    zvalue = rets[i][1].strip().replace('\'','')
                except:
                    zvalue = rets[i][1]

                if oname in ['ifIndex']:
                    yresult['%s-%s-%d' % (yneid, oname, i)] = zid
                else:
                    yresult['%s-%s-%s' % (yneid, oname, zid)] = zvalue

                i = i+1
                #print yneid,oname,zid,zvalue
            print "%s (%s %s) -> %d" % (yneid, oname, tmp_mib, lens)

            if oname in ['ifIndex']:
                yresult['%s-%s-LEN' % (yneid, oname)] = lens
            sys.stdout.flush()
    except Exception, msg:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+']:'+str(msg)

    return yresult


snmp_oid = {}
oid_name = []

ora = ORA('nms@cnis')

if not ora.db:
    sys.exit(0)

# Get SNMP OID
SQL = "select name,upper(model) model,oid \
       from snmp_mib \
       where name in ('SysDescr','ifIndex','ifDescr','ifAdminStatus','ifOperStatus','ifSpeed','ifAlias','ifHighSpeed','ifIpIndex')"
rst = ora.execall(SQL)
if rst is not None and len(rst)>0:
    for aw in rst:
        try:
            xname = aw[0]
            xmodel = aw[1]
            xoid = aw[2]
            if xmodel is None:
                xmodel = 'X'
            snmp_oid[xname+'-'+xmodel] = xoid

            if xname in ['SysDescr']:
                continue
            if xname not in oid_name:
                oid_name.append(xname)
        except Exception, msg:
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print '['+nowdate+']:'+str(msg)
else:
    print "Error: SNMP_MIB is empty"
    if ora.db:
        ora.se_close()
    sys.exit(0)

ne_so={}
ne_id={}
ne_ip={}
ne_comm={}
ne_mflag={}
ne_model={}
ne_type={}
ne_cnt = 0

if so.upper() == 'TFM':
    sosql = "a.companyno in ('101','103','104','300','701','500')"
elif so.upper() == 'KBRO1':
    sosql = "a.companyno in ('240')"
else:
    sosql = "a.companyno in ('310','330','410','420','610','810','820')"

qrysql = "select a.companyno,a.ne_id,a.ip,a.snmp_ro,a.mflag,b.maker||' '||b.model model, a.type \
          from ip_ne a \
          inner join sys_object b on b.ne_id=substr(a.ne_id,-8,4) and b.stopyn='N' \
          where " + sosql + " and a.ip is not NULL and a.snmp_ro is not NULL and a.stopyn='N' and a.mflag > 0 and a.ne_id='WS_ICR1_001' \
          order by a.companyno,a.ne_id asc"
print qrysql
rs1 = ora.execall(qrysql)
if rs1 is not None and len(rs1)>0:
    for aw in rs1:
        ne_so[ne_cnt] = aw[0]
        ne_id[ne_cnt] = aw[1]
        ne_ip[ne_cnt] = aw[2]
        ne_comm[ne_cnt] = aw[3]
        ne_mflag[ne_cnt] = aw[4]
        ne_model[ne_cnt] = aw[5]
	ne_type[ne_cnt]  = aw[6]
        ne_cnt = ne_cnt+1

ne_idx = 0
while ne_idx<ne_cnt:
    try:
        xso = ne_so[ne_idx]
        xneid = ne_id[ne_idx]
        xIP = ne_ip[ne_idx]
        xcomm = ne_comm[ne_idx]
        xmflag = ne_mflag[ne_idx]
        xmodel = ne_model[ne_idx]
	xtype  = ne_type[ne_idx]

        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+']', xso, xneid, xIP, xcomm, xmodel

        result = {}
        ipary = {}
        ifipindex = ''
        result = query_status(xneid, xIP, xmodel, xcomm, oid_name, xtype)
        #print 'result=',result
        
        ipary = result.keys()
        j = 0
        #原格式為neid-ifIpIndex-10.10.10.10 = index, 改為neid-ifIpIndex-index = 10.10.10.10
        while j<len(ipary):
          if ipary[j].find('ifIpIndex') > 0:
            ifipindex=result[ipary[j]]
            result['%s-ifIpIndex-%s' % (xneid,ifipindex)] = ipary[j].replace('-ifIpIndex-','').replace(xneid,'')
          j = j+1

        ifnum = 0
        try:
            if result['%s-ifIndex-LEN' % (xneid)] > 0:
                ifnum = result['%s-ifIndex-LEN' % (xneid)]
        except:
            pass

        i = 0
        while i<ifnum:
            xid = result[xneid+'-ifIndex-'+str(i)]
            xifip = ''
            try:
                xifalias = result[xneid+'-ifAlias-'+str(xid)].strip().replace('\'','')
            except:
                xifalias = ''

            try:
                if int(result[xneid+'-ifSpeed-'+str(xid)]) == 4294967295 and int(result[xneid+'-ifHighSpeed-'+str(xid)]) > 0:
                    result[xneid+'-ifSpeed-'+str(xid)] = int(result[xneid+'-ifHighSpeed-'+str(xid)]) * 1000000
            except:
                pass
                
            try:
              if result[xneid+'-ifIpIndex-'+str(xid)] is not None:
                xifip = result[xneid+'-ifIpIndex-'+str(xid)]
              else:
                xifip = ''
            except:
                pass

            SQL = "select ifindex from ip_ne_if where companyno='%s' and ne_id='%s' and ifindex=%d" % (xso, xneid, int(xid))
            rs2 = ora.execall(SQL)
            reclen = len(rs2)
	    print xso, xneid, int(xid), result[xneid+'-ifDescr-'+str(xid)], int(result[xneid+'-ifSpeed-'+str(xid)]), result[xneid+'-ifAdminStatus-'+str(xid)], result[xneid+'-ifOperStatus-'+str(xid)], xifalias, xifip
            if rs2 is not None and reclen>0:
                SQL = "update ip_ne_if set ifdescr='%s',ifadminstatus='%s',ifoperstatus='%s',ifspeed=%d,ifalias='%s',ifip='%s',synctime=sysdate where companyno='%s' and ne_id='%s' and ifindex=%d" % (result[xneid+'-ifDescr-'+str(xid)], result[xneid+'-ifAdminStatus-'+str(xid)], result[xneid+'-ifOperStatus-'+str(xid)], int(result[xneid+'-ifSpeed-'+str(xid)]), xifalias, xifip, xso, xneid, int(xid))
            else:
		print 'insert'
                SQL = "insert into ip_ne_if (companyno,ne_id,ifindex,ifdescr,ifspeed,ifadminstatus,ifoperstatus,ifalias,ifip,synctime) values ('%s','%s',%d,'%s',%d,'%s','%s','%s','%s',sysdate)" % (xso, xneid, int(xid), result[xneid+'-ifDescr-'+str(xid)], int(result[xneid+'-ifSpeed-'+str(xid)]), result[xneid+'-ifAdminStatus-'+str(xid)], result[xneid+'-ifOperStatus-'+str(xid)], xifalias, xifip)
            print i, '/', ifnum, ':', SQL
            ora.execone(SQL)
            i = i+1
            if (i%50)==0:
                ora.commit()
                sys.stdout.flush()
        if i > 0:
           ora.commit()
           sys.stdout.flush()
    except Exception, detail:
        print 'Exception: ['+nowdate+']', xso, xneid, detail
        SQL = "update ip_ne set mflag=-1,synctime=sysdate where companyno='%s' and ne_id='%s'" % (xso, xneid)
        ora.execone(SQL)
        ora.commit()
        ne_idx = ne_idx+1
        continue

    sys.stdout.flush()

    sys_descr = ''
    rets = agent.snmpget([xIP, '-c', xcomm, snmp_oid['SysDescr-X']])
    if rets is not None and rets[0][1]!='':
        sys_descr = rets[0][1].strip().replace('\'','')
    print 'SysDescr:', sys_descr
    SQL = "update ip_ne set mflag=0,sys_descr='%s',synctime=sysdate where companyno='%s' and ne_id='%s'" % (sys_descr, xso, xneid)
    ora.execone(SQL)
    ora.commit()

    print '%s %s is complete ...' % (xso, xneid)
    sys.stdout.flush()
    ne_idx = ne_idx+1

ora.execone("delete from ip_ne_if where synctime < sysdate-7")
ora.commit()

if ora.db:
    ora.se_close()
sys.exit(0)
