#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# 10.22.111.11 : 60002
import os,sys,time,string,socket,select
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'
#sourceID_array = [5,6,7,8,9,10,11,12,13,14,15]
sourceID_array = [5,6,7,8,9,10,11,12,15]
querySql = "select icc_no,min(sid) as minsid,max(sid) as maxsid,count(sid) as cnt from cagw_queue_d3 where sid>111025612 and sourceid is null group by icc_no"

def main():
    oracon = None
    sourceID_idx = 0
    sourceID_batch_count = 0
    try:
        nowdate = time.strftime("%Y%m%d", time.localtime())
        while 1:
            try:
                if oracon is None:
                    oracon = ORA('coss@kbro_nmsdb')
                rs = None
                if oracon.cexist():
                    try:
                        rs = oracon.execall(querySql)
                    except Exception, msg:
                        print querySql
                        print 'querySQL: '+str(msg)
                        oracon.se_close()
                        oracon = None
                        time.sleep(15)
                        continue

                    if rs is not None and len(rs) > 0:
                        print "%s cnt=%d" %(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()), len(rs))
                        for a_row in rs:
                            try:
                                icc_no = a_row[0]
                                minsid = a_row[1]
                                maxsid = a_row[2]
                                p_cnt = a_row[3]
                                sourceID_batch_count = sourceID_batch_count+p_cnt
                                try:
                                    p_sourceID = sourceID_array[sourceID_idx]
                                except:
                                    pass
                                    sourceID_idx = 0
                                    p_sourceID = sourceID_array[sourceID_idx]
                                upd_sql = "update cagw_queue_d3 set sourceid=%d where icc_no='%s' and sid between %d and %d" % (p_sourceID, icc_no, minsid, maxsid)
                                oracon.execone(upd_sql)
                                if sourceID_batch_count>30:
                                    sourceID_batch_count = 0
                                    sourceID_idx = sourceID_idx+1
                                print "%s %d %d %d %s" %(icc_no, minsid, maxsid, p_cnt, time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
                            except Exception, msg:
                                print "ERROR : "+str(msg)
                                sys.stdout.flush()
                        oracon.commit()
                    else:
                        print '--'
                        sys.stdout.flush()
                print '*'
                sys.stdout.flush()
            except Exception, msg:
                print 'Error: '+str(msg)
                try:
                    oracon.se_close()
                except:
                    pass
                oracon = None
                time.sleep(15)
            if oracon:
                oracon.se_close()
                oracon = None
            print "@"
            sys.stdout.flush()
            time.sleep(10)
    except KeyboardInterrupt:
        if oracon:
            oracon.se_close()
            oracon = None
        print "Interrupt...\n"
        exit

if __name__ == "__main__":
    main()
