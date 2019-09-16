#!/usr/bin/env python
# -*- coding: Big5 -*- 
import time,sys,string,binascii
import socket,telnetlib,select
from oraclass import ORA
from cagw_func import CAGW_FUNC

sosql = ""
sourceid = 3 
q_table = 'cagw_queue_d3_lab'

querySql = "SELECT ltrim(to_char(sid,'0999999')) sid,icc_no,stb_no,cmd,decode(bg_date,null,to_char(sysdate,'yyyymmdd'), \
            to_char(bg_date,'yyyymmdd')) bg_date,decode(end_date,null,to_char(sysdate+900,'yyyymmdd'), \
            to_char(end_date,'yyyymmdd')) end_date,decode(channel,null,'0',channel) channel,mail,tune,networkid,product_name,to_char(sysdate+1,'yyyymmdd') ppvdate \
            from %s where icc_no is not null and status is null and cmd not in ('E3','E7') %s and (active_time is null or sysdate>=active_time) order by substr(cmd,1,1),sid" % (q_table, sosql)

xca_cmd = ''
xca_ret = ''
cafunc = CAGW_FUNC(sourceid, 'emm', 1)
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
        #cafunc.prn_data(buf)
    except Exception, msg:
        print msg
        return None
    return buf
    
def gw_send(tn, s):
    try:
        buf = chr(0)+chr(len(s))+s
        tn.send(buf)
        #cafunc.prn_data(buf)
    except Exception, msg:
        print msg
        return -1
    return 1

def login(tn):
  obname = "KBRO_CAGWD3"
  buf = chr(0)+chr(len(obname)+2)+chr(0x0)+chr(0xb)+obname
  tn.send(buf)
  #cafunc.prn_data(buf)
  rst = gw_read(tn)
  while rst is None:
      time.sleep(1)
      rst = gw_read(tn)
  if rst[2]==chr(0x06):
      rst = gw_read(tn)
      while rst is None:
          time.sleep(1)
          rst = gw_read(tn)
      if rst[2]==chr(0x0):
          return 1
  return -1
  
def ora_upd(ora, sid, status, result=None, ca_cmd=None, ca_ret=None):
    try:
        result_sql = ''
        if result is not None:
            result_sql = ",result='%s'" % (result)
        cacmd_sql = ''
        if ca_cmd is not None:
            cacmd_sql = ",ca_cmd='%s'" % (ca_cmd)
        caret_sql = ''
        if ca_ret is not None:
            caret_sql = ",ca_ret='%s'" % (ca_ret)
        sql = "update %s set status='%s'%s%s%s,update_date=sysdate where sid=%d" % (q_table, status, result_sql, cacmd_sql, caret_sql, int(sid))
        ora.execone(sql)
        ora.commit()
    except Exception, msg:
        print msg

def main():
   oracon = None
   sock = None
   nop_flag = 0
   try:
     nowdate = time.strftime("%Y%m%d", time.localtime())
     while 1:
           if nop_flag>0:
               nop_flag = 0
           if sock is None:
               sock = gw_open("10.20.51.11",60002)
               if sock is None:
                   time.sleep(5)
                   continue
               if login(sock)<=0:
                   sock.close()
                   sock = None
                   time.sleep(5)
                   continue
           if oracon is None:
               oracon = ORA('coss/coss@nmsdb')
           rs = None
           if oracon.cexist():
               rs = oracon.execall(querySql)
               if rs is not None and len(rs) > 0:
                   print "%s cnt=%d" %(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()), len(rs))
                   for a_row in rs:
                       sid = a_row[0]
                       icc_no = a_row[1]
                       stb_no = a_row[2]
                       cmd = a_row[3]
                       bg_date = a_row[4]
                       end_date = a_row[5]
                       mail = a_row[7]
                       tune = a_row[8]
                       networkid = a_row[9]
                       prodname = a_row[10]
                       ppvdate = a_row[11]
                       if stb_no is None:
                           stb_no = '0000000000'
                       channel = "%.12d" % int(a_row[6])
                       if cmd=='A1':
                          resp = cafunc.gw_add_icc(sid, ppvdate, end_date, icc_no, stb_no)
                       elif cmd=='A2':
                          resp = cafunc.gw_cancel_icc(sid, bg_date, end_date, icc_no)
                       elif cmd=='B1':
                          resp = cafunc.gw_add_prod(sid, bg_date, end_date, icc_no, channel)
                       elif cmd=='B2':
                          resp = cafunc.gw_cancel_prod(sid, bg_date, end_date, icc_no, channel)
                       elif cmd=='B7':
                          resp = cafunc.gw_add_prod_7days(sid, bg_date, end_date, icc_no, channel)
                       elif cmd=='B8':
                          resp = cafunc.gw_add_prod_62days(sid, bg_date, end_date, icc_no, channel)
                       elif cmd=='E1':
                          resp = cafunc.gw_chgpwd(sid, bg_date, end_date, icc_no)
                       elif cmd=='E2':
                          resp = cafunc.gw_resetpwd(sid, bg_date, end_date, icc_no)
                       elif cmd=='E3':
                          resp = cafunc.gw_mail(sid, bg_date, end_date, icc_no, mail, 0)
                       elif cmd=='E4':
                          resp = cafunc.gw_forcetune(sid, bg_date, end_date, icc_no, tune)
                       elif cmd=='E5':
                          resp = cafunc.gw_networkid(sid, bg_date, end_date, icc_no, networkid)
                       elif cmd=='E6':
                          resp = cafunc.gw_resetpincode(sid, bg_date, end_date, icc_no)
                       elif cmd=='E7':
                          resp = cafunc.gw_mail(sid, bg_date, end_date, icc_no, mail, 1)
                       elif cmd=='P1':
                          resp = cafunc.gw_setcredit(sid, ppvdate, end_date, icc_no, channel)
                       elif cmd=='P2':
                          resp = cafunc.gw_resetcredit(sid, bg_date, end_date, icc_no, channel)
                       elif cmd=='P3':
                          resp = cafunc.gw_seteventprod(sid, bg_date, end_date, icc_no, channel, prodname, tune)
                       elif cmd=='P4':
                          resp = cafunc.gw_suspend_ippv(sid, ppvdate, end_date, icc_no)
                       elif cmd=='P5':
                          resp = cafunc.gw_immediate_callback(sid, ppvdate, end_date, icc_no)
                       elif cmd=='P6':
                          resp = cafunc.gw_resume_ippv(sid, bg_date, end_date, icc_no)
                       elif cmd=='P7':
                          resp = cafunc.gw_get_product(sid, bg_date, end_date, icc_no)
                       elif cmd=='P8':
                          resp = cafunc.gw_upd_ippvthreshold(sid, bg_date, end_date, icc_no, tune)
                       elif cmd=='P9':
                          resp = cafunc.gw_cmd_pincode(sid, bg_date, end_date, icc_no)
                       elif cmd=='P10':
                          resp = cafunc.gw_cmd_setcallback_date(sid, ppvdate, end_date, icc_no)
                       elif cmd=='V1':
                          resp = cafunc.gw_PVR_pair_hd(sid, bg_date, end_date, icc_no, prodname)
                       elif cmd=='V2':
                          resp = cafunc.gw_PVR_pair_any(sid, bg_date, end_date, icc_no)
                       elif cmd=='V3':
                          resp = cafunc.gw_PVR_hd_storage(sid, bg_date, end_date, icc_no, tune)
                       elif cmd=='V4':
                          resp = cafunc.gw_PVR_factory_reset(sid, bg_date, end_date, icc_no)
                       elif cmd=='V5':
                          resp = cafunc.gw_PVR_OTA_force(sid, bg_date, end_date, icc_no)
                       elif cmd=='V6':
                          resp = cafunc.gw_PVR_OTA_interactive(sid, bg_date, end_date, icc_no)
                       else:
                          resp = -2
                       if resp<0:
                           print '[Error]: %s, %d, %s' % (cmd, resp, sid)
                       sys.stdout.flush() 
                          
                   # Sending commands to CA Gateway
                   x, y, z, idx, key = cafunc.seek_q(1)
                   while x is not None:
                       try:
                           nop_flag = 1
                           print y
                           if gw_send(sock, y)>0:
                               cafunc.upd_q(idx, 2)
                               ora_upd(oracon, key, 'SENT', None, y)
                           x, y, z, idx, key = cafunc.seek_q(1)
                           time.sleep(0.1)
                       except Exception, msg:
                           print msg
                           pass
                       sys.stdout.flush() 
               else:
                 pass
           else:
               print "%s Reconnect" % time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
           sys.stdout.flush()
           
           # recieving commands from CA Gateway
           recv_str = gw_read(sock)
           if recv_str is not None:
               maxlen = len(recv_str)
               nop_flag = 1
               ofs = 0
               while ofs<maxlen:
                   xlen = ord(recv_str[ofs+1])
                   x = recv_str[ofs+2:ofs+2+xlen]
                   sid = x[36:45]
                   idx = cafunc.mapping_idx(sid)
                   cafunc.rcv_q(idx, x)
                   cafunc.upd_q(idx, 3)
                   ofs = ofs+xlen+2
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
                   result_str = cafunc.gw_msg(z)
                   ora_upd(oracon, key, 'OK', result_str, None, z)
                   x, y, z, idx, key = cafunc.seek_q(3)
               except Exception, msg:
                   print msg
               sys.stdout.flush() 
           oracon.se_close()
           oracon = None
           
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
               cmdstr = cafunc.gw_keepalive(nowdate)
               gw_send(sock, cmdstr)
               read_str = None
               while read_str is None:
                   read_str = gw_read(sock)
                   time.sleep(1)
                   pass
               nop_flag = 0
               time.sleep(5)
           sys.stdout.flush()
           time.sleep(2)
     oracon.se_close()
     if sock:
         sock.close()
   except KeyboardInterrupt:
     oracon.se_close()
     sock.close();
     print "Interrupt...\n"
     exit

if __name__ == "__main__":
   main()

