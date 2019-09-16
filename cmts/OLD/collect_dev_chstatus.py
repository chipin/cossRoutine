#!/usr/bin/env python
# -*- coding: big5 -*-
import sys
import time
import MySQLdb
from pysnmpclass import snmpclass
from oraclass import ORA

ora = ORA('nms@cnis')
if not ora.db:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Error: Unable to connect to server [CNIS]'
    sys.exit(0)


snmp_oid = {}
oid_name = []

# Get OID
SQL = "select name,upper(model) model,oid \
       from snmp_mib \
       where name in ('DEVChStatus')"
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

            if xname not in oid_name:
                oid_name.append(xname)
        except Exception, msg:
            print 'Exception: '+str(msg)

if len(snmp_oid) == 0:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Error: SNMP_MIB is empty'

    if ora is not None:
        ora.se_close()
    sys.exit(0)


dev_so = {}
dev_id = {}
dev_ip = {}
dev_comm = {}
dev_maker = {}
dev_cnt = 0

SQL = "select a.companyno,a.dtv_id,a.type,a.ip,a.snmp_ro,a.snmp_rw,b.maker,b.model \
       from dtv_ne a \
       inner join sys_object b on b.ne_id=substr(a.dtv_id,-8,4) and b.stopyn='N' \
       where a.type='RF' and a.stopyn='N' and b.maker='DEV' \
       order by a.companyno,a.dtv_id"
rst = ora.execall(SQL)
if rst is not None and len(rst)>0:
    for aw in rst:
        try:
            dev_so[dev_cnt] = aw[0]
            dev_id[dev_cnt] = aw[1]
            dev_ip[dev_cnt] = aw[3]
            dev_comm[dev_cnt] = aw[4]
            dev_maker[dev_cnt] = aw[6]
            dev_cnt = dev_cnt+1
        except Exception, msg:
            print 'Exception: '+str(msg)

if len(dev_id) == 0:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Error: DEV_ID is empty'

    if ora is not None:
        ora.se_close()
    sys.exit(0)


try:
    mydb = MySQLdb.connect(host="MCT-QOS", user="root", passwd="newom123", db="cmdb_104")
    mydbcur = mydb.cursor()
except Exception, msg:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] Error: Unable to connect to server [MYSQL]'
    sys.exit(0)


ora_retry = mydb_retry = 0
startime = time.time()
while 1:
    try:
        ora.execone('select sysdate from dual')
        ora_retry = 0
    except Exception, msg:
        print str(msg)

        print 'Error: Lost connection to [CNIS], trying to reconnect'
        ora_retry = ora_retry + 1
        ora = ORA('nms@cnis')
        if not ora.db:
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            if ora_retry >= 10:
                print '['+nowdate+'] Error: Lost connection to [CNIS], fail to retry [EXIT]'
                break
            else:
                print '['+nowdate+'] Error: Unable to reconnect to server [CNIS]',ora_retry
                sys.stdout.flush()
                time.sleep(120)
                continue

    try:
        mydb.ping()
        mydb_retry = 0
    except Exception, msg:
        print str(msg)

        print 'Error: Lost connection to [MYSQL], trying to reconnect'
        mydb_retry = mydb_retry + 1
        try:
            mydb = MySQLdb.connect(host="localhost", user="root", passwd="newom123", db="cmdb_%s"%(so))
            mydbcur = mydb.cursor()
        except Exception, msg:
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            if mydb_retry >= 10:
                print '['+nowdate+'] Error: Lost connection to [MYSQL], fail to retry [EXIT]'
                break
            else:
                print '['+nowdate+'] Error: Unable to reconnect to server [MYSQL]',mydb_retry
                sys.stdout.flush()
                time.sleep(120)
                continue

    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] START'

    idx = 0
    while idx < dev_cnt:
        try:
            xso = dev_so[idx]
            xneid = dev_id[idx]
            xip = dev_ip[idx]
            xmaker = dev_maker[idx]
            xcomm = dev_comm[idx]
            print xso,xneid,xip

            if xmaker.find('DEV') >= 0:
                agent = snmpclass(version='v1',ptimeout=1,pretries=3,debug=0)
            else:
                agent = snmpclass(version='v2c',ptimeout=1,pretries=3,debug=0)

            zresult = {}
            for oname in oid_name:
                try:
                    xoid = snmp_oid['%s-X' % (oname)]
                except:
                    try:
                        xoid = snmp_oid['%s-%s' % (oname, xmaker)]
                    except:
                        continue

                rets = agent.snmpwalk([xip, '-c', xcomm, xoid])
                #print oname,xoid,rets
                i = 0
                lens = len(rets)
                while i<lens:
                    zid = rets[i][0].replace(xoid+'.','')
                    try:
                        zvalue = rets[i][1].strip().replace('\'','')
                    except:
                        zvalue = rets[i][1]
                    print '('+str(lens)+'CH)',str(zid)+':'+str(zvalue)

                    if oname in ['ifIndex']:
                        zresult['%s-%d' % (oname, i)] = zid
                    else:
                        zresult['%s-%s' % (oname, zid)] = zvalue

                    if oname == 'DEVChStatus' and lens == 12:
                        break
                    i = i+1

                sys.stdout.flush()

            try:
                ch1_status = zresult['DEVChStatus-1']
            except:
                ch1_status = 'null'
            try:
                ch2_status = zresult['DEVChStatus-2']
            except:
                ch2_status = 'null'

            SQL = "update dtv_ne set ch1_status=%s,ch2_status=%s,synctime=sysdate where companyno='%s' and dtv_id='%s'" % (ch1_status, ch2_status, xso, xneid)
            print SQL
            try:
                #pass
                ora.execone(SQL)
                ora.commit()
            except Exception, msg:
                print 'Exception: '+str(msg)
                sys.exit(0)

            sid = (int)((time.time()/300)%115200)
            xtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            SQL = "select sid from dev_chstatus where sid=%d and ne_id='%s'" % (sid, xneid)
            mydbcur.execute(SQL)
            ins_flag = 0
            result = mydbcur.fetchall()
            if result:
                for record in result:
                    if record[0] is not None:
                        pass
                    else:
                        ins_flag = 1
            else:
                ins_flag = 1

            if ins_flag==1:
                SQL = "insert into dev_chstatus (sid,ne_id,updatetime,ch1,ch2) values (%d,'%s','%s',%s,%s)" % (sid, xneid, xtime, ch1_status, ch2_status)
            else:
                SQL = "update dev_chstatus set updatetime='%s',ch1=%s,ch2=%s where sid=%d and ne_id='%s'" % (xtime, ch1_status, ch2_status, sid, xneid)

            print SQL
            try:
                mydbcur.execute(SQL)
                mydb.commit()
                #pass
            except Exception, msg:
                print 'Exception: '+str(msg)

        except Exception, msg:
            print 'Exception: '+str(msg)

        sys.stdout.flush()
        idx = idx+1

    endtime = time.time()
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print "[%s] END (totalsec: %d)\n" % (nowdate, endtime-startime)
    sys.stdout.flush()

    #break

    while endtime-startime<300:
        print 'sleep 30 secs ...'
        sys.stdout.flush()
        time.sleep(30)
        endtime = time.time()
    startime = time.time()

if ora is not None:
    ora.se_close()
if mydb is not None:
    mydb.close()
sys.exit(0)
