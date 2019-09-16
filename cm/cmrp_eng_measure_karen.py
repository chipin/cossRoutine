#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

if len(sys.argv) > 2 or len(sys.argv) < 1:
    print 'Error: Argument error'
    sys.exit(0)

so = sys.argv[1]

if so.upper() != 'TFM' and so.upper() != 'KBRO' and so.upper() != 'CG':
    print 'Error: Argument error'
    sys.exit(0)

nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print nowdate

yyyymmdd = time.strftime("%Y%m%d", time.localtime(time.time()-1*24*60*60))

try:
    if so == 'CG':
        con = pymssql.connect(host='CossMS_CG',user=cossdb.account,password=cossdb.passwd,database='cossdb')
    elif so == 'TFM':
        con = pymssql.connect(host='TFMCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')
    else:
        con = pymssql.connect(host='kbroCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
    cur = con.cursor()
except Exception, errmesg:
    print 'Error:',errmesg
    sys.exit(0)

oracon_qry = ORA('nms@cnis')
oracon_upd = ORA('qos@cnis')
oracon_coss = ORA('coss@cnis')

if not oracon_upd.db:
    sys.exit(0)




## 3 DSTB
if so == 'TFM':
   # querysql = "select a.companyno,a.subsid,a.worksheet,c.stbcmmac,a.worker1,convert(varchar(19),a.finishtime,20) finishtime,b.workkind from ms0301 a with (nolock) left join ms0300 b with (nolock) \
    #            on a.companyno=b.companyno and a.worksheet=b.worksheet left join mi0130 c with (nolock) on  a.singlesn=c.singlesn and c.stbcmmac is not null and c.stbcmmac<> '' \
    #            where (substring(b.workkind,1,1)  in ('1','6') or (substring(b.workkind,1,1) in ('C','5') and a.backcause1 not in ('C0805 區域性(雜訊或T3)干擾先結待查外線'))) and substring(a.sheetstatus,1,1) not in ('3','A') and a.companyno in ('101','103','104','300','701') and a.servicename='3 DSTB' and a.singlesn is not null \
     #           and a.singlesn<>''  and c.stbcmmac <> '' and c.stbcmmac is not null and convert(varchar,a.opfintime,112) ='%s' \
      #          group by a.companyno,a.subsid,a.worksheet,c.stbcmmac,a.worker1,a.finishtime,b.workkind " % (yyyymmdd)
                
    querysql = "select a.companyno,a.subsid,a.worksheet,a.singlesn,c.stbcmmac,a.worker1,convert(varchar(19),a.finishtime,20) finishtime,b.workkind \
			 from ms0301 a with (nolock) left join ms0300 b with (nolock)  \
			on a.companyno=b.companyno and a.worksheet=b.worksheet left join mi0130 c with (nolock) on a.companyno=c.companyno \
			and a.singlesn=c.singlesn and c.stbcmmac is not null and c.stbcmmac<> ''  \
			where  substring(b.workkind,1,1) in ('C','5')  and substring(a.sheetstatus,1,1) not in ('3','A')  \
			and a.servicename='3 DSTB' and a.singlesn is not null  and a.singlesn<>''  and convert(varchar,a.finishtime,112) ='%s' \
			 group by a.companyno,a.subsid,a.worksheet,c.stbcmmac,a.worker1,a.finishtime,b.workkind,a.singlesn" % (yyyymmdd)
else:
    #querysql = "select a.companyno,a.subsid,a.worksheet,c.stbcmmac,a.worker1,convert(varchar(19),a.finishtime,20) finishtime,b.workkind from ms0301 a with (nolock) left join ms0300 b with (nolock) \
     #           on a.companyno=b.companyno and a.worksheet=b.worksheet left join mi0130 c with (nolock) on a.companyno=c.companyno and a.singlesn=c.singlesn and c.stbcmmac is not null and c.stbcmmac<> '' \
      #          where (substring(b.workkind,1,1)  in ('1','6') or (substring(b.workkind,1,1) in ('C','5') and a.backcause1 not in ('C0805 區域性(雜訊或T3)干擾先結待查外線'))) and substring(a.sheetstatus,1,1) not in ('3','A')  and a.servicename='3 DSTB' and a.singlesn is not null \
       #         and a.singlesn<>'' and c.stbcmmac <>'' and c.stbcmmac is not null and a.chargename like '%%STB%%' and convert(varchar,a.opfintime,112) ='%s' \
        #        group by a.companyno,a.subsid,a.worksheet,c.stbcmmac,a.worker1,a.finishtime,b.workkind" % (yyyymmdd)
    querysql = "select a.companyno,a.subsid,a.worksheet,a.singlesn,c.stbcmmac,a.worker1,convert(varchar(19),a.finishtime,20) finishtime,b.workkind \
			 from ms0301 a with (nolock) left join ms0300 b with (nolock) \
			on a.companyno=b.companyno and a.worksheet=b.worksheet left join mi0130 c with (nolock) on a.companyno=c.companyno \
			and a.singlesn=c.singlesn and c.stbcmmac is not null and c.stbcmmac<> '' \
			where  substring(b.workkind,1,1) in ('C','5')  and substring(a.sheetstatus,1,1) not in ('3','A')  \
			and a.servicename='3 DSTB' and a.singlesn is not null  and a.singlesn<>'' and c.stbcmmac <>'' and c.stbcmmac is not null \
			 and convert(varchar,a.finishtime,112) ='%s' group by a.companyno,a.subsid,a.worksheet,c.stbcmmac,a.worker1,a.finishtime,b.workkind" % (yyyymmdd)
print querysql
cur.execute(querysql)
i = 0
uprxpwr=''
cmdspwr=''
cmuspwr=''
cmdssnr=''
cmussnr=''
t3=''
t4=''
cmussnr_2=''
uprxpwr_2=''
cmuspwr_2=''
while 1:
    curarr = cur.fetchmany(100)
    i = i+1
    if curarr:
        xlen = len(curarr)
        for ii in range(0, xlen):
            companyno = curarr[ii][0]
            subsid    = curarr[ii][1]
            worksheet = curarr[ii][2]
            singlesn  = curarr[ii][3]
            mac       = curarr[ii][4]
            worker    = curarr[ii][5]
            finishtime= curarr[ii][6]
            workkind  = curarr[ii][7]
            work_id   = ''
            work_name = ''
            if so == 'TFM':
              if mac is None:
              	coss_sql = "select cmmac from ca_stb where stbno='%s'" % (singlesn)
              	rst = oracon_coss.execall(coss_sql)
              	if rst is not None  and len(rst)>0:
                  for kk in rst:
                    try:
			mac = kk[0]
		    except:
			nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
			print '['+nowdate+']:'+str(msg)
            try:
                work_arr = worker.split(' ')
                work_id = work_arr[0]
                work_name = work_arr[1]
            except:
                pass

            if mac is not None:
            	qry_sql = "select rxpwr,cm_rxpwr,cm_txpwr,dl_snr,ul_snr,cm_t3,cm_t4,ul_snr2,rxpwr2,cm_txpwr2 from cmmac where cmmac='%s' and companyno='%s'" % (mac, companyno)
            	if companyno == '103':
		   print mac
		rs0 = oracon_qry.execall(qry_sql)
            	#print qry_sql
            	if rs0 is not None and len(rs0)>0:
                  for aw in rs0:
                    uprxpwr = aw[0]  ##上行接收功率
                    cmdspwr = aw[1]  ##下行接收功率
                    cmuspwr = aw[2]  ##上行發射功率
                    cmdssnr = aw[3]  ##下行SNR
                    cmussnr = aw[4]  ##上行SNR
                    t3     = aw[5]
                    t4     = aw[6]
                    cmussnr_2 = aw[7]
                    uprxpwr_2 = aw[8]
                    cmuspwr_2 = aw[9]
                if uprxpwr is None:
                  uprxpwr = ''
                if cmdspwr is None:
                  cmdspwr = ''
                if cmuspwr is None:
                  cmuspwr = ''
                if cmdssnr is None:
                  cmdssnr = ''
                if cmussnr is None:
                  cmussnr = ''
                if t3 is None:
                  t3 = ''
                if t4 is None:
                  t4 = ''
                if cmussnr_2 is None:
                  cmussnr_2 = ''
                if uprxpwr_2 is None:
                  uprxpwr_2 = ''
                if cmuspwr_2 is None:
                  cmuspwr_2 = ''

                qry_sql = "select count(*) cnt from eng_tickets_main where servicename='4 DSTB' and companyno='%s' and subsid='%d' and worksheet='%s' and mac='%s'" % (companyno,subsid,worksheet,mac)
                rs1 = oracon_upd.execall(qry_sql)
		#print qry_sql
                if rs1 is not None and len(rs1)>0:
                  for aw in rs1:
                    cnt = aw[0]

                if cnt < 1:
                  if cmussnr is None or cmdssnr is None:
                    oraupdsql = "insert into eng_tickets_main(companyno,worksheet,servicename,subsid,work_id,worker,mac,memo,eng_datetime, workkind, updatetime) \
                                 values ('%s','%s','4 DSTB',%d,'%s','%s','%s','4DSTB',sysdate,'%s',sysdate)" % (companyno, worksheet, subsid, work_id, work_name, mac, workkind)
                  else:
                    oraupdsql = "insert into eng_tickets_main(companyno,worksheet,servicename,subsid,work_id,worker,mac,memo,eng_datetime, cmussnr,cmussnr_2, cmdssnr, cmuspwr, cmuspwr_2, cmdspwr,uprxpwr, uprxpwr_2, t3, t4, workkind, updatetime) \
                                 values('%s','%s','4 DSTB',%d,'%s','%s','%s','4DSTB',sysdate,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',sysdate)" % (companyno, worksheet, subsid, work_id, work_name, mac, cmussnr, cmussnr_2, cmdssnr, cmuspwr, cmuspwr_2, cmdspwr, uprxpwr, uprxpwr_2, t3, t4, workkind)
                else:
                  if cmussnr is None or cmdssnr is None:
                    oraupdsql = "update eng_tickets_main set work_id='%s',worker='%s',workkind='%s',updatetime=sysdate where companyno='%s' and subsid='%d' and worksheet='%s' and mac='%s'" % \
                                 (work_id, work_name, workkind, companyno, subsid, worksheet, mac)
                  else:
                    oraupdsql = "update eng_tickets_main set cmussnr='%s',cmussnr_2='%s',cmdssnr='%s',cmuspwr='%s',cmuspwr_2='%s',cmdspwr='%s',uprxpwr='%s',uprxpwr_2='%s',servicename='3 DSTB',work_id='%s',worker='%s',workkind='%s',updatetime=sysdate where companyno='%s' and subsid='%d' and worksheet='%s' and mac='%s'" %  \
                                 (cmussnr, cmussnr_2, cmdssnr, cmuspwr, cmuspwr_2, cmdspwr, uprxpwr, uprxpwr_2, work_id, work_name, workkind, companyno, subsid, worksheet, mac)      
                  #print oraupdsql
                
		try:
		 
                  print oraupdsql
                  #oracon_upd.execone(oraupdsql)
                except Exception, msg:
                  print msg
                  sys.stdout.flush()

                #oracon_upd.commit()
                sys.stdout.flush()
    else:
        break

if oracon_qry is not None:
    oracon_qry.se_close()

if oracon_upd is not None:
    oracon_upd.se_close()

con.close()
sys.exit(0)
