#!/usr/bin/env python
# -*- coding: Big5 -*-
import time,sys,string,binascii
import socket,telnetlib,select
import cossdb,pymssql
from oraclass import ORA
from cagw_func import CAGW_FUNC

sourceid = 20

xca_cmd = ''
xca_ret = ''
cafunc = CAGW_FUNC(sourceid, 'feedback', 1)
recv_buffer_length = 409600
sock = None

def gw_open(host, port):
        global sock
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

def gw_read(tn):
    global sock
    if tn is None:
        return None
    buf = None
    r, w, e = select.select([tn], [], [], 0.5)
    if r == []:
        return None
    try:
        buf = tn.recv(recv_buffer_length, 0)
        if len(buf)==0:
            return None
        #cafunc.prn_data(buf)
    except Exception, msg:
        print msg
        sock = None
        return None
    return buf

def gw_send(tn, s):
    global sock
    if tn is None:
        return None
    try:
        buf = chr(0)+chr(len(s))+s
        tn.sendall(buf)
        #cafunc.prn_data(buf)
    except Exception, msg:
        print msg
        sock = None
        return -1
    return 1

def login(tn):
  obname = "KBRO_FEEDBACK"
  buf = chr(0)+chr(len(obname)+2)+chr(0x0)+chr(len(obname))+obname
  tn.send(buf)
  cafunc.prn_data(buf)
  rst = gw_read(tn)
  try:
      if rst[2]==chr(0x06):
          rst = gw_read(tn)
          if rst[2]==chr(0x0):
              return 1
  except Exception, msg:
      print msg
      sys.stdout.flush()
      time.sleep(10)
      return -1

def ora_upd(result=None):
    if result is not None:
        s = result
        sid = s[0:9]
        return sid
    else:
        return None
    try:
        ora = ORA('coss/coss@nmsdb')
    except Exception, msg:
        print msg
        return None
    try:
        result_sql = ''
        cmd = ''
        sid = None
        s = result
        if result is not None:
            sid = s[0:9]
            type = s[9:11]
            src_id = s[11:15]
            dst_id = s[15:19]
            ppid = s[19:24]
            sdate = s[24:32]
            icc_no = s[32:42]
            cmd = s[42:46]
            print sid,type,cmd
            sql = "insert into cagw_feedback_d3(sid,icc_no,cmd) values(%d,'%s','%s')" % (int(sid), icc_no, cmd)
            ora.execone(sql)
            result_sql = ",sid='%s',cmd='%s'" % (sid, cmd)
            if cmd=='0211':
                result_sql = "%s,callback_date=to_date('%s','yyyymmddhh24miss')+8/24" % (result_sql, s[46:60])
            elif cmd=='0201':
                result_sql = "%s,stb_no='%s',credit=%f,debit=%f" % (result_sql, s[50:60], int(s[60:67])/100, int(s[67:74])/100)
            elif cmd=='0202':
                result_sql = "%s,stb_no='%s',product_id='%d',purchase_date=to_date('%s','yyyymmdd'),watch_flag='%s'" % (result_sql, s[50:60], int(s[60:72]), s[72:80], s[80:81])
            elif cmd=='0206':
                result_sql = "%s,stb_no='%s',watch_flag='%s'" % (result_sql, s[50:60], s[60:61])
            elif cmd=='0212':
                result_sql = "%s,cnt=%d" % (result_sql, int(s[46:48]))
            elif cmd=='0215':
                result_sql = "%s,orig_sid=%d,stb_no='%s',stop_flag='%s',cnt=%d" % (result_sql, int(s[46:55]), s[59:69], s[69:70], int(s[70:72]))
        else:
            return None
        if cmd=='0202':
            sql = "update cagw_feedback_d3 set status=''%s where sid=%d and status is null" % (result_sql, int(sid))
        else:
            sql = "update cagw_feedback_d3 set status='OK'%s where sid=%d and status is null" % (result_sql, int(sid))
        print sql
        ora.execone(sql)
        ora.commit()
        ora.se_close()
        return sid
    except Exception, msg:
        ora.se_close()
        print msg
        return None

def icc_sn(sid):
    tmp_sid = ((6*(sid/100000000)+19*(sid/10000000%10)+8*(sid/10000%1000)+(sid/100%100))%23+(sid%100))%100
    return tmp_sid

def ppv_trans():
    qsql = "select sid,icc_no,product_id,watch_flag from cagw_feedback_d3 where cmd='0202' and status is null"
    try:
        #con = pymssql.connect(host='CossMS',user='proguser',password='cossuser',database='cossdb')
        con = pymssql.connect(host='CossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
        cur = con.cursor()
        #inscon = pymssql.connect(host='CossMS',user='proguser',password='cossuser',database='cossdb')
        inscon = pymssql.connect(host='CossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
        inscur = inscon.cursor()
        orapt = ORA('coss/coss@nmsdb')
        rs = orapt.execall(qsql)
        if rs is not None and len(rs) > 0:
            for a_row in rs:
                err_flag = 0
                sid = a_row[0]
                try:
                    if len(a_row[1])<12:
                        icc_no = "%s%d" % (a_row[1], icc_sn(int(a_row[1])))
                    else:
                        icc_no = a_row[1][:12]
                    product_id = a_row[2]
                    watch_flag = a_row[3]
                    if watch_flag=='Y':
                        ppv_status = 'OK'
                    else:
                        ppv_status = 'IPPV_NOWATCH'
                    lsql = "select companyno,subsid,custid,singlesn from ms0200 where smartcard='%s' and servicename='3 DSTB' and custstatus in ('0 未收','1 正常','8 欠費中','9 移機中')" % (icc_no)
                    #print lsql
                    cur.execute(lsql)
                    xarr = cur.fetchone()
                    if xarr is not None:
                        companyno = xarr[0]
                        subsid = xarr[1]
                        custid = xarr[2]
                        singlesn = xarr[3]
                    else:
                        oraupdsql = "update cagw_feedback_d3 set status='SUBSID_NOTFOUND',icc_no='%s' where sid='%d'" % (icc_no, sid)
                        orapt.execone(oraupdsql)
                        orapt.commit()
                        print oraupdsql
                        continue
                    psql = "select name,point,channel,substr(channel||to_char(event_start,'mmddhh24mi'),1,10) prod_id,to_char(event_start+duration/86400,'yyyy/mm/dd hh24:mi') acttime,to_char(event_start+duration/86400,'yyyy/mm/dd') actdate,to_char(event_start,'yyyy/mm/dd hh24:mi')||':00' show_date from ppv_product where productid='%s'" % (product_id)
                    print psql
                    rs1 = orapt.execall(psql)
                    #print psql
                    if rs1 is not None and len(rs1) > 0:
                        for b_row in rs1:
                            prod_name = b_row[0]
                            ppv_point = b_row[1]
                            channel = b_row[2]
                            prod_id = b_row[3]
                            acttime = b_row[4]
                            actdate = b_row[5]
                            show_date = b_row[6]
                    csql = "select sid,subsid,icc_no from ppv_trans where companyno='%s' and prod_idx='%s' and custid='%s' and status='OK'" % (companyno,product_id,custid)
                    print csql
                    rs1 = orapt.execall(csql)
                    if rs1 is None or len(rs1)==0:
                        inssql = "insert into ppv_trans(companyno,subsid,custid,type,product_id,stb_no,icc_no,status,prod_idx,prod_name,ppv_point,src) values('%s','%s','%s','order','%s','%s','%s','%s','%s','%s','%s','IPPV')" % (companyno,subsid,custid,prod_id,singlesn,icc_no,ppv_status,product_id,prod_name,ppv_point)
                        print inssql
                        try:
                            orapt.execone(inssql)
                        except Exception, msg:
                            print msg
                            pass
                        if ppv_status=='OK':
                            try:
                                msql = "insert into ms3120(companyno,subsid,activetime,servicename,itemname,itemamt,activedate,billyn,billamt,createname,createtime,updatename,updatetime,showdate,eventid,itemtype,chargename,channelno) values('%s','%s','%s','3 DSTB','%s','%s','%s','N','%s','IPPV',getdate(),'IPPV',convert(varchar(19),getdate(),20),'%s','%s','PPV','18000 計次付費服務點播費用','%s')" % (companyno,subsid,acttime,prod_name,ppv_point,actdate,ppv_point,show_date,prod_id,channel)
                                print msql
                                #inscur.execute(msql)
                                msql = "insert into ms0212(companyno,subsid,eventdate,eventitem,eventamt,eventdesc,createname,createtime) values('%s','%s','%s','遙控器訂購影片','%s','日期:%s, 節目編號:%s,名稱:%s','IPPV',getdate())" % (companyno,subsid,acttime,ppv_point,acttime,prod_id,prod_name)
                                print msql
                                #inscur.execute(msql)
                                inscon.commit()
                            except Exception, msg:
                                print msg
                                err_flag = 1
                                pass
                    else:
                        for b_row in rs1:
                            x_subsid = b_row[1]
                            x_iccno = b_row[2]
                            if x_subsid==subsid and x_iccno==icc_no:
                                print "INFO: Already exist %s, %s, %s, %s" % (companyno,subsid,prod_id,icc_no)
                                break
                            else:
                                inssql = "insert into ppv_trans(companyno,subsid,custid,type,product_id,icc_no,status,prod_idx,prod_name,ppv_point,src) values('%s','%s','%s','order','%s','%s','IPPV_CUSTID_DUP','%s','%s','%s','IPPV')" % (companyno,subsid,custid,prod_id,icc_no,product_id,prod_name,ppv_point)
                                print inssql
                                orapt.execone(inssql)
                    if err_flag==0:
                        oraupdsql = "update cagw_feedback_d3 set status='OK',icc_no='%s' where sid='%d'" % (icc_no, sid)
                    print oraupdsql
                    orapt.execone(oraupdsql)
                    orapt.commit()
                except Exception, msg:
                    msg = str(msg).replace("'","")
                    oraupdsql = "update cagw_feedback_d3 set status='ERROR',msg='%s' where sid='%d'" % (msg, sid)
                    print oraupdsql
                    orapt.execone(oraupdsql)
                    orapt.commit()
                    print msg
                    continue

        orapt.se_close()
        con.close()
        inscon.close()
    except Exception, msg:
        print msg
        return None

def main():
   global sock
   oracon = None
   sock = None
   nop_flag = 0
   try:
     nowdate = time.strftime("%Y%m%d", time.localtime())
     ext_pkt = None
     while 1:
           #ppv_trans()
           if nop_flag>0:
               nop_flag = 0
           if sock is None:
               #sock = gw_open("10.20.51.11", 60003)
               sock = gw_open("10.20.111.11", 60003)
               if login(sock)<=0:
                   sock.close()
                   sock = None
                   continue
           # recieving commands from CA feedback Gateway
           recv_str = gw_read(sock)
           if recv_str is not None:
               if ext_pkt is not None:
                   recv_str = ext_pkt+recv_str
               maxlen = len(recv_str)
               nop_flag = 1
               ofs = 0
               while ofs<maxlen:
                   xlen = ord(recv_str[ofs])*256+ord(recv_str[ofs+1])
                   x = recv_str[ofs+2:ofs+2+xlen]
                   #print x
                   xsid = ora_upd(x)
                   if xsid is not None:
                       ack_cmd = cafunc.gw_ack(xsid)
                       #print ack_cmd
                       gw_send(sock, ack_cmd)
                   sid = x[36:45]
                   ofs = ofs+xlen+2
                   if ofs+xlen+2<maxlen:
                       ext_pkt = recv_str[ofs:maxlen]
                   else:
                       ext_pkt = None
           if nop_flag<=0:
               nop_flag = nop_flag-1
           #ppv_trans()
           sys.stdout.flush()
           if nop_flag<=-5:
               ppv_trans()
               cmdstr = cafunc.gw_keepalive(nowdate)
               #print cmdstr
               gw_send(sock, cmdstr)
               read_str = None
               iloop = 0
               while read_str is None and iloop<10:
                   read_str = gw_read(sock)
                   #print read_str
                   time.sleep(1)
                   iloop = iloop+1
                   pass
               nop_flag = 0
           sys.stdout.flush()
           time.sleep(1)
     if sock:
         sock.close()
   except KeyboardInterrupt:
     sock.close();
     print "Interrupt...\n"
     exit

if __name__ == "__main__":
   main()

