#!/usr/bin/env python
import sys
import os
import string
import time
import binascii
from pysnmpclass import snmpclass
from oraclass import ORA

cuda_online_mib = '.1.3.6.1.4.1.3493.2.4.1.1.25.1.20'
cuda_total_mib = '.1.3.6.1.4.1.3493.2.4.1.1.25.1.19'
arris_online_mib = '.1.3.6.1.4.1.4998.1.1.20.2.12.1.14'
arris_total_mib = '.1.3.6.1.4.1.4998.1.1.20.2.12.1.13'
ubr_online_mib = '.1.3.6.1.4.1.9.9.116.1.4.1.1.4'
ubr_total_mib = '.1.3.6.1.4.1.9.9.116.1.4.1.1.3'
casa_online_mib = '.1.3.6.1.4.1.20858.10.12.1.1.1.1'
casa_total_mib = '.1.3.6.1.4.1.20858.10.12.1.1.1.3'

if len(sys.argv)<2:
    print "[ERROR]: Argument error."
    sys.exit(0)
so = sys.argv[1]
tmpsql = "where so in ('%s')" % (so)

agent = snmpclass(version='v2c',community='public',ptimeout=1,pretries=4)
ora = None
while 1:
    try:
        if ora is None:
            ora = ORA('NMS/NMS@SCNIS')
    except Exception, msg:
        print msg
        pass
        time.sleep(20)
        continue
    
    tx_ip={}
    tx_id={}
    tx_so={}
    tx_comm={}
    tx_type={}
    tx_cnt = 0
    
    txsql = "select so,cmts_id,ip,snmp_ro,type from em_cmts %s order by so,cmts_id" % (tmpsql)
    rs1 = ora.execall(txsql)
    if rs1 is not None and len(rs1)>0:
        for aw in rs1:
            tx_so[tx_cnt] = aw[0]
            tx_id[tx_cnt] = aw[1]
            tx_ip[tx_cnt] = aw[2]
            tx_comm[tx_cnt] = aw[3]
            tx_type[tx_cnt] = aw[4]
            tx_cnt = tx_cnt+1
    
    tx_idx = 0
    while tx_idx<tx_cnt:    
        try:
            result = {}
            nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            xso = tx_so[tx_idx]
            xneid = tx_id[tx_idx]
            xIP = tx_ip[tx_idx]
            xcomm = tx_comm[tx_idx]
            xtype = tx_type[tx_idx]
            
            print '['+nowdate+']',
            print xso, xneid, xIP, xcomm, xtype
            sys.stdout.flush()
            
            if xtype=='Cuda12k':
                online_mib = cuda_online_mib
                total_mib = cuda_total_mib
            elif xtype=='Arris':
                online_mib = arris_online_mib
                total_mib = arris_total_mib
            elif xtype=='Casa':
                online_mib = casa_online_mib
                total_mib = casa_total_mib
            else:
                online_mib = ubr_online_mib
                total_mib = ubr_total_mib
            
            online_array = agent.snmpwalk([xIP, '-c', xcomm, online_mib])
            print online_mib
            i=0
            lens=len(online_array)
            while i<lens:
                if len(online_array[i])>=2:
                    xvalue = online_array[i][1]
                    xidtmp = online_array[i][0].replace(online_mib+'.','')
                    xid_arr = xidtmp.split('.')
                    if len(xid_arr)==1:
                        xid = xid_arr[0]
                        result[xneid+'-IDX-'+str(i)] = xid
                        result[xneid+'-ONLINE-'+str(xid)] = xvalue
                    elif len(xid_arr)==2:
                        xid = xid_arr[1]
                        result[xneid+'-IDX-'+str(i)] = xid
                        try:
                            result[xneid+'-ONLINE-'+str(xid)] = result[xneid+'-ONLINE-'+str(xid)]+xvalue
                        except:
                            result[xneid+'-ONLINE-'+str(xid)] = xvalue
                            pass
                i = i+1
                
            total_array = agent.snmpwalk([xIP, '-c', xcomm, total_mib])
            print total_mib
            i=0
            lens=len(total_array)
            while i<lens:
                if len(total_array[i])>=2:
                    xvalue = total_array[i][1]
                    xidtmp = total_array[i][0].replace(total_mib+'.','')
                    xid_arr = xidtmp.split('.')
                    if len(xid_arr)==1:
                        xid = xid_arr[0]
                        result[xneid+'-IDX-'+str(i)] = xid
                        result[xneid+'-TOTAL-'+str(xid)] = xvalue
                    elif len(xid_arr)==2:
                        xid = xid_arr[1]
                        result[xneid+'-IDX-'+str(i)] = xid
                        try:
                            result[xneid+'-TOTAL-'+str(xid)] = result[xneid+'-TOTAL-'+str(xid)]+xvalue
                        except:
                            result[xneid+'-TOTAL-'+str(xid)] = xvalue
                            pass
                i = i+1
            
            ifnum = i
            
            i = 0
            cmts_online = 0
            cmts_total = 0
            while i<ifnum:
                xid = result[xneid+'-IDX-'+str(i)]
                xonline = int(result[xneid+'-ONLINE-'+str(xid)])
                xtotal = int(result[xneid+'-TOTAL-'+str(xid)])
                cmts_online = cmts_online+xonline
                cmts_total = cmts_total+xtotal
                SQL = "begin PROC_UPD_CM_CNT('%s','%s',%s,%d,%d); end;" % (xso, xneid, xid, xonline, xtotal)
                print SQL
                ora.execone(SQL)
                i = i+1
            SQL = "begin PROC_UPD_CMTS_CNT('%s','%s',%d,%d); end;" % (xso, xneid, cmts_online, cmts_total)
            print SQL
            ora.execone(SQL)
        except Exception, detail:
            print '['+nowdate+']',
            print xneid
            print detail
        
        ora.commit()    
        sys.stdout.flush()
        tx_idx = tx_idx+1
    ora.se_close()
    ora = None
    #time.sleep(30)
    break
sys.exit(0)

