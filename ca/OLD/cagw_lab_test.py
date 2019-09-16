#!/usr/bin/env python
# -*- coding: big5 -*-
import time,sys,string,binascii
import socket,telnetlib,codecs
from oraclass import ORA
sms_table = "cagw_queue_lab"
querySql = "SELECT ltrim(to_char(sid,'09999999')) sid,icc_no,stb_no,cmd,decode(bg_date,null,to_char(sysdate,'yyyymmdd'), \
            to_char(bg_date,'yyyymmdd')) bg_date,decode(end_date,null,to_char(sysdate+900,'yyyymmdd'), \
            to_char(end_date,'yyyymmdd')) end_date,decode(channel,null,'0',channel) channel,mail,tune,networkid \
            from cagw_queue_lab where status is null order by sid"
updateSql = "UPDATE cagw_queue_lab SET status = :1, result=:2, update_date=sysdate,ca_cmd=:3,ca_ret=:4 where sid=:5"

xca_cmd = ''
xca_ret = ''
xca_mailid = int(time.time() % 1023)

if len(sys.argv)<2:
    hostip = '10.20.111.11';
else:
    hostip = sys.argv[1]

def prn_data(d):
  k = 0;  
  print d[2:] 
  return
  while k<len(d):
    pp = ""
    i = 0
    while i<16:
      if k+i>=len(d):
        j = k+i
        while j<k+16:
          print "  ",
          j = j+1
        break
      pp = d[k+i]
      vs = binascii.hexlify(pp)
      print vs,
      i = i+1
    print " - ",
    pp = ""
    i = 0
    while i<16:
      if k+i>=len(d): break
      pp = d[k+i]
      if pp in (string.digits+string.letters+string.punctuation):
        print pp,
      else:
        print "?",
      i = i+1
    print ""
    k = k+16
  print ""

sock = None

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
                continue
            break
        if not sock:
            raise socket.error, msg
        return sock

def gw_read(tn, timeout=10):
    global xca_ret
    buf = ''
    socket.setdefaulttimeout(timeout)
    while 1:
      try:
        buf = tn.recv(256)
        if len(buf)>0:
          break
      except Exception, msg:
        print msg
        tn.close()
        sys.exit(0)
    prn_data(buf)
    xca_ret = buf[2:]
    return buf

def login(tn):
  obname = "KBRO_CAGWD3"
  buf = chr(0)+chr(len(obname)+2)+chr(0x0)+chr(0xb)+obname
  tn.send(buf)
  prn_data(buf)
  rst = gw_read(tn)
  if rst[2]==chr(0x06):
    rst = gw_read(tn)
    if rst[2]==chr(0x0):
      return 1
  return -1

def gw_combo(seq,sid, bgd, endd, icc, cmd):
    str = seq+sid+'010006025744289'+bgd+'N'+bgd+endd+'U'+icc+cmd
    return str 

def gw_msg(s):
    xid = s[2:11]
    type = s[11:13]
    src_id = s[13:17]
    dst_id = s[17:21]
    ppid = s[21:26]
    sdate = s[26:34]
    cmd = s[34:38]
    print xid,type,src_id,dst_id,ppid,sdate,',CMD:'+cmd
    if cmd=='1000':
        sid = s[38:47]
        ims_pid = s[47:59]
        sms_pid = s[59:71]
        print xid,type,src_id,dst_id,ppid,sdate,',CMD:'+cmd+'SID:'+sid+',',ims_pid,sms_pid
        return 'OK'
    elif cmd=='1001':
        sid = s[38:47]
        nack = s[47:48]
        error = s[48:52]
        error_ext = s[52:56]
        cmd_len = s[56:59]
        cmd_sec = s[59:]
        print xid,type,src_id,dst_id,ppid,sdate,',CMD:'+cmd+'SID:'+sid+',',nack,error,error_ext,cmd_len,cmd_sec
        return 'ERROR:'+error
    elif cmd=='1002':
        print '1002 No command'
    else:
        print 'Unknown'
    return 'SYSTEM ERROR'

def gw_sendcmd(tn, cmd):
    global xca_cmd
    buf = chr(0)+chr(len(cmd))+cmd
    tn.send(buf)
    #print 'Sending:'
    prn_data(buf)
    xca_cmd = buf[2:]
    rst = gw_read(tn)
    return gw_msg(rst)

def gw_cancel_icc(tn, sid, bgd, endd, icc):
  iccs = icc[:10]
  s = gw_combo('0',sid, bgd, endd, iccs, '0007')
  print gw_sendcmd(tn, s)
  s = gw_combo('0',sid, bgd, endd, iccs, '0051')
  print gw_sendcmd(tn, s)
  s = gw_combo('1',sid, bgd, endd, iccs, '005200000000000000')
  return gw_sendcmd(tn, s)

def gw_add_icc(tn, sid, bgd, endd, icc, stb):
  iccs = icc[:10]
  stbs = stb[:10]
  s = gw_combo('0',sid, bgd, endd, iccs, '0007')
  print gw_sendcmd(tn, s)
  s = gw_combo('0',sid, bgd, endd, iccs, '0051')
  print gw_sendcmd(tn, s)
  s = gw_combo('1',sid, bgd, endd, iccs, '00520000'+stbs)
  return gw_sendcmd(tn, s)

def gw_add_prod(tn, sid, bgd, endd, icc, channel):
  iccs = icc[:10]
  s = gw_combo('0',sid, bgd, endd, iccs, '0002'+channel+bgd+endd)
  return gw_sendcmd(tn, s)

def gw_cancel_prod(tn, sid, bgd, endd, icc, channel):
  iccs = icc[:10]
  s = gw_combo('0',sid, bgd, endd, iccs, '0006'+channel)
  return gw_sendcmd(tn, s)

def ird_cmd(cmd):
  s = "0069%s" % (cmd)
  i = len(s)
  while i<108:
      s = s+'0'
      i = i+1
  return s
  
def utf8(s):
     return s.decode('big5').encode('utf-8')

def gw_chgpwd(tn, sid, bgd, endd, icc):
  iccs = icc[:10]
  cmd = ird_cmd('200001050431323334');
  s = gw_combo('1',sid, bgd, endd, iccs, cmd)
  return gw_sendcmd(tn, s)

def gw_resetpwd(tn, sid, bgd, endd, icc):
  iccs = icc[:10]
  cmd = ird_cmd('01800100');
  s = gw_combo('1',sid, bgd, endd, iccs, cmd)
  return gw_sendcmd(tn, s)

def gw_mail(tn, sid, bgd, endd, icc, mmsg):
  global xca_mailid
  if mmsg is None or mmsg=='':
      return 'Mail error'
  iccs = icc[:10]
  if xca_mailid<1023:
      xca_mailid = xca_mailid+1
  else:
      xca_mailid = 1
  mmsgs = utf8(mmsg)
  msg = ""
  for c in mmsgs:
    msg = msg+"%.2X" % (ord(c))
  print msg
  seg = ((len(msg)/2-1)/45)+1
  curr_seg = 0
  curr_idx = 0
  priority = 0
  while curr_seg<seg:
      if curr_seg<=seg-2:
          sndmsg = msg[curr_idx:(90+curr_idx)]
          curr_idx = curr_idx+90
          xlen = 48
      else:
          sndmsg = msg[curr_idx:len(msg)+1]
          curr_idx = curr_idx+len(sndmsg)
          xlen = len(sndmsg)/2+3
      cmdstr = "192001%.2d%.4X%.2X%s" % (xlen, (xca_mailid<<6)+seg, (priority<<6)+curr_seg, sndmsg)
      print '** '+cmdstr
      cmd = ird_cmd(cmdstr);
      s = gw_combo('1',sid, bgd, endd, iccs, cmd)
      retmsg = gw_sendcmd(tn, s)
      curr_seg = curr_seg+1
  return retmsg
  
def gw_forcetune(tn, sid, bgd, endd, icc, tune):
  iccs = icc[:10]
  if tune is None:
      return 'ServiceID error'
  cmd = ird_cmd('19300106000100040017');
  s = gw_combo('1',sid, bgd, endd, iccs, cmd)
  return gw_sendcmd(tn, s)

def gw_networkid(tn, sid, bgd, endd, icc, nwid):
  iccs = icc[:10]
  if nwid is None:
      return 'NetworkID error'
  cmdstr = '19800104%.4X0001' % (int(nwid))
  cmd = ird_cmd(cmdstr);
  s = gw_combo('1',sid, bgd, endd, iccs, cmd)
  return gw_sendcmd(tn, s)

def main():
   oracon = None
   try:
     while 1:
           oracon = ORA('coss/coss@nmsdb')
           rs = None
           if oracon.cexist():
             rs = oracon.execall(querySql)
             if rs != None and len(rs) > 0:
               print rs
               #sock = gw_open("10.20.51.11",59001) Lab
               sock = gw_open(hostip,59001)
               print sock
               if login(sock)>0:
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
                   if stb_no is None:
                       stb_no = '0000000000'
                   channel = "%.12d" % int(a_row[6])
                   status = "1"
                   if cmd=='A1':
                      resp = gw_add_icc(sock, sid, bg_date, end_date, icc_no, stb_no) 
                   elif cmd=='A2':
                      resp = gw_cancel_icc(sock, sid, bg_date, end_date, icc_no) 
                   elif cmd=='B1':
                      resp = gw_add_prod(sock, sid, bg_date, end_date, icc_no, channel) 
                   elif cmd=='B2':
                      resp = gw_cancel_prod(sock, sid, bg_date, end_date, icc_no, channel) 
                   elif cmd=='E1':
                      resp = gw_chgpwd(sock, sid, bg_date, end_date, icc_no) 
                   elif cmd=='E2':
                      resp = gw_resetpwd(sock, sid, bg_date, end_date, icc_no) 
                   elif cmd=='E3':
                      resp = gw_mail(sock, sid, bg_date, end_date, icc_no, mail) 
                   elif cmd=='E4':
                      resp = gw_forcetune(sock, sid, bg_date, end_date, icc_no, tune) 
                   elif cmd=='E5':
                      resp = gw_networkid(sock, sid, bg_date, end_date, icc_no, networkid) 
                   else:
                      resp = 'Command error'
                      status = "-1"
                   update_param=([status, resp, xca_cmd, xca_ret, sid],)
                   oracon.updateone(updateSql, update_param)
                   print "%s done" % sid
               sock.close();
             else:
               print ".",
           else:
             print "%s Reconnect" % time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
             oracon.reconnect()
           sys.stdout.flush()
           oracon.se_close()
           time.sleep(3)
     oracon.se_close()
   except KeyboardInterrupt:
     if oracon is not None:
         oracon.se_close()
     sock.close();
     print "Interrupt...\n"
     exit

if __name__ == "__main__":
   main()

