#!/usr/bin/env python
# -*- coding: big5 -*-
import sys, re, os, time
import urllib
import httplib

target = '0935864096'
msg = '10181銀行授權'

# 客服
auth_str = "username=VCSA003300&password=6864959499&rateplan=A&srcaddr=8707342"

sport = 18994
stype = 'BIG5'
status = 'ERROR'
result = 'Exception'
smbody = ''
smslen = smscnt = 0
twmid = twmcnt = 0
try:
    msg = msg.replace('#','-')
    msg = msg.replace('<','(')
    msg = msg.replace('>',')')
    smslen = len(msg.decode('big5'))

    if smslen <= 0 or smslen > (67*5):
        print 'ERROR: msg length incorrect'
    elif smslen > 70 and smslen <= (67*5): # 長簡訊
        smscnt = int(smslen/67)
        if smslen%67 > 0:
            smscnt = smscnt+1
        stype = 'LBIG5'
        sport = 18995

        for cnt in range(0, smscnt):
            submsg = msg.decode('big5')[cnt*67:(cnt+1)*67].encode('big5')
            header = "%%05%%00%%03%%C7%%%02d%%%02d" % (smscnt, cnt+1)
            smbody = "%s%s%s" % (smbody, header, urllib.quote(submsg))
            #print header,submsg,smbody
    else: # 短簡訊
        smbody = urllib.quote(msg)
except Exception, detail:
    print "Exception: %s" % (detail)

if len(smbody) > 0 and smslen > 0:
    try:
        rurl = 'http://123.0.63.47/GW/sms/sms_callback.php'
        rurl = urllib.quote(rurl)
        durl = "/send.cgi?%s&dstaddr=%s&encoding=%s&smbody=%s&response=%s" % (auth_str, target, stype, smbody, rurl)
        print durl

        twmdata = None
        server = "bizsms.taiwanmobile.com:%d" % (sport)
        twmconn = httplib.HTTPConnection(server)
        twmconn.connect()
        twmconn.request('POST', durl)
        twmresp = twmconn.getresponse()
        twmdata = twmresp.read()
        twmresp.close()
        twmconn.close()

        print twmdata

    except Exception, detail:
        print "Exception: %s" % (detail)

