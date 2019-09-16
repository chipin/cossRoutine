#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  One of the following entitlement commands can be used to entitle a subscriber for a Pre-Paid product:
#    createSector (SCFULL)
#    overwriteSector (SOFULL)
#    synchronizeSector (SOSYNC)
#    createEntitlements (SCENTL)
#    overwriteEntitlements (SOENTL)
#  One of the following de-entitlement commands can be used:
#    deleteEntitlements (SDENTL)
#    overwriteEntitlements (SOENTL)
#    overwriteSector (SOFULL)
#    synchronizeSector (SOSYNC)
#    deleteAllEntitlements (SDPROA)
#
#

import sys
import os
import struct
import array
import time
import math
import string
import urllib
import httplib
import binascii
from oraclass import ORA

def utf8(s):
    if s is None:
        return ""
    t = s.decode('big5')
    t1 = t.encode('utf-8')
    return t1

if len(sys.argv)<=1:
    #sosql = "and so='999'"
    sosql = "and so not in ('101','103','104','300','701','106')"
    CA_operator = "TFM"
else:
    so = sys.argv[1]
    sosql = "and so='%s'" % (so)
    if so=='106':
        CA_operator = "CG"
    else:
        CA_operator = "TFM"

CA_server = "10.250.1.11"
q_table = "irdeto_queue"
http_server_c = None
cmd_list = {}

soap_header = '<?xml version="1.0" encoding="UTF-8"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="**namespace**"><SOAP-ENV:Body>'
soap_tail = '</SOAP-ENV:Body></SOAP-ENV:Envelope>'

SQL = "select cmd,url,action,space,type,param from irdeto_matrix"
oracon = ORA('COSS@CNIS')
rst = oracon.execall(SQL)
if rst is not None and len(rst)>0:
    for aw in rst:
        cmd = aw[0]
        url = aw[1]
        action = aw[2]
        space = aw[3]
        type = aw[4]
        param = aw[5]
        cmd_list['URL-'+str(cmd)] = url
        cmd_list['ACT-'+str(cmd)] = action
        cmd_list['SPE-'+str(cmd)] = space
        cmd_list['TYP-'+str(cmd)] = type
        cmd_list['PRM-'+str(cmd)] = param.split(",")
oracon.se_close()
oracon = None

def open_http():
    global http_server_c, CA_server
    if http_server_c is None:
        http_server_c = httplib.HTTPConnection("%s" % (CA_server))
    else:
        http_server_c.close()
        http_server_c = httplib.HTTPConnection("%s" % (CA_server))
    http_server_c._http_vsn = 11
    http_server_c._http_vsn_str = 'HTTP/1.1'
    return http_server_c

def close_http():
    global http_server_c, CA_server
    if http_server_c is None:
        pass
    else:
        http_server_c.close()
        http_server_c = None

def p_error(msg):
    print "[Error]: %s" % (msg)
    return "ERROR", msg

def send_cmd(cmd, p):
    global CA_server, soap_header, soap_tail, CA_operator
    try:
        print cmd, p
        durl = '%s' % (cmd_list['URL-'+str(cmd)])
        c1url = '%s' % (cmd_list['ACT-'+str(cmd)]).replace("irdeto.com", CA_server)
        curl = '%s' % (cmd_list['ACT-'+str(cmd)])
        xurl = '%s' % (cmd_list['SPE-'+str(cmd)])
        soap_head_str = soap_header.replace("**namespace**", xurl)
        ptmp = cmd_list['PRM-'+str(cmd)]
        if len(ptmp)>len(p):
            return p_error("Parameters not enough")
        params = ''
        for i in range(0, len(ptmp)):
            if ptmp[i]=='productTagList':
                params = "%s<ns1:%s><ns1:string>%s</ns1:string></ns1:%s>" % (params, ptmp[i], p[i], ptmp[i])
            else:
                params = "%s<ns1:%s>%s</ns1:%s>" % (params, ptmp[i], p[i], ptmp[i])
        xmls = '%s<ns1:%s><ns1:operatorTag>%s</ns1:operatorTag>%s</ns1:%s>%s%c' % (soap_head_str, cmd, CA_operator, params, cmd, soap_tail, chr(10))
        print xmls
        xhttp = open_http()

        xhttp.putrequest("POST", durl, 0, 1)
        xhttp.putheader("Connection", "Keep-Alive")
        xhttp.putheader("User-Agent", "Python-SOAP/kbro")
        xhttp.putheader("Content-type", "text/xml; charset=utf-8")
        xhttp.putheader("SOAPAction", '\"%s\"' % (curl))
        xhttp.putheader("Content-length", "%d" % (len(xmls)))
        xhttp.endheaders()
        xhttp.send(xmls)

        xrep = xhttp.getresponse()
        res = xrep.read()
        print res
        xrep.close()
        token = res.split(cmd+"Result>")
        if token is not None and len(token)>1:
            result_str = token[1]
        else:
            result_str = res
        if '<message>OK</message>' in result_str:
            return 'OK', result_str
        else:
            return 'ERROR', result_str
    except Exception, detail:
        pass
        print str(detail)
        return "ERROR", str(detail)[0:127]

def ora_upd(ora, sid, status, result=None, ca_cmd=None, ca_ret=None):
    try:
        if result is not None:
            result = string.replace(result, "'","*")
            result = string.replace(result, '"',"*")
        result_sql = ''
        if result is not None:
            result_sql = ",result='%s'" % (result)
        cacmd_sql = ''
        if ca_cmd is not None:
            cacmd_sql = ",ca_cmd='%s'" % (ca_cmd)
        caret_sql = ''
        if ca_ret is not None:
            caret_sql = ",ca_ret='%s'" % (ca_ret)
        sql = "update %s set status='%s'%s%s%s,update_date=sysdate where sid=%d" % (q_table, status, result_sql, cacmd_sql, caret_sql, sid)
        ora.execone(sql)
        ora.commit()
        return 1
    except Exception, msg:
        print msg
        return -1

# 4120051539,7690316
#print send_cmd('getProduct', ('ALL_CHANNELS',))
#send_cmd('unpairChipSet', ('4120051539', '7690316', ))
#send_cmd('pairChipSet', ('4120051539', '7690316', ))
#send_cmd('createSector', ('4120051539','TW', 'YL', 'ALL_CHANNELS', ))
#print send_cmd('createEntitlements', ('4120051539','HBO99', ))
#print send_cmd('overwriteSector', ('4120051539','TW', 'YL', 'HBO99', ))
#print send_cmd('createEntitlements', ('4120051539', 'GROUP_9', ))
#print send_cmd('createParentalPinCode', ('4120051539', '2222'))
#close_http()
#sys.exit(0)

#querySQL = "SELECT sid,icc_no,stb_no,cmd,bg_date,end_date,channel,mail,tune,networkid,product_name,ppvdate from v_irdeto_queue_wait where icc_no not in ('4149924523','4256442579','4138310209','4126036616','4126026013','4126036573','4138304437','4149919297') and rownum<=30 %s" % (sosql)
querySQL = "SELECT sid,icc_no,stb_no,cmd,bg_date,end_date,channel,mail,tune,networkid,product_name,ppvdate from v_irdeto_queue_wait where rownum<=30 %s" % (sosql)

loop = 1
oracon = None
while 1:
    try:
        oracon = ORA('COSS@CNIS')
        if oracon is None:
            print "[Oracle Info]: Can't open database"+chr(10)
            time.sleep(10);
            continue
        try:
            rst = oracon.execall(querySQL)
        except Exception, detail:
            print "[Oracle Info]: Can't execute SQL"
            print detail
            pass
            oracon.se_close()
            oracon = None
            time.sleep(10)
            continue
        queue_flag = 0
        if rst is not None and len(rst)>0:
            queue_flag = 1
            for a_row in rst:
                tme = time.strftime("%Y/%m/%d %H-%M-%S", time.localtime())
                sid = int(a_row[0])
                icc_no = a_row[1]
                stb_no = a_row[2]
                cmd = a_row[3]
                bg_date = a_row[4]
                end_date = a_row[5]
                channel = a_row[6]
                mail = a_row[7]
                tune = a_row[8]
                networkid = a_row[9]
                prodname = a_row[10]
                ppvdate = a_row[11]
                print sid, icc_no, stb_no, cmd, channel
                sys.stdout.flush()
                if stb_no is None:
                    stb_no = '0'
                resp = ''

                if cmd=='A1':
                    cmd_str = 'pairChipSet'
                    status, resp = send_cmd('pairChipSet', (icc_no, stb_no,))
                    #if status=="OK":
                    send_cmd('createParentalPinCode', (icc_no, '0000'))
                    status, resp = send_cmd('overwriteSector', (icc_no, 'TW', 'YL', '',))
                elif cmd=='A2':
                    cmd_str = 'unpairChipSet'
                    status, resp = send_cmd('overwriteSector', (icc_no, 'TW', 'YL', '',))
                    if status=="OK":
                        status, resp = send_cmd('unpairChipSet', (icc_no, stb_no,))
                elif cmd=='B1':
                    cmd_str = 'createEntitlements'
                    status, resp = send_cmd('createEntitlements', (icc_no, '%s'%(channel)))
                elif cmd=='B2':
                    cmd_str = 'deleteEntitlements'
                    status, resp = send_cmd('deleteEntitlements', (icc_no, '%s'%(channel)))
                elif cmd=='E1':
                    cmd_str = 'createParentalPinCode'
                    status, resp = send_cmd('createParentalPinCode', (icc_no, '0000'))
                elif cmd=='E2':
                    cmd_str = 'overwriteParentalPinCode'
                    status, resp = send_cmd('overwriteParentalPinCode', (icc_no))
                elif cmd=='E6':
                    cmd_str = 'overwriteParentalPinCode'
                    status, resp = send_cmd('overwriteParentalPinCode', (icc_no))
                elif cmd=='E3':
                    cmd_str = 'sendMail'
                    mmsgs = utf8(mail)
                    msg = ""
                    for c in mmsgs:
                        msg = msg+"%.2X" % (ord(c))
                    status, resp = send_cmd('sendMail', (icc_no, msg, 'Raw'))
                elif cmd=='E8':
                    cmd_str = 'sendMessage'
                    mmsgs = utf8(mail)
                    msg = ""
                    for c in mmsgs:
                        msg = msg+"%.2X" % (ord(c))
                    status, resp = send_cmd('sendMessage', (icc_no, msg, 'Raw'))
                elif cmd=='E7':
                    cmd_str = 'sendMailGlobal'
                    mmsgs = utf8(mail)
                    msg = ""
                    for c in mmsgs:
                        msg = msg+"%.2X" % (ord(c))
                    status, resp = send_cmd('sendMailGlobal', (msg, 'Raw'))
                elif cmd=='E9':
                    cmd_str = 'sendMessageGlobal'
                    mmsgs = utf8(mail)
                    msg = ""
                    for c in mmsgs:
                        msg = msg+"%.2X" % (ord(c))
                    status, resp = send_cmd('sendMessageGlobal', (msg, 'Raw'))
                elif cmd=='V1':
                    cmd_str = 'sendMessage'
                    cmdmsg = "__TFM-PVR-PREFIX-SWITCH__||ON||%s" % (prodname)
                    mmsgs = utf8(cmdmsg)
                    msg = ""
                    for c in mmsgs:
                        msg = msg+"%.2X" % (ord(c))
                    status, resp = send_cmd('sendMessage', (icc_no, msg, 'Raw'))
                elif cmd=='V9':
                    cmd_str = 'sendMessage'
                    cmdmsg = "__TFM-PVR-PREFIX-SWITCH__||OFF||%s" % (prodname)
                    mmsgs = utf8(cmdmsg)
                    msg = ""
                    for c in mmsgs:
                        msg = msg+"%.2X" % (ord(c))
                    status, resp = send_cmd('sendMessage', (icc_no, msg, 'Raw'))
                elif cmd=='V10': # Time-Shift on
                    cmd_str = 'sendMessage'
                    cmdmsg = "__TFM-CONTROL-LIVE-TV-PREFIX-SWITCH__||ON||%s" % (prodname)
                    mmsgs = utf8(cmdmsg)
                    msg = ""
                    for c in mmsgs:
                        msg = msg+"%.2X" % (ord(c))
                    status, resp = send_cmd('sendMessage', (icc_no, msg, 'Raw'))
                elif cmd=='V11': # Time-Shift off
                    cmd_str = 'sendMessage'
                    cmdmsg = "__TFM-CONTROL-LIVE-TV-PREFIX-SWITCH__||OFF||%s" % (prodname)
                    mmsgs = utf8(cmdmsg)
                    msg = ""
                    for c in mmsgs:
                        msg = msg+"%.2X" % (ord(c))
                    status, resp = send_cmd('sendMessage', (icc_no, msg, 'Raw'))
                else:
                    cmd_str = cmd
                    print '[Error]: %s, %d' % (resp, sid)
                    sys.stdout.flush()
                    ora_upd(oracon, sid, 'ERROR', 'FAIL', cmd_str, "Unknown command %s"%(cmd))
                    continue
                ora_upd(oracon, sid, status, 'NORMAL', cmd_str, resp)
                sys.stdout.flush()

        oracon.se_close()
        oracon = None
        close_http()
        if queue_flag==1:
            time.sleep(3)
        else:
            time.sleep(15)
        loop = loop+1
    except Exception, detail:
        print "Exception: %s" % (detail)
        pass
        close_http()
        if oracon is not None:
            try:
                oracon.se_close()
            except:
                pass
            oracon = None
        continue

sys.exit()
