#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# 10.22.128.11 : 60002
import os,sys,time,socket,select
from oraclass import ORA
from ca_func import CA_FUNC

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

sourceid = 20

oracon = None
oracon = ORA('coss@cnis')
if oracon.db is None:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] ERROR: Unable to connect to DB [CNIS]'
    sys.exit(0)

init_seq = -1
sql = "select seq from cagw_seq where sourceid='%d'" % (sourceid)
rst = oracon.execall(sql)
if rst is not None and len(rst) > 0:
    for a_row in rst:
        init_seq = a_row[0]
oracon.se_close()

if init_seq<0:
    init_seq = 900000000

print "init seq: %.9d" % (init_seq)

xca_cmd = ''
xca_ret = ''
cafunc = CA_FUNC(sourceid, 'emm', init_seq)
recv_buffer_length = 40960

def gw_open(host, port=60002):
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
        return None
    try:
        buf = tn.recv(recv_buffer_length)
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

def ora_upd(ora, p_nuid, p_status, p_iccno=None):
    try:
        if p_iccno is not None:
            sql = "update ca_dta set status='%s',iccno='%s',updatetime=sysdate where nuid='%s'" % (p_status, p_iccno, p_nuid)
        else:
            sql = "update ca_dta set status='%s',updatetime=sysdate where nuid='%s'" % (p_status, p_nuid)
        #print sql
        ora.execone(sql)
        return 1
    except Exception, msg:
        print "[ORA_UPD Error]: %s" % (msg)
        return -1

def main():
    global sourceid
    oracon = None
    sock = None
    nop_flag = 0
    querySql = "SELECT ltrim(to_char(round(dbms_random.value(1,10000000)),'0999999')) sid,nuid,to_char(sysdate-(1/3),'yyyymmdd') d1,to_char(sysdate+3650,'yyyymmdd') d2 from ca_dta where status='INIT' and createtime >= sysdate-2 and rownum<=30 and nuid !='0B0007041645'"
    try:
        nowdate = time.strftime("%Y%m%d", time.localtime())
        while 1:
            try:
                data_flag = 0
                if nop_flag>0:
                    nop_flag = 0
                if sock is None:
                    sock = gw_open("10.22.128.11", 60002)
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
                if oracon is None:
                    oracon = ORA('coss@cnis')
                rs = None
                if oracon.cexist():
                    try:
                        rs = oracon.execall(querySql)
                    except Exception, msg:
                        print querySql
                        print 'querySQL: '+str(msg)
                        oracon.se_close()
                        oracon = None
                        time.sleep(2)
                        continue

                    if rs is not None and len(rs) > 0:
                        print "%s cnt=%d" %(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()), len(rs))
                        data_flag = 1
                        for a_row in rs:
                            try:
                                sid = a_row[0]
                                nuid = a_row[1]
                                bg_date = a_row[2]
                                end_date = a_row[3]
                                resp = cafunc.gw_sync_icc(sid, bg_date, end_date, nuid)
                                if resp<0:
                                    print '[Error]: %d, %s' % (resp, nuid)
                                    ora_upd(oracon, nuid, 'ERROR')
                                print "%s %s %s %s %s" %(sid, nuid, bg_date, end_date, time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
                            except Exception, msg:
                                print "ERROR : "+str(msg)
                                ora_upd(oracon, nuid, 'ERROR')
                            sys.stdout.flush()

                        # Sending commands to CA Gateway
                        oracon.commit()
                        print "%s Sending commands to CA Gateway" %(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
                        sys.stdout.flush()
                        x, y, z, idx, key = cafunc.seek_q(1)
                        while x is not None:
                            try:
                                nop_flag = 1
                                print y
                                if gw_send(sock, y)>0:
                                    cafunc.upd_q(idx, 2)
                                else:
                                    sock.close()
                                    sock = None
                                    time.sleep(2)
                                    break
                                x, y, z, idx, key = cafunc.seek_q(1)
                                time.sleep(0.1)
                            except Exception, msg:
                                print msg
                                if sock:
                                    try:
                                        sock.close()
                                        sock = None
                                    except:
                                        pass
                                    break
                            sys.stdout.flush()
                        oracon.commit()
                    else:
                        print ".",
                else:
                    print "%s Reconnect" % time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                sys.stdout.flush()

                # recieving commands from CA Gateway
                recv_str = gw_read(sock)
                if recv_str is not None and recv_str!='ERROR':
                    maxlen = len(recv_str)
                    nop_flag = 1
                    ofs = 0
                    while ofs<maxlen:
                        xlen = ord(recv_str[ofs+1])
                        x = recv_str[ofs+2:ofs+2+xlen]
                        print x
                        sid = x[36:45]
                        p_iccno = x[45:]
                        idx = cafunc.mapping_idx(sid)
                        cafunc.rcv_q(idx, p_iccno)
                        cafunc.upd_q(idx, 3)
                        ofs = ofs+xlen+2
                elif recv_str=='ERROR':
                    print "Reading error...."+str(recv_str)
                    time.sleep(2)
                    oracon.se_close()
                    oracon = None
                    sock.close()
                    sock = None
                    continue
                else:
                    pass
                #cafunc.print_q()
                # Update Result
                x, y, z, idx, key = cafunc.seek_q(-1)
                x, y, z, idx, key = cafunc.seek_q(3)
                while x is not None:
                    try:
                        nop_flag = 1
                        print "%s, %d> %s" % (x, idx, z)
                        sys.stdout.flush()
                        cafunc.upd_q(idx, 0)
                        p_iccno = z[:10]
                        p_nuid = z[10:]
                        print p_iccno, p_nuid
                        if ora_upd(oracon, p_nuid, 'OK', p_iccno)<0:
                            oracon.se_close()
                            oracon = None
                            break
                        x, y, z, idx, key = cafunc.seek_q(3)
                    except Exception, msg:
                        print msg
                        if sock:
                            try:
                                sock.close()
                                sock = None
                            except:
                                pass
                            break
                    sys.stdout.flush()

                if nop_flag==0:
                    x, y, z, idx, key = cafunc.seek_q(-1)
                    x, y, z, idx, key = cafunc.seek_q(1)
                    if x is not None:
                        nop_flag = 1
                    else:
                        x, y, z, idx, key = cafunc.seek_q(-1)
                        x, y, z, idx, key = cafunc.seek_q(2)
                        if x is not None:
                            nop_flag = 1
                        else:
                            x, y, z, idx, key = cafunc.seek_q(-1)
                            x, y, z, idx, key = cafunc.seek_q(3)
                            if x is not None:
                                nop_flag = 1

                if nop_flag<=0:
                    nop_flag = nop_flag-1
                if nop_flag<=-10:
                    print "[Keep-alive]"
                    cmdstr = cafunc.gw_keepalive(nowdate)
                    if gw_send(sock, cmdstr)<0:
                        sock.close()
                        sock = None
                        time.sleep(2)
                    else:
                        read_str = None
                        loop = 0
                        while (read_str is None or read_str=='ERROR') and loop<30:
                            read_str = gw_read(sock)
                            time.sleep(1)
                            loop = loop+1
                        if loop>=30:
                            sock.close()
                            sock = None
                        nop_flag = 0
                        time.sleep(5)

                if data_flag==0:
                    oracon.se_close()
                    oracon = None
                    time.sleep(15)
                else:
                    sql = "update cagw_seq set seq='%d' where sourceid=%d" % (cafunc.seqid, sourceid)
                    oracon.execone(sql)
                    oracon.commit()
                    oracon.se_close()
                    oracon = None
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
                time.sleep(5)
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
