#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] START" % (tme)

try:
    con = pymssql.connect(host='kbroCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
    cur = con.cursor()
except:
    print "Exception: Unable to connect kbroCossMS"
    sys.exit(0)

try:
    con_t = pymssql.connect(host='TFMCossMS',user=cossdb.account,password=cossdb.passwd,database='cossdb')
    cur_t = con_t.cursor()
except:
    print "Exception: Unable to connect TFMCossMS"
    sys.exit(0)

try:
    con_c = pymssql.connect(host='CossMS_CG',user=cossdb.account,password=cossdb.passwd,database='cossdb_cg')
    cur_c = con_c.cursor()
except:
    print "Exception: Unable to connect CGCossMS"
    sys.exit(0)


oracon = ORA('OEMS@KBRO_NMSDB')
#SQL="update oems_impact set getimpactsubsid=null where sid in (SELECT sid FROM oems_impact where result='ERROR' and createtime>=sysdate-1) and result='ERROR' and companyno in ('101','103','104','300','701')"
SQL="update oems_impact set getimpactsubsid=null where result='ERROR' and createtime>=sysdate-1"
print SQL
#oracon.execone(SQL)
#oracon.commit()


oracon_cnis = ORA('NMS@CNIS')

sid_arr = []

orasql = "select a.sid,a.type,a.value,a.companyno,a.node,b.servicename,b.type \
from oems_impact a \
inner join oems_tickets_main b on b.sid=a.sid \
where a.sid='3368521' \
order by a.sid,a.type"
print orasql
rs = oracon.execall(orasql)
if rs is not None and len(rs) > 0:
    ii = 0
    jj = len(rs)
    kk = 0
    oldsid = 0
    print rs
    for a_row in rs:
        ii = ii+1
        sid = a_row[0]
        if(oldsid!=sid):
            oldsid = sid
            kk = ii-1
        type = a_row[1]
        value = a_row[2]
        companyno = a_row[3]
        if companyno=='106':
            cur_main = cur_c
        elif companyno in ['101','103','104','300','701']:
            cur_main = cur_t
        else:
            cur_main = cur
        node_value = a_row[4]
        if node_value is None:
            node_sql = "B.nodeno is not null"
            updnode_sql = "and node is null"
        else:
            node_sql = "B.nodeno='%s'" % (node_value)
            updnode_sql = "and node='%s'" % (node_value)

        srv = a_row[5]
        srv_sql = ''
        if srv is not None and len(srv) > 0:
            srv1 = srv.strip().split(',')
            if srv1 is not None and len(srv1) > 0:
                srv2 = "','".join(srv1)
                if srv2 is not None and len(srv2) > 0:
                    #srv3 = "'%s'" % (srv2)
                    srv_sql = "and A.servicename in ('%s')" % (srv2)
        
        
        act = a_row[6]
        if act is not None:
          act = int(act)
          if act == 3114:
              srv_sql = "and A.servicename in ('2 CM')"
          elif act == 3115:
              srv_sql = "and A.servicename in ('3 DSTB')"
        print sid,type,value,companyno,node_value,srv
        if sid is None:
            print '[SID] = NULL'
            continue
        if type is not None:
            if type=='LINK':
                ma = re.match(r"^(\w{5}\-[1-9]{1,11})", value)
                if ma is not None:
                    mat = ma.group(1)
                else:
                    type='ErrorLINK'

            if type=='ROAD':
                sqls = "select distinct A.subsid,A.servicename,A.subsname,B.nodeno,B.addrname,C.mailtitle,B.mduname,B.linkid \
from ms0200 A with (nolock) inner join ms0102 B with (nolock) on A.custid = B.custid and A.companyno=B.companyno \
inner join ms0100 C with (nolock) on A.custid = C.custid and A.companyno=C.companyno \
where A.companyno='%s' and ( \
  substring(A.custstatus,1,1) not in ('3','4','5','6') or \
  (substring(A.custstatus,1,1) = '6' and substring(A.servicename,1,1) in ('2','3','5','7','9','C') and len(A.singlesn) > 0) or \
  (substring(A.custstatus,1,1) = '6' and substring(A.servicename,1,1) not in ('2','3','5','7','9','C')) \
) and B.addrno = 0 and (B.addrname like '%%%s%%' or B.msregion='%s') and %s %s" % (companyno, value, value, node_sql, srv_sql)
            elif type=='NODE':
                if companyno=='106':
                    sqls = "select distinct A.subsid,A.servicename,A.subsname, \
case when substring(a.servicename, 1, 1) = '5' and D.nodeno <> '' and D.nodeno <> '未設' and D.nodeno is not null then D.nodeno else B.nodeno end nodeno, \
B.addrname,C.mailtitle,B.mduname, \
case when substring(a.servicename, 1, 1) = '5' and D.nodeno <> '' and D.nodeno <> '未設' and D.nodeno is not null then D.nodeno else B.linkid end linkid \
from ms0200 A with (nolock) \
inner join ms0102 B with (nolock) on A.custid = B.custid and A.companyno=B.companyno \
inner join ms0100 C with (nolock) on A.custid = C.custid and A.companyno=C.companyno \
left join fttx_node D with (nolock) on A.subsid = D.subsid \
where A.companyno='%s' and ( \
  substring(A.custstatus,1,1) not in ('3','4','5','6') or \
  (substring(A.custstatus,1,1) = '6' and substring(A.servicename,1,1) in ('2','3','5','7','9','C','F') and len(A.singlesn) > 0) or \
  (substring(A.custstatus,1,1) = '6' and substring(A.servicename,1,1) not in ('2','3','5','7','9','C','F')) \
) and B.addrno = 0 and (B.nodeno='%s' or D.nodeno='%s') %s" % (companyno, value, value, srv_sql)
                else:
                    sqls = "select distinct A.subsid,A.servicename,A.subsname,B.nodeno,B.addrname,C.mailtitle,B.mduname,B.linkid \
from ms0200 A with (nolock) inner join ms0102 B with (nolock) on A.custid = B.custid and A.companyno=B.companyno \
inner join ms0100 C with (nolock) on A.custid = C.custid and A.companyno=C.companyno \
where A.companyno='%s' and ( \
  substring(A.custstatus,1,1) not in ('3','4','5','6') or \
  (substring(A.custstatus,1,1) = '6' and substring(A.servicename,1,1) in ('2','3','5','7','9','C','F') and len(A.singlesn) > 0) or \
  (substring(A.custstatus,1,1) = '6' and substring(A.servicename,1,1) not in ('2','3','5','7','9','C','F')) \
) and B.addrno = 0 and B.nodeno='%s' %s" % (companyno, value, srv_sql)
            elif type=='LINK':
                sqls = "select distinct A.subsid,A.servicename,A.subsname,B.nodeno,B.addrname,C.mailtitle,B.mduname,B.linkid \
from ms0200 A with (nolock) inner join ms0102 B with (nolock) on A.custid = B.custid and A.companyno=B.companyno \
inner join ms0100 C with (nolock) on A.custid = C.custid and A.companyno=C.companyno \
where A.companyno='%s' and ( \
  substring(A.custstatus,1,1) not in ('3','4','5','6') or \
  (substring(A.custstatus,1,1) = '6' and substring(A.servicename,1,1) in ('2','3','5','7','9','C','F') and len(A.singlesn) > 0) or \
  (substring(A.custstatus,1,1) = '6' and substring(A.servicename,1,1) not in ('2','3','5','7','9','C','F')) \
) and B.addrno = 0 and B.nodeno='%s' and B.linkid like '%s%%' %s" % (companyno, node_value, mat, srv_sql)
            elif type=='SUBSID':
                sqls = "select distinct A.subsid,A.servicename,A.subsname,B.nodeno,B.addrname,C.mailtitle,B.mduname,B.linkid \
from ms0200 A with (nolock) inner join ms0102 B with (nolock) on A.custid = B.custid and A.companyno=B.companyno \
inner join ms0100 C with (nolock) on A.custid = C.custid and A.companyno=C.companyno \
where A.companyno='%s' and ( \
  substring(A.custstatus,1,1) not in ('3','4','5','6') or \
  (substring(A.custstatus,1,1) = '6' and substring(A.servicename,1,1) in ('2','3','5','7','9','C','F') and len(A.singlesn) > 0) or \
  (substring(A.custstatus,1,1) = '6' and substring(A.servicename,1,1) not in ('2','3','5','7','9','C','F')) \
) and B.addrno = 0 and A.subsid='%s'" % (companyno, value)
            else:
                if type=='ErrorLINK':
                    type='LINK'
                updsql = "update OEMS_IMPACT set getimpactsubsid=sysdate,result='UNKNOWN' where sid=%d and companyno='%s' and type='%s' and value='%s' %s" % (sid,companyno,type,value,updnode_sql)
                print updsql
                #oracon.execone(updsql)
                #oracon.commit()
                continue
        else:
            print '[Type] = NULL'
            continue

        print sqls
        try:
            cur_main.execute(sqls)
            xarr = cur_main.fetchall()
            vip_string = ''
            for ms_row in xarr:
                vip = 'N'
                if ms_row[5] is not None:
                	vip_cnt = ms_row[5].find('009',0)
                	vip_string = ms_row[5][vip_cnt:]
              	else:
              		vip_string = ms_row[5]
                try:
                    if vip_string is not None and vip_string[0:3]=='009':
                        vip_str = vip_string[0:5]
                        if vip_str=='00905' or vip_str=='00906' or vip_str=='00907':
                            vip = 'S'
                        elif vip_str in ['00908','00909','00910','00911','00912','00914','00916']:
                            vip = 'Y'
                except:
                    pass
                inssql = "insert into OEMS_IMPACT_SUBSCRID(sid,companyno,subsid,servicename,create_date,impact,subsname,nodeno,addrname,mduname,vip,linkid) values(%d,'%s',%d,'%s',sysdate,'Y','%s','%s','%s','%s','%s','%s')" % (sid,companyno,ms_row[0],ms_row[1],ms_row[2],ms_row[3],ms_row[4],ms_row[6],vip,ms_row[7])
                print inssql
                try:
                    #oracon.execone(inssql)
                    pass
                except Exception, detail:
                    print '[Insert Error]: '+ str(detail)

            node_lv = ''
            if type in ['ROAD','NODE','LINK','SUBSID'] and node_value is not None and len(node_value) > 0:
                orasql2 = "select companyno,s_id,stopyn,mslayer from site_engine where companyno='%s' and s_id='%s' and site_type='20' and stopyn='N' order by updatetime desc" % (companyno,node_value)
                rs2 = oracon_cnis.execall(orasql2)
                if rs2 is not None and len(rs2) > 0:
                    for row2 in rs2:
                        node_lv = row2[3]
                        break;

            updsql = "update OEMS_IMPACT set getimpactsubsid=sysdate,result='OK',node_lv='%s' where sid=%d and companyno='%s' and type='%s' and value='%s' %s" % (node_lv,sid,companyno,type,value,updnode_sql)
            print updsql
            #oracon.execone(updsql)
            #oracon.commit()
            if sid not in sid_arr:
                sid_arr.append(sid)
        except Exception, detail:
            print detail
            updsql = "update OEMS_IMPACT set getimpactsubsid=sysdate,result='ERROR' where sid=%d and companyno='%s' and type='%s' and value='%s' %s" % (sid,companyno,type,value,updnode_sql)
            print updsql
            #oracon.execone(updsql)
            #oracon.commit()

for sid in sid_arr:
    try:
        catv_total = cm_total = dstb_total = voip_total = fttb_total = eoc_total = ls_total = cmc_total = total = 0
        cntsql = "select servicename,count(*) cnt from oems_impact_subscrid where sid=%d and impact='Y' group by servicename" % (sid)
        print cntsql
        rscnt = oracon.execall(cntsql)
        if rscnt is not None and len(rscnt) > 0:
            for rowcnt in rscnt:
                subsrv = rowcnt[0]
                subcnt = int(rowcnt[1])
                total = total + subcnt

                if subsrv == '1 CATV':
                    catv_total = subcnt
                if subsrv == '2 CM':
                    cm_total = subcnt
                if subsrv == '3 DSTB':
                    dstb_total = subcnt
                if subsrv == '4 VOIP':
                    voip_total = subcnt
                if subsrv == '5 FTTB':
                    fttb_total = subcnt
                if subsrv == '7 EOC':
                    eoc_total = subcnt
                if subsrv == '8 LS':
                    ls_total = subcnt
                if subsrv == '9 CMC':
                    cmc_total = subcnt
        if total > 0:
            cntqrysql = "select sid from oems_impact_summary where sid=%d" % (sid)
            rsqry = oracon.execall(cntqrysql)
            if rsqry is not None and len(rsqry) > 0:
                cntupdsql = "update oems_impact_summary set total=%d,catv_total=%d,cm_total=%d,dstb_total=%d,voip_total=%d,fttb_total=%d,eoc_total=%d,ls_total=%d,cmc_total=%d,updatetime=sysdate where sid=%d" % (total,catv_total,cm_total,dstb_total,voip_total,fttb_total,eoc_total,ls_total,cmc_total,sid)
            else:
                cntupdsql = "insert into oems_impact_summary (sid,total,catv_total,cm_total,dstb_total,voip_total,fttb_total,eoc_total,ls_total,cmc_total,updatetime) values (%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,sysdate)" % (sid,total,catv_total,cm_total,dstb_total,voip_total,fttb_total,eoc_total,ls_total,cmc_total)
            print cntupdsql
           # oracon.execone(cntupdsql)
           # oracon.commit()
    except Exception, detail:
        print detail

if oracon is not None:
    oracon.se_close()
if oracon_cnis is not None:
    oracon_cnis.se_close()
con.close()
con_c.close()
con_t.close()

tme = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print "[%s] END\n" % (tme)
