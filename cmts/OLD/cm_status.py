#!/usr/bin/env python
# -*- coding: big5 -*-
import sys, time, re
import binascii
import threading
from pysnmpclass import snmpclass
from oraclass import ORA

mitem = {}
cmts = {}

if len(sys.argv)!=3:
    print 'Usage: cm_measure.py companyno cmmac'+chr(10)
    sys.exit(1);
else :
    so    = sys.argv[1]
    cmmac = sys.argv[2].upper()

def make_mac(mac):
    try:
        mac_b = binascii.unhexlify(mac)
        mac1 = ord(mac_b[0])
        mac2 = ord(mac_b[1])
        mac3 = ord(mac_b[2])
        mac4 = ord(mac_b[3])
        mac5 = ord(mac_b[4])
        mac6 = ord(mac_b[5])
        mac_mib = "%d.%d.%d.%d.%d.%d" % (mac1,mac2,mac3,mac4,mac5,mac6)
    except Exception, msg:
        mac_mib = '0.0'
        pass
    return mac_mib

def clear_m(id, m, cnt):  # id=cmtsno , m=result array , cnt=array count
    i = 0
    while i<cnt:
        if m[str(id)+'-VTYPE-'+str(i)]=='INT':
            m[str(id)+'-V-'+str(i)] = 0
        elif m[str(id)+'-VTYPE-'+str(i)]=='STRING':
            m[str(id)+'-V-'+str(i)] = ''
        else:
            m[str(id)+'-V-'+str(i)] = None
        m[str(id)+'-DONE-'+str(i)] = 'N'
        i = i+1
    return m

def snmp_walk(ip, oid, types, comm):
    ret_value = {}
    oid_value = {}
    try:
        agt = snmpclass(version='v2c', community=comm, ptimeout=3, pretries=5, debug=0)
        rets = agt.snmpwalk([ip, '-c', comm, oid])
        #print rets
        i = 0
        if rets is not None and len(rets)>0:
            while i<len(rets):
                oid_value[i] = rets[i][0]
                ret_value[i] = rets[i][1]
                i = i+1
        else:
            return None
    except Exception, msg:
        pass
        return None
    if ret_value is None:
        return None
    else:
        v = ''
        if types=='INT':
            for i in range(len(rets)):
                v = v+str(ret_value[i])
                if i<len(rets)-1:
                    v = v+','
        elif types=='STRING':
            for i in range(len(rets)):
                v = v+ret_value[i]
                if i<len(rets)-1:
                    v = v+','
        elif types=='IP':
            for i in range(len(rets)):
                ip1 = ord(ret_value[i][0])
                ip2 = ord(ret_value[i][1])
                ip3 = ord(ret_value[i][2])
                ip4 = ord(ret_value[i][3])
                ip = "%d.%d.%d.%d" % (ip1, ip2, ip3, ip4)
                v = v+ip
                if i<len(rets)-1:
                    v = v+','
        elif types=='IP_MAC':
            for i in range(len(rets)):
                xip = oid_value[i].replace(oid+".", "")
                xip = xip[4:]
                v = v+xip
                if i<len(rets)-1:
                    v = v+','
        elif types=='IDX':
            for i in range(len(rets)):
                idx = oid_value[i].replace(oid+".", "")
                v = v+str(idx)
                if i<len(rets)-1:
                    v = v+','
        elif types=='HEX-STRING':
            for i in range(len(rets)):
                v = v+ret_value[i].encode('hex').upper()
                if i<len(rets)-1:
                    v = v+','
        else:
            return ret_value[0]
        return v

def snmp_get(ip, oid, types, comm):
    ret_value = None
    try:
        agt = snmpclass(version='v2c', community=comm, ptimeout=3, pretries=5, debug=0)
        rets = agt.snmpget([ip, '-c', comm, oid])
        if rets is not None and rets[0][1]!='':
            ret_value = rets[0][1]
    except Exception, msg:
        pass
    if ret_value is None:
        return None
    else:
        if types=='INT':
            return int(ret_value)
        elif types=='STRING':
            return str(ret_value)
        elif types=='IP':
            ip1 = ord(ret_value[0])
            ip2 = ord(ret_value[1])
            ip3 = ord(ret_value[2])
            ip4 = ord(ret_value[3])
            ip = "%d.%d.%d.%d" % (ip1, ip2, ip3, ip4)
            return ip
        else:
            return ret_value

def valify_cmts(id, mac):
    global cmts
    cmts_ip = cmts['IP-'+str(id)]
    cmts_snmp = cmts['SNMP-'+str(id)]
    oid = '.1.3.6.1.2.1.10.127.1.3.7.1.2.' + make_mac(mac)
    macidx = snmp_get(cmts_ip, oid, 'INT', cmts_snmp)
    if macidx is None or macidx<0:
        cmts['MACIDX-'+str(id)] = -1
        cmts['CMSTATUS-'+str(id)] = -1
        cmts['DONE-'+str(id)] = 'Y'
    else:
        cmts['MACIDX-'+str(id)] = macidx
        oid = '.1.3.6.1.2.1.10.127.1.3.3.1.3.' + str(macidx)
        cmip = snmp_get(cmts_ip, oid, 'STRING', cmts_snmp)
        oid = '.1.3.6.1.2.1.10.127.1.3.3.1.9.' + str(macidx)
        cmstatus = snmp_get(cmts_ip, oid, 'STRING', cmts_snmp)
        cmts['CMIP-'+str(id)] = cmip
        cmts['CMSTATUS-'+str(id)] = cmstatus
        cmts['DONE-'+str(id)] = 'Y'

def catch_value(id, vid, comm):
    global cmts, mitem
    try:
        cmts_ip = cmts['IP-'+str(id)]
        cmts_snmp = cmts['SNMP-'+str(id)]
        cmip = cmts['CMIP-'+str(id)]
        macidx = cmts['MACIDX-'+str(id)]
        vtype = mitem[str(id)+'-VTYPE-'+str(vid)]
        mtype = mitem[str(id)+'-MT-'+str(vid)]
        oid = mitem[str(id)+'-OID-'+str(vid)]
        oper = mitem[str(id)+'-OPER-'+str(vid)]
        ifidx = []
        if mtype=='CMTS':
            oid = oid + str(macidx)
            snmpip = cmts_ip
            snmp_comm = cmts_snmp
        elif mtype=='CMTS_MAC':
            if cmmac is not None and cmmac!='':
                oid = oid + '.' + make_mac(cmmac)
                snmpip = cmts_ip
                snmp_comm = cmts_snmp
            else:
                oper = ''
        elif mtype=='CASA_MAC':
            if cmmac is not None and cmmac!='':
                #oid = oid + '.' + make_mac(cmmac)+ '.1.4'
                oid = oid + '.' + make_mac(cmmac)
                snmpip = cmts_ip
                snmp_comm = cmts_snmp
            else:
                oper = ''
        elif mtype=='CM':
            snmpip = cmip
            snmp_comm = 'public'
        else:
            snmpip = cmts_ip
            snmp_comm = cmts_snmp
            try:
                ptr = 0
                if int(mtype)-1>=0:
                    while mitem[str(id)+'-DONE-'+str(int(mtype)-1)]=='N':
                        time.sleep(0.01)
                    ptr = mitem[str(id)+'-V-'+str(int(mtype)-1)]

                    ma = re.match(r"^[\d]+$", ptr) # 非純數字, 表示有複數介面
                    if ma is None:
                        ptr1 = ptr.strip().split(',')
                        if ptr1 is not None and len(ptr1) > 0:
                            for i in range(len(ptr1)):
                                if ptr1[i] is not None and len(ptr1[i]) > 0:
                                    if ptr1[i] not in ifidx:
                                        ifidx.append(ptr1[i])
                    #print ifidx

            except:
                pass
            oid = oid + str(ptr)
        if oper=='GROUP':
            if snmpip=='0.0.0.0':
                v = None
            else:
                v = snmp_walk(snmpip, oid, vtype, snmp_comm)
            if v is None:
                mitem[str(id)+'-V-'+str(vid)] = ''
            mitem[str(id)+'-V-'+str(vid)] = v
        else:
            if snmpip=='0.0.0.0':
                v = None
            else:
                if ifidx is not None and len(ifidx) > 0:
                    n = ''
                    for i in range(len(ifidx)):
                        oid = mitem[str(id)+'-OID-'+str(vid)] + str(ifidx[i])
                        m = snmp_get(snmpip, oid, vtype, snmp_comm)
                        if n is not None and len(n) > 0:
                            n = n + ',' + str(m)
                        else:
                            n = str(m)
                    v = n
                else:
                    v = snmp_get(snmpip, oid, vtype, snmp_comm)
            if v is None:
                mitem[str(id)+'-V-'+str(vid)] = ''
            mitem[str(id)+'-V-'+str(vid)] = v
    except Exception, msg:
        #print msg
        pass
    mitem[str(id)+'-DONE-'+str(vid)] = 'Y'

def measure(id):
    global cmts, mitem
    mitem[str(id)+'-V-0'] = cmts['MACIDX-'+str(id)]
    mitem[str(id)+'-V-1'] = cmts['CMIP-'+str(id)]
    mitem[str(id)+'-V-2'] = cmts['CMSTATUS-'+str(id)]
    cmts_snmp = cmts['SNMP-'+str(id)]

    i = 3
    while i<mitem['COUNT']:
        p = threading.Thread(target = catch_value, args = (id, i, cmts_snmp,))
        p.start()
        time.sleep(0.01)
        i = i+1

    check_loop_total = 0
    while check_loop_total < 1000:
        time.sleep(0.2)
        i = 3
        check_loop = 3
        while i<mitem['COUNT']:
            if mitem[str(id)+'-DONE-'+str(i)]=='Y':
                check_loop = check_loop+1
            i = i+1
        if check_loop>=mitem['COUNT']:
            break
        check_loop_total = check_loop_total+1


ora_nms = ORA('nms@cnis')
if not ora_nms.db:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '[' + nowdate + ']: Unable to connect to server [CNIS]'
    sys.exit(0)

# ------------- Get CMTS infomation -------------------------------------------
SQL = "select cmts_id,ip,snmp_ro from cmts where companyno='%s' and stopyn='N' order by cmts_id" % (so)
rst = ora_nms.execall(SQL)
if rst is None:
    print 'Error: Unable to query CMTS [CNIS]'
    ora_nms.se_close()
    sys.exit(0)
else:
    if len(rst)>0:
        i = 0
        for aw in rst:
            cmts['ID-'+str(i)] = aw[0]
            cmts['IP-'+str(i)] = aw[1]
            cmts['SNMP-'+str(i)] = aw[2]
            cmts['MACIDX-'+str(i)] = None
            cmts['CMIP-'+str(i)] = None
            cmts['CMSTATUS-'+str(i)] = None
            cmts['DONE-'+str(i)] = 'N'
            cmts['MEASURE-'+str(i)] = 'N'
            i = i+1
        cmts['COUNT'] = i
    else:
        print 'Error: Unable to query CMTS [CNIS]'
        ora_nms.se_close()
        sys.exit(0)

# ------------- Get measure items -------------------------------------------
SQL = "select oid, ip_type, v_type, operator from cm_measure_item where id <= 3 order by id"
rst = ora_nms.execall(SQL)
if rst is None:
    print 'Error: Unable to query cm_measure_item [CNIS]'
    ora_nms.se_close()
    sys.exit(0)
else:
    if len(rst)>0:
        cmtsidx = 0
        mitem['COUNT'] = 0
        while cmtsidx<cmts['COUNT']:
            i = 0
            for aw in rst:
                mitem[str(cmtsidx)+'-OID-'+str(i)] = aw[0]
                mitem[str(cmtsidx)+'-MT-'+str(i)] = aw[1]
                mitem[str(cmtsidx)+'-VTYPE-'+str(i)] = aw[2]
                mitem[str(cmtsidx)+'-OPER-'+str(i)] = aw[3]
                mitem[str(cmtsidx)+'-V-'+str(i)] = None
                i = i+1
            if mitem['COUNT']==0:
                mitem['COUNT'] = i
            mitem = clear_m(cmtsidx, mitem, mitem['COUNT'])
            cmtsidx = cmtsidx+1
    else:
        print 'Error: Unable to query cm_measure_item [CNIS]'
        ora_nms.se_close()
        sys.exit(0)

i = 0
while i<cmts['COUNT']:
    p = threading.Thread(target = valify_cmts, args = (i, cmmac,))
    p.start()
    i = i+1

valid_cmts_idx = -1
check_loop = 0
while check_loop < 1000:
    i = 0
    check_cmts = 0
    time.sleep(0.01)
    while i<cmts['COUNT']:
        if cmts['DONE-'+str(i)]=='Y':
            check_cmts = check_cmts+1
            if cmts['MEASURE-'+str(i)]=='N' and cmts['MACIDX-'+str(i)]>0 and cmts['CMSTATUS-'+str(i)]=='6':
                valid_cmts_idx = i
                check_cmts = cmts['COUNT']
                break
            elif cmts['MEASURE-'+str(i)]=='N' and cmts['MACIDX-'+str(i)]>0:
                cmts['MEASURE-'+str(i)] = 'Y'
                valid_cmts_idx = i
        i = i+1
    if check_cmts>=cmts['COUNT']:
        break
    check_loop = check_loop+1

if valid_cmts_idx>=0:
    measure(valid_cmts_idx)
    print 'CMTS_ID: %s' % (cmts['ID-'+str(valid_cmts_idx)])
    print 'CMTS_IP: %s' % (cmts['IP-'+str(valid_cmts_idx)])

    i = 0
    while i < mitem['COUNT']:
        if mitem[str(valid_cmts_idx)+'-V-'+str(i)] is None:
            pass
        else:
            if i+1 == 1:
                print 'CM_IDX:',mitem[str(valid_cmts_idx)+'-V-'+str(i)]
            elif i+1 == 2:
                print 'CM_IP:',mitem[str(valid_cmts_idx)+'-V-'+str(i)]
            elif i+1 == 3:
                print 'CM_STATUS:',mitem[str(valid_cmts_idx)+'-V-'+str(i)]
        i = i+1

else:
    print 'CMTS_ID: X'
    print 'CMTS_IP: X'

if ora_nms is not None :
    ora_nms.se_close()

sys.exit(0)
