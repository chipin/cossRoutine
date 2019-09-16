#!/usr/bin/env python
# -*- coding: big5 -*-
import sys, time
from oraclass import ORA

v1 = None
v2 = None
while 1:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print nowdate

    try:
        v2 = ORA('coss@cnis')
        if not v2.db:
            print 'Error: Unable to connect to server [CNIS]'
            v2 = None
            time.sleep(60)
            continue
    except:
        print 'Error: Unable to connect to server [CNIS]'
        v2 = None
        time.sleep(60)
        continue

    try:
        v1 = ORA('coss@kbro_nmsdb')
        if not v1.db:
            print 'Error: Unable to connect to server [KBRO_NMSDB]'
            v1 = None
            time.sleep(60)
            continue
    except:
        print 'Error: Unable to connect to server [KBRO_NMSDB]'
        v1 = None
        time.sleep(60)
        continue

    try:
        qrysql = "select * from (select sid,sys,sender,target,msg,so,subsid from oss_sms where status='INIT' and real_sendtime is null and sysdate >= sendtime and sys not in ('SMS_SYS','COSSMS') and length(target) = 10 and msg is not null order by sid) where rownum <= 30"
        #qrysql = "select sid,sys,sender,target,msg,so,subsid from oss_sms where status='INIT' and real_sendtime is null and sysdate>=sendtime and sys not in ('SMS_SYS','COSSMS') and length(target) = 10 and msg is not null and rownum<=3 order by sid"
        rst = v1.execall(qrysql)
    except:
        print 'Error: Unable to execute SQL [KBRO_NMSDB]'
        if v1 is not None:
            v1.se_close()
            v1 = None
        time.sleep(60)
        continue

    if rst is not None and len(rst) > 0:
        for aw in rst:
            #nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())

            #external = 585000
            sid = int(aw[0])
            sysrc = aw[1]
            sender = aw[2]
            target = aw[3]
            #target = '0935864096'
            msg = aw[4]
            so = aw[5]
            if so is None:
                so = '026'
            #if so is not None:
            #    external = 585000 + so
            #else:
            #    external = 585000 + 26
            subsid = aw[6]
            if subsid is None:
                subsid = ''
            sysrc = sysrc + '(' + so + ')'
            sender = "%s(%d)" % (sender,sid)

            print sysrc,sender,target,subsid

            if len(target) == 10 and len(msg) > 0:
                try:
                    inssql = "insert into sms_queue_pay@tfnnms (external,mbl_nbr,msg,ins_date,catgy,account) values ('5856666','%s','%s',sysdate,'%s','%s')" % (target, msg, sysrc, sender)
                    print inssql
                    v2.execone(inssql)
                    v2.commit()
                except Exception, detail:
                    result = "Exception: Unable to insert sms_queue_pay (%s)" % (detail)
                    print result

                try:
                    updsql = "update oss_sms set status='OK(T)',real_sendtime=sysdate where sid=%d" % (sid)
                    print updsql
                    v1.execone(updsql)
                    v1.commit()
                except Exception, detail:
                    print "Exception: Unable to update oss_sms (%s)" % (detail)

            sys.stdout.flush()

    if v1 is not None:
        v1.se_close()
        v1 = None
    if v2 is not None:
        v2.se_close()
        v2 = None
    sys.stdout.flush()
    time.sleep(10)
