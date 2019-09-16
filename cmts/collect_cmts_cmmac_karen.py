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
if so.upper() != 'TFM1' and so.upper() != 'TFM2' and so.upper() != 'KBRO1' and so.upper() != 'KBRO2' and so.upper() != 'KBRO3' and so.upper() != 'KBRO4':
    print 'Error: Argument error'
    sys.exit(0)

agent = snmpclass(version='v2c',ptimeout=10,pretries=3,debug=0)

def query_status(ycmtsid, yip, ymodel, ycomm, yoid):
    global cmts_oid, agent
    print yoid
    print ycmtsid, yip, ymodel, ycomm

    yresult = {}

    try:
        for oname in yoid:
            try:
                tmp_mib = cmts_oid['%s-X' % (oname)]
		print 'tmp_mib',tmp_mib
            except:
                try:
                    tmp_mib = cmts_oid['%s-%s' % (oname, ymodel)]
		    print tmp_mib
                except:
                    continue
            lens = 0
            for y in range(0, 3):
                try:
                    rets = agent.snmpwalk([yip, '-c', ycomm, tmp_mib])
                    lens = len(rets)
                    i = 0
                    while i<lens:
                        zid = rets[i][0].replace(tmp_mib+'.','')
			print 'zid',zid
                        zvalue = rets[i][1]
			print 'zvalue',zvalue

                        if oname in ['ifIndex']:
                            yresult['%s-%s-%d' % (ycmtsid, oname, i)] = zid
                        elif oname in ['docsIfCmtsCmPtr']:
                            yresult['%s-%s-%d' % (ycmtsid, oname, i)] = zid
                            yresult['%s-%s-%d' % (ycmtsid, 'docsIfCmtsCmPtrIdx', i)] = zvalue
                        elif oname in ['docsIf3CmtsCmUsStatusSignalNoise']: # 透過USSNR取出USIDX
                            zz = zid.split('.')
                            zp = int(zz[0])
                            zi = int(zz[1])
                            if '%s-%s-%d-0' % (ycmtsid, oname, zp) not in yresult:
                                yresult['%s-%s-%d-0' % (ycmtsid, oname, zp)] = zi
                            elif '%s-%s-%d-1' % (ycmtsid, oname, zp) not in yresult:
                                yresult['%s-%s-%d-1' % (ycmtsid, oname, zp)] = zi
                        else:
                            yresult['%s-%s-%s' % (ycmtsid, oname, zid)] = zvalue

                        i = i+1
                        print ycmtsid,oname,zid,zvalue
                    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                    print "[%s] %s (%s %s) -> %d (%d)" % (nowdate, ycmtsid, oname, tmp_mib, lens, y)
                except:
                    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                    print "[%s] Exception: %s (%s %s)(%d)" % (nowdate, ycmtsid, oname, tmp_mib, y)
                if lens > 0:
                    break
            if oname in ['ifIndex','docsIfCmtsCmPtr']:
                yresult['%s-%s-LEN' % (ycmtsid, oname)] = lens
            sys.stdout.flush()
    except Exception, msg:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+']:'+str(msg)

    return yresult


cmts_oid = {}
oid_name = []

ora = ORA('nms@cnis')

if not ora.db:
    sys.exit(0)

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print '['+nowdate+'] START'

# Get CMTS OID
SQL = "select name,upper(model) model,oid \
       from snmp_mib \
       where name in ('SysDescr','ifIndex','ifDescr','ifAdminStatus','ifOperStatus','ifSpeed','ifHighSpeed', \
                      'docsIfCmtsCmPtr','docsIfCmtsCmStatusUpChannelIfIndex','docsIfCmtsCmStatusDownChannelIfIndex','docsIfCmtsCmStatusIpAddress','docsIfCmtsCmStatusValue', \
                      'docsIfDownChannelId','docsIfDownChannelFrequency','docsIfDownChannelWidth','docsIfDownChannelModulation','docsIfDownChannelInterleave', \
                      'docsIfUpChannelId','docsIfUpChannelFrequency','docsIfUpChannelWidth','docsIfUpChannelModulation','docsIf3CmtsCmUsStatusSignalNoise')"
rst = ora.execall(SQL)
if rst is not None and len(rst)>0:
    for aw in rst:
        try:
            xname = aw[0]
            xmodel = aw[1]
            xoid = aw[2]
            if xmodel is None:
                xmodel = 'X'
            cmts_oid[xname+'-'+xmodel] = xoid

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

cmts_so={}
cmts_id={}
cmts_ip={}
cmts_comm={}
cmts_mflag={}
cmts_model={}
cmts_cnt = 0

if so.upper() == 'TFM1':
    sosql = "a.companyno in ('101','103','104')"
elif so.upper() == 'TFM2':
    sosql = "a.companyno in ('300','701')"
elif so.upper() == 'KBRO1':
    sosql = "a.companyno in ('210','220','230','240')"
elif so.upper() == 'KBRO2':
    sosql = "a.companyno in ('250','260','106')"
elif so.upper() == 'KBRO3':
    sosql = "a.companyno in ('310','330','410','420')"
else:
    sosql = "a.companyno in ('610','810','820')"

cmtssql = "select a.companyno,a.cmts_id,a.ip,a.snmp_ro,a.mflag, \
           case \
             when upper(b.maker||b.model) like '%%UBR%%' then 'UBR' when upper(b.maker||b.model) like '%%CBR%%' then 'UBR' \
	     when upper(b.maker||b.model) like '%%CASA%%' then 'CASA' \
             when upper(b.maker||b.model) like '%%CUDA%%' then 'CUDA' when upper(b.maker||b.model) like '%%MOTO%%' then 'MOTO' else NULL end type \
           from cmts a \
           inner join sys_object b on b.ne_id=substr(a.cmts_id,-8,4) and b.stopyn='N' \
           where " + sosql + " and a.cmts_id='GS3_CK01_001' and a.ip is not NULL and a.snmp_ro is not NULL and a.stopyn='N' and a.mflag > 0 \
           order by a.companyno,a.updatetime,a.createtime asc"
print cmtssql
rs1 = ora.execall(cmtssql)
if rs1 is not None and len(rs1)>0:
    for aw in rs1:
        cmts_so[cmts_cnt] = aw[0]
        cmts_id[cmts_cnt] = aw[1]
        cmts_ip[cmts_cnt] = aw[2]
        cmts_comm[cmts_cnt] = aw[3]
        cmts_mflag[cmts_cnt] = aw[4]
        cmts_model[cmts_cnt] = aw[5]
        cmts_cnt = cmts_cnt+1

cmts_idx = 0
while cmts_idx<cmts_cnt:
    try:
        xso = cmts_so[cmts_idx]
        xcmtsid = cmts_id[cmts_idx]
        xIP = cmts_ip[cmts_idx]
        xcomm = cmts_comm[cmts_idx]
        xmflag = cmts_mflag[cmts_idx]
        xmodel = cmts_model[cmts_idx]

        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print '['+nowdate+']', xso, xcmtsid, xIP, xcomm, xmodel

        result = {}
        result = query_status(xcmtsid, xIP, xmodel, xcomm, oid_name)
        #print 'result=',result

        ifnum = 0
        if result['%s-ifIndex-LEN' % (xcmtsid)] > 0:
            ifnum = result['%s-ifIndex-LEN' % (xcmtsid)]

        for y in range(0, 3):
            try:
                ora.execone('select sysdate from dual')
            except Exception, msg:
                nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                print '['+nowdate+'] Error: Lost connection to [CNIS], trying to reconnect. '+str(msg)
                ora = ORA('nms@cnis')
                if ora.db:
                    break
                else:
                    print '['+nowdate+'] Error: Unable to reconnect to server [CNIS]',y
                    sys.stdout.flush()
                    if y == 2:
                        sys.exit(0)
                    else:
                        time.sleep(10)

        i = 0
        while i<ifnum:
            xid = result[xcmtsid+'-ifIndex-'+str(i)]
            chtype = ''

            try:
                chid = int(result[xcmtsid+'-docsIfDownChannelId-'+str(xid)])
                chtype = 'DS'
            except:
                try:
                    chid = int(result[xcmtsid+'-docsIfUpChannelId-'+str(xid)])
                    chtype = 'US'
                except:
                    chid = -1
            try:
                chfreq = int(result[xcmtsid+'-docsIfDownChannelFrequency-'+str(xid)])
            except:
                try:
                    chfreq = int(result[xcmtsid+'-docsIfUpChannelFrequency-'+str(xid)])
                except:
                    chfreq = -1
            try:
                chbw = int(result[xcmtsid+'-docsIfDownChannelWidth-'+str(xid)])
            except:
                try:
                    chbw = int(result[xcmtsid+'-docsIfUpChannelWidth-'+str(xid)])
                except:
                    chbw = -1
            try:
                chmodf = int(result[xcmtsid+'-docsIfDownChannelModulation-'+str(xid)])
            except:
                try:
                    chmodf = int(result[xcmtsid+'-docsIfUpChannelModulation-'+str(xid)])
                except:
                    chmodf = -1
            try:
                chinter = int(result[xcmtsid+'-docsIfDownChannelInterleave-'+str(xid)])
            except:
                chinter = -1

            try:
                if int(result[xcmtsid+'-ifSpeed-'+str(xid)]) == 4294967295 and int(result[xcmtsid+'-ifHighSpeed-'+str(xid)]) > 0:
                    result[xcmtsid+'-ifSpeed-'+str(xid)] = int(result[xcmtsid+'-ifHighSpeed-'+str(xid)]) * 1000000
            except:
                pass

            SQL = "update cmts_if set ifdescr='' where companyno='%s' and cmts_id='%s' and ifindex != %d and ifdescr='%s'" % (xso, xcmtsid, int(xid), result[xcmtsid+'-ifDescr-'+str(xid)])
            #print SQL
            #ora.execone(SQL)

            SQL = "select ifindex from cmts_if where companyno='%s' and cmts_id='%s' and ifindex=%d" % (xso, xcmtsid, int(xid))
            rs2 = ora.execall(SQL)
            reclen = len(rs2)
            if rs2 is not None and reclen>0:
                SQL = "update cmts_if set ifdescr='%s',ifadminstatus='%s',ifoperstatus='%s',ifspeed=%d,ch_id=%d,ch_freq=%d,ch_bw=%d,ch_mod=%d,ch_inter=%d,ch_type='%s',synctime=sysdate,cmactive=null,cmtotal=null where companyno='%s' and cmts_id='%s' and ifindex=%d" % (result[xcmtsid+'-ifDescr-'+str(xid)], result[xcmtsid+'-ifAdminStatus-'+str(xid)], result[xcmtsid+'-ifOperStatus-'+str(xid)], int(result[xcmtsid+'-ifSpeed-'+str(xid)]), chid,chfreq,chbw,chmodf,chinter,chtype,xso,xcmtsid,int(xid))
            else:
                SQL = "insert into cmts_if (companyno,cmts_id,ifindex,ifdescr,ifspeed,ifadminstatus,ifoperstatus,ch_id,ch_freq,ch_bw,ch_mod,ch_inter,ch_type,synctime) values ('%s','%s',%d,'%s',%d,%d,%d,%d,%d,%d,%d,%d,'%s',sysdate)" % (xso, xcmtsid, int(xid), result[xcmtsid+'-ifDescr-'+str(xid)], int(result[xcmtsid+'-ifSpeed-'+str(xid)]), result[xcmtsid+'-ifAdminStatus-'+str(xid)], result[xcmtsid+'-ifOperStatus-'+str(xid)], chid,chfreq,chbw,chmodf,chinter,chtype)
            print i, '/', ifnum, ':', SQL
            #ora.execone(SQL)
            i = i+1
            if (i%50)==0:
                #ora.commit()
                sys.stdout.flush()
        if i > 0:
            #ora.commit()
            sys.stdout.flush()
    except Exception, detail:
        print '['+nowdate+']', xso, xcmtsid, detail
        SQL = "update cmts set mflag=-1,synctime=sysdate where companyno='%s' and cmts_id='%s'" % (xso, xcmtsid)
        #ora.execone(SQL)
        #ora.commit()
        cmts_idx = cmts_idx+1
        continue

    sys.stdout.flush()

    if xmflag==1:
        #truncsql = "update cmmac set status=-1,updatetime=trunc(sysdate) where companyno='%s' and cmts_id='%s'" % (xso, xcmtsid)
        truncsql = "update cmmac set status=-1 where companyno='%s' and cmts_id='%s'" % (xso, xcmtsid)
	print truncsql
        #ora.execone(truncsql)
        #ora.commit()

        try:
            macnum = 0
            if result['%s-docsIfCmtsCmPtr-LEN' % (xcmtsid)] > 0:
                macnum = result['%s-docsIfCmtsCmPtr-LEN' % (xcmtsid)]
            print macnum
            i=0
            while i<macnum:
                xid = result[xcmtsid+'-docsIfCmtsCmPtr-'+str(i)]
		print xid
                xvalue = result[xcmtsid+'-docsIfCmtsCmPtrIdx-'+str(i)]
                mac = xid.split('.')
                cmmac = "%.2X%.2X%.2X%.2X%.2X%.2X" % (int(mac[0]), int(mac[1]), int(mac[2]), int(mac[3]), int(mac[4]), int(mac[5]))

                try:
                    xuplnkidx = result[xcmtsid+'-docsIf3CmtsCmUsStatusSignalNoise-'+str(xvalue)+'-0']
                except Exception, detail:
                    try:
                        xuplnkidx = result[xcmtsid+'-docsIfCmtsCmStatusUpChannelIfIndex-'+str(xvalue)]
                    except Exception, detail:
                        xuplnkidx = -1
                try:
                    xuplnkidx2 = str(result[xcmtsid+'-docsIf3CmtsCmUsStatusSignalNoise-'+str(xvalue)+'-1'])
                except Exception, detail:
                    xuplnkidx2 = 'null'
                try:
                    xdownlnkidx = result[xcmtsid+'-docsIfCmtsCmStatusDownChannelIfIndex-'+str(xvalue)]
                except Exception, detail:
                    xdownlnkidx = -1
                try:
                    cmip = result[xcmtsid+'-docsIfCmtsCmStatusIpAddress-'+str(xvalue)]
                except Exception, detail:
                    cmip = ''
                try:
                    status = result[xcmtsid+'-docsIfCmtsCmStatusValue-'+str(xvalue)]
                except Exception, detail:
                    status = -1

                SQL = "select idx from cmmac where companyno='%s' and cmmac='%s'" % (xso, cmmac)
                rs2 = ora.execall(SQL)
                reclen = len(rs2)
                if rs2 is not None and reclen>0:
                    SQL = "update cmmac set cmts_id='%s',idx=%d,ip='%s',uplink_idx=%d,uplink_idx2=%s,dllink_idx=%d,status=%d,updatetime=trunc(sysdate) where companyno='%s' and cmmac='%s'" % (xcmtsid, xvalue, cmip, xuplnkidx, xuplnkidx2, xdownlnkidx, status, xso, cmmac)
                else:
                    SQL = "insert into cmmac (companyno,cmts_id,cmmac,idx,ip,uplink_idx,uplink_idx2,dllink_idx,status,updatetime,synctime) values ('%s','%s','%s',%d,'%s',%d,%s,%d,%d,trunc(sysdate),trunc(sysdate-0.8,'MI'))" % (xso, xcmtsid, cmmac, xvalue, cmip, xuplnkidx, xuplnkidx2, xdownlnkidx, status)
                print i, '/', macnum, ':', SQL
                ora.execone(SQL)
                ora.commit()
                sys.stdout.flush()
                i = i+1
                #if (i%50)==0:
                #    ora.commit()
                #    sys.stdout.flush()
            #if i > 0:
            #    ora.commit()
            #    sys.stdout.flush()
        except Exception, detail:
            print '['+nowdate+']', xso, xcmtsid, detail
            SQL = "update cmts set mflag=-1,synctime=sysdate where companyno='%s' and cmts_id='%s'" % (xso, xcmtsid)
            #ora.execone(SQL)
            #ora.commit()

    cmts_descr = ''
    rets = agent.snmpget([xIP, '-c', xcomm, cmts_oid['SysDescr-X']])
    if rets is not None and rets[0][1]!='':
        cmts_descr = rets[0][1].strip().replace('\'','')
    print 'SysDescr:', cmts_descr
    SQL = "update cmts set mflag=0,sys_descr='%s',synctime=sysdate where companyno='%s' and cmts_id='%s'" % (cmts_descr, xso, xcmtsid)
    #ora.execone(SQL)
    #ora.commit()

    print '%s %s is complete ...' % (xso, xcmtsid)
    sys.stdout.flush()
    cmts_idx = cmts_idx+1


if ora.db:
    ora.se_close()

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())

