#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# 10.22.111.11 : 60002
import os,sys,time,string,socket,select
from oraclass import ORA
from cagw_func import CAGW_FUNC

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv) != 2:
    print 'usage:',sys.argv[0],'SourceID'
    sys.exit(0)

try:
    sourceid = int(sys.argv[1])
except:
    sourceid = 0



oracon = None
oracon = ORA('coss@kbro_nmsdb')
if oracon.db is None:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] ERROR: Unable to connect to DB [KBRO_NMSDB]'
    sys.exit(0)

init_seq = -1
sql = "select seq from cagw_seq where sourceid='%d'" % (sourceid)
rst = oracon.execall(sql)
if rst is not None and len(rst) > 0:
    for a_row in rst:
        init_seq = a_row[0]
oracon.se_close()

if init_seq<0:
    init_seq = 800000000

print "init seq: %.9d" % (init_seq)


xca_cmd = ''
xca_ret = ''
cafunc = CAGW_FUNC(sourceid, 'emm', init_seq)
recv_buffer_length = 40960

def gw_open(host, port=59001):
    msg = "getaddrinfo returns an empty list"
    for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            sock = socket.socket(af, socktype, proto)
            sock.connect(sa)
        except socket.error, msg:
            if sock:
                sock.close()
            sock = None
            print "gw_open() error: %s" % (str(msg))
            time.sleep(5)
            continue
        break
    if not sock:
        raise socket.error, msg
    return sock

def gw_read(tn):
    buf = None
    r, w, e = select.select([tn], [], [], 0.5)
    if r == []:
        #tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        #print "[%s]: Socket read timeout..." % (tme)
        return None
    try:
        buf = tn.recv(recv_buffer_length)
        #cafunc.prn_data(buf)
    except Exception, msg:
        print 'gw_read(): '+str(msg)
        return 'ERROR'
    return buf

def gw_send(tn, s):
    try:
        buf = chr(0)+chr(len(s))+s
        tn.send(buf)
        #cafunc.prn_data(buf)
    except Exception, msg:
        print 'gw_send(): '+msg
        return -1
    return 1

def login(tn):
    obname = "KBRO_CAGWD3"
    buf = chr(0)+chr(len(obname)+2)+chr(0x0)+chr(0xb)+obname
    tn.send(buf)
    #cafunc.prn_data(buf)
    rst = gw_read(tn)

    loop = 0
    while rst is None and loop<30:
        time.sleep(1)
        rst = gw_read(tn)
        loop = loop+1
    print rst
    if rst is not None and rst[2]==chr(0x06):
        rst = gw_read(tn)
        print rst
        loop = 0
        while rst is None and loop<30:
            time.sleep(1)
            rst = gw_read(tn)
            loop = loop+1
        if rst is not None and rst[2]==chr(0x0):
            return 1
    elif rst=='ERROR':
        return -1
    return -1



def main():
    global sourceid
    oracon = None
    sock = None
    nop_flag = 0
    i = 0
    try:
        nowdate = time.strftime("%Y%m%d", time.localtime())
        print 'sock:',sock
        while i < 2:
            try:
                data_flag = 0
                if nop_flag>0:
                    nop_flag = 0
                if sock is None:
                    sock = gw_open("10.22.111.11",60002)
                    if sock is None:
                        print 'Socket create error'
                        time.sleep(5)
                        continue
                    if login(sock)<=0:
                        print 'Login to CA error'
                        sock.close()
                        sock = None
                        time.sleep(5)
                        continue
                
                else:
                    print "%s Reconnect" % time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                sys.stdout.flush()

                
            except Exception, msg:
                print 'Error: '+str(msg)
                try:
                    oracon.se_close()
                except:
                    pass
                oracon = None
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                    sock = None
                time.sleep(15)
            i = i+1
        if oracon:
            oracon.se_close()
            oracon = None
        if sock:
            sock.close()
            sock = None
    except KeyboardInterrupt:
        if oracon:
            oracon.se_close()
        if sock:
            sock.close();
        print "Interrupt...\n"
        exit

if __name__ == "__main__":
    main()
