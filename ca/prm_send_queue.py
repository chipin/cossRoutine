#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# 10.21.128.11 : 60002
import os,sys,time,string,socket,select
from oraclass import ORA
from prm_func import CA_FUNC

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'


sourceid = 17
oracon = None
oracon = ORA('coss@cnis')
if oracon.db is None:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print '['+nowdate+'] ERROR: Unable to connect to DB [CNIS]'
    sys.exit(0)


model_mapping = {}
model_mapping['7584'] = '0801 000E 0805 0007 00'
model_mapping['7141'] = '0D01 0001 0D05 0000 00'
model_mapping['7019c'] = '0801 0008 0805 0001 00'
model_mapping['7019z'] = '0801 000C 0805 0005 00'
model_mapping['72604'] = '0801 000E 0805 0007 00'


xca_cmd = ''
xca_ret = ''
init_seq = 1
cafunc = CA_FUNC(sourceid, 'emm', init_seq)
recv_buffer_length = 40960

def gw_open(host, port=60004):
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

def ora_upd(ora, sid, status, result=None, ca_cmd=None, ca_ret=None):
    try:
        if result is not None:
            result = string.replace(result, "'","*")
        result_sql = ''
        if result is not None:
            result_sql = ",send_result= send_result || ' %s'" % (result)
        sql = "update prm_queue set send_status='%s'%s,update_date=sysdate where sid=%d" % (status, result_sql, int(sid))
        print sql
        ora.execone(sql)
        return 1
    except Exception, msg:
        print msg
        return -1
        


def main():
    global sourceid
    oracon = None
    sock = None
    sock_dlk = None
    sock_d3 = None
    ca_sock = None
    nop_flag = 0
    result_id = None
    ca_sys = None
    recv_str = None
    #querySql = "select ltrim(to_char(sid,'099999999')) sid,nuid,old_nuid,stb_no,old_stb_no,model,old_model,status,to_char(create_date -8/24,'YYYYMMDD') create_date,result,icc_no from prm_queue where send_status = 'INIT' and status = 'OK' "
    querySql = "select ltrim(to_char(a.sid,'099999999')) sid,a.nuid,a.old_nuid,a.stb_no,a.old_stb_no,a.model,a.old_model,a.status,to_char(a.create_date -8/24,'YYYYMMDD') create_date,a.result,a.icc_no from prm_queue a \
                where a.send_status = 'INIT' and a.status = 'OK' and rownum < 2 "
    print querySql
    #querySql = "SELECT ltrim(to_char(round(dbms_random.value(1,10000000)),'0999999')) sid,nuid,to_char(sysdate-(1/3),'yyyymmdd') d1,to_char(sysdate+3650,'yyyymmdd') d2 from ca_dta where status='INIT' and createtime >= sysdate-1 and rownum<=30"
    try:
        nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print nowdate
        x = ''
        while 1:
            try:
                data_flag = 0
                if nop_flag>0:
                    nop_flag = 0
                if sock_dlk is None:
                    sock_dlk = gw_open("10.22.128.11", 60002)
                    if sock_dlk is None:
                        print '[DLK] Socket create error'
                        time.sleep(5)
                        continue
                    if login(sock_dlk)<=0:
                        print '[DLK] Login to CA error'
                        sock_dlk.close()
                        sock_dlk = None
                        time.sleep(5)
                        continue
                        
                if sock_d3 is None:
                    sock_d3 = gw_open("10.22.111.11",60002)
                    if sock_d3 is None:
                        print '[D3] Socket create error'
                        time.sleep(5)
                        continue
                    if login(sock_d3)<=0:
                        print '[D3] Login to CA error'
                        sock_d3.close()
                        sock_d3 = None
                        time.sleep(5)
                        continue
                if oracon is None:
                    oracon = ORA('coss@cnis')
                rs = None
                res1 = None
                res2 = None
                res3 = None
                res4 = None
                if oracon.cexist():
                    try:
                        rs = oracon.execall(querySql)
                        #print '['+nowdate+']'+querySql
                    except Exception, msg:
                        print querySql
                        print 'querySQL: '+str(msg)
                        oracon.se_close()
                        oracon = None
                        time.sleep(2)
                        continue

                    if rs is not None and len(rs) > 0:
                        #print "%s cnt=%d" %(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()), len(rs))
                        data_flag = 1
                        for a_row in rs:
                            try:
                                sid = a_row[0]
                                nuid = a_row[1]
                                old_nuid = a_row[2]
                                stb_no = a_row[3]
                                old_stb_no = a_row[4]
                                model = model_mapping[a_row[5]]
                                old_model = model_mapping[a_row[6]]
                                create_date = a_row[8]
                                lci_result = a_row[9]
                                icc_no = a_row[10]
                                
                                #key_content = lci_result[52:]
                                key_content = lci_result
                                key1 = key_content[0:82]
                                key2 = key_content[82:164]
                                key3 = key_content[164:246]
                                key4 = key_content[246:]  
                                key4 = "%s00000000000000000000000000000000" %(key4)
                                
                                res1 = cafunc.prm_set_comm(sid, 0, stb_no, key1, icc_no)
                                res2 = cafunc.prm_set_comm(sid, 1, stb_no, key2, icc_no)
                                res3 = cafunc.prm_set_comm(sid, 2, stb_no, key3, icc_no)
                                res4 = cafunc.prm_set_comm(sid, 3, stb_no, key4, icc_no)
                                
                                print 'send_IRD1:',stb_no,'-',res1
                                print 'send_IRD2:',stb_no,'-',res2
                                print 'send_IRD3:',stb_no,'-',res3
                                print 'send_IRD4:',stb_no,'-',res4
                                #print "%s %s %s %s %s %s" %( nuid, old_nuid, stb_no, old_stb_no, model,old_model)
                            except Exception, msg:
                                print "ERROR : "+str(msg)
                                ora_upd(oracon, sid, 'ERROR')

                            sys.stdout.flush()
                        if icc_no is not None:
                          iccs = icc_no[:10]
                          SQL = "select sys,queue from ca_sc_range where %s between sc_begin and sc_end" % (iccs)
                          print SQL
                          rs = oracon.execall(SQL)
                          if rs is not None and len(rs) > 0:
                            for b_row in rs:
                              try:
                                ca_sys = b_row[0]
                                
                              except Exception, msg:
                                print "ERROR : "+str(msg)
                                ora_upd(oracon, sid, 'ERROR')
                          else:
                            print "ERROR : 智慧卡號不在定義範圍"
                            ora_upd(oracon, sid, 'ERROR','智慧卡號不在定義範圍');
                            
                        # Sending commands to CA Gateway
                        oracon.commit()
                        print 'ca_sys',ca_sys
                        if ca_sys is not None:
                          if ca_sys == 'D3':
                            sock = sock_d3
                          else:
                            sock = sock_dlk
                        
                        print "%s Sending commands to CA Gateway %s" %(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()), sock)
                        sys.stdout.flush()
                        x, y, z, idx, key = cafunc.seek_q(1)
                        while x is not None:
                            try:
                                nop_flag = 1
                                
                                if gw_send(sock, y)>0:
                                    cafunc.upd_q(idx, 2)
                                else:
                                    sock_dlk.close()
                                    sock_dlk = None
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
                        #print ".",
                        pass
                else:
                    print "%s Reconnect" % time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                sys.stdout.flush()
                
                if sock is not None:
                  recv_str = gw_read(sock)
                #print 'response',recv_str
                if recv_str is not None and recv_str!='ERROR':
                    maxlen = len(recv_str)
                    nop_flag = 1
                    ofs = 0
                    while ofs<maxlen:
                        xlen = ord(recv_str[ofs+1])
                        
                        x = recv_str[ofs+2:ofs+2+xlen]
                        result_code = x[32:36]
                        if result_code == '1000':
                          ora_upd(oracon, sid, 'OK', x)
                        else:
                          ora_upd(oracon, sid, 'ERROR', x)
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
                oracon.commit()
                
            except Exception, msg:
                print 'Error111: '+str(msg)
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
        oracon.se_close()
        oracon = None
        if sock:
            sock.close()
            sock = None
        time.sleep(10)
    except KeyboardInterrupt:
        if oracon:
            oracon.se_close()
        if sock:
            sock.close();
        print "Interrupt...\n"
        exit

if __name__ == "__main__":
    main()
