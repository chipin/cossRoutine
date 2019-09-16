#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import time,sys,os,re,string
import requests,base64,json,re
from oraclass import ORA
from pprint import pprint
import pexpect,socket

# 執行 ./bin/cnr/cpnrTableNotMatch_addfixedip.py 310 >> davis.log
reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'
echoNum = 0

# 函式-cnr：connect
def conn(so,cnrip):
    cnr_shell = None
    '''永佳樂-101 陽明山-210 新台北-220 金頻道-230 全聯-250'''
    if  so=='101' or so=='210' or so=='220' or so=='230' or so=='250':
        nrcmd = '/opt/nwreg3/local/usrbin/nrcmd -C ' + cnrip + ' -N provgw -P pv#1176'
    else:
        nrcmd = '/opt/nwreg2/usrbin/nrcmd -C '       + cnrip + ' -N provgw -P pv#1176'
    try:
        cnr_shell = pexpect.spawn(nrcmd, timeout=15)
        cnr_shell.expect('nrcmd>', timeout=15)
        return cnr_shell
    except Exception, e:
        if  cnr_shell is not None:
            cnr_shell.close(True)
        return False

# 函式-轉換mac格式
def mac_fmt_conv(mac='',type=1):
    mac_fmt = ''
    try:
        ma = re.match(r"^([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$", mac)
        if  ma is not None:
            if  type==1:
                # 777df7777b99 -> 01:06:77:7d:f7:77:7b:99
                mac_fmt = '01:06:' + ma.group(1) + ':' + ma.group(2) + ':' + ma.group(3) + ':' + ma.group(4) + ':' + ma.group(5) + ':' + ma.group(6)
            else:
                # 777df7777b99 -> 1,6,77:7d:f7:77:7b:99
                mac_fmt = '1,6,' + ma.group(1) + ':' + ma.group(2) + ':' + ma.group(3) + ':' + ma.group(4) + ':' + ma.group(5) + ':' + ma.group(6)
            return mac_fmt.lower()
        else:
            return False
    except Exception, e:
        return False

# 函式-CMD client ip return result
def get_leaseIP_rst(ip,cnr_shell):
    cnr_shell.sendline('lease ' + ip)
    cnr_shell.expect('nrcmd>', timeout=60)
    return cnr_shell.before

# 函式-解析參數
def explodeStr(str):
    rst = re.split('=',str) # 【reservation-lookup-key = 1,6,xx:xx:xx:xx:xx:xx】 -> 【1,6,xx:xx:xx:xx:xx:xx】
    return rst[1].strip()

# 函式-insert cnr_queue cmd=addfixip
def ins_cnr_queue_addfixip(so,ip,cpemac,subsid):
    global getCPNRbySo
    account  = 'client-IP比對table-cpemac專案'
    sql = '''
    INSERT INTO cnr_queue(CNR_ID,COMMAND,IP,CPEMAC,COMPANYNO,SUBSID,ACCOUNT)
               VALUES('%s','addfixip','%s','%s','%s','%s','%s')
    '''%(getCPNRbySo[so]['cnr_id'],ip,cpemac,so,subsid,account)
    # oracon.execone(sql) # 執行不回傳，用execone
    # oracon.commit()
    return sql

# 函式-過濾空字串、單引號、下行、左右空白
def strip_rtn_cmd(msg):
    return msg.replace(" ","").replace("'","").replace(chr(13),"").strip()

# 函式-取得本機ip
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com', 0))
    ipaddr=s.getsockname()[0]
    return ipaddr

print '##############################################'
print '# 主程式開始'
print '##############################################'
if  len(sys.argv) < 2:
    print "error[Please input so]"
    sys.stdout.flush()
    exit(0)
else:
    so = sys.argv[1]

# ip與系統台驗證
thisIP = get_ip_address()
'''永佳樂-101 陽明山-210 新台北-220 金頻道-230 全聯-250'''
if  so=='101' or so=='210' or so=='220' or so=='230' or so=='250':
    if  thisIP.find(".72")>=0:
        sys.exit("該系統台%s，無法在%s執行!"%(so,thisIP))
else:
    if  thisIP.find(".71")>=0:
        sys.exit("該系統台%s，無法在%s執行!"%(so,thisIP))

# db 連接
oracon = ORA('nms@cnis')
if  oracon.db is None:
    print "[contents=DB Connect Faile]"
    sys.stdout.flush()
    exit(0)

# 取得cnrid資料by公司別
sql = "SELECT companyno,cnr_id,case when companyno='701' then ip4 else ip end ip  FROM cnr WHERE stopyn='N' ORDER BY companyno ASC"
getCPNRbySo = {}
soArrs      = []
cnrInfoArrs = oracon.execall(sql)
for arrs in cnrInfoArrs:
    soArrs.append(arrs[0])
    companyno = arrs[0]
    getCPNRbySo[companyno] = {'cnr_id':arrs[1],'cnr_ip':arrs[2]}

# 驗證so是否存在
if  not so in soArrs:
    print 'error[so is not exist!]'
    sys.exit()

time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
print time
try:
    cpnr_ip = getCPNRbySo[so]['cnr_ip']
except:
    print "error[Input only 101,210,220,230,250]"
    sys.stdout.flush()
    exit(0)

cnr_shell = None
cnr_shell = conn(so,cpnr_ip)

if  not cnr_shell:
    print "error[Connection failed!]"
    sys.stdout.flush()
    exit(0)

# 測試 schema for 220
sql = "select subsid,mac,ip,TO_CHAR(UPDATETIME,'YYYY-MM-DD-HH24:MI:SS') from cnr_fixip_coss where stopyn='N' and companyno='%s' and mac in('BC14015F1A43','000C766B2613')"%(so)
# 正式 schema
sql = "SELECT subsid,mac,ip,TO_CHAR(UPDATETIME,'YYYY-MM-DD-HH24:MI:SS') FROM cnr_fixip_coss WHERE stopyn='N' AND companyno='%s' AND UPDATETIME > to_date('2017/1/10 00:00:00','yyyy/mm/dd HH24:mi:ss') ORDER BY UPDATETIME ASC"%(so)
arrs_rst = oracon.execall(sql)
total = len(arrs_rst)
if  len(arrs_rst)>=0:
    if  so=='101' or so=='210' or so=='220' or so=='230' or so=='250':
        findWhere = 1
    else:
        findWhere = 2
    unknownArrs,matchArrs,not_matchArrs_beReserved,not_matchArrs_beFree,errorArrs = [],[],[],[],[]
    # cmd lease ip 迴圈
    for arrs in arrs_rst:
        subsid,cpemac,ip,upd = int(arrs[0]),mac_fmt_conv(arrs[1],2),arrs[2],arrs[3]
        result_str = get_leaseIP_rst(ip,cnr_shell) # cmd回傳字串
        # print result_str
        if  result_str is not None and len(result_str)>0:
            '''matchType
               => [unknownArrs]               ： cpemac 為空
               => [matchArrs]                 ： 資料正確 match(相符的話，flags=reserved,failover-updated)
               => [not_matchArrs_beReserved]  ： match不相符，該ip為reserved狀態
               => [not_matchArrs_beFree]      ： match不相符，該ip為free狀態
               => [errorArrs]                 ： 狀態為 302或500 錯誤
            '''
            obj = {'cpemac':''}
            getMacRst,getReservedRst = None,None
            if  result_str.find("100 Ok")>=0:
                lineArray = result_str.splitlines() # 將回傳字串，折解為陣列並比對
                for line in lineArray:
                    if  getMacRst==True and getReservedRst==True:
                        break
                    else:
                        if  findWhere==1:
                            # find for pnr
                            if  line.find("reservation-lookup-key = 1,6")>=0:
                                obj['cpemac'] = explodeStr(line)
                                getMacRst = True if obj['cpemac']==cpemac else False
                                continue
                            if  line.find("flags = reserved")>=0:
                                getReservedRst = True
                        elif findWhere==2:
                            # find for cnr
                            if  line.find("client-mac-addr = 1,6")>=0:
                                obj['cpemac'] = explodeStr(line)
                                getMacRst = True if obj['cpemac']==cpemac else False
                                continue
                            if  line.find("flags = reserved")>=0:
                                getReservedRst = True
                # matchType
                if  getMacRst==None and getReservedRst==None:
                    matchType ='[unknownArrs]'
                    obj['error'] = strip_rtn_cmd(result_str)
                elif  getMacRst==True and getReservedRst==True:
                    matchType ='[matchArrs]'
                elif  getMacRst==False:
                    if  getReservedRst==True:
                        matchType ='[not_matchArrs_beReserved]'
                    else:
                        matchType ='[not_matchArrs_beFree]'
                    obj['error'] = strip_rtn_cmd(result_str)
            else:
                # matchType
                matchType ='[errorArrs]'
                obj['error'] = strip_rtn_cmd(result_str)
            # lease ip結果塞入陣列
            log = "%s[%s]client %s[cnr_fixip_coss.mac=%s,cnr.cmd.mac=%s][subsid=%s][cmd.Rst=%s]"%(matchType,upd,ip,cpemac,obj['cpemac'],subsid,obj)
            if  matchType=='[unknownArrs]':
                unknownArrs.append(log)
            elif matchType=='[matchArrs]':
                matchArrs.append(log)
            elif matchType=='[not_matchArrs_beReserved]':
                not_matchArrs_beReserved.append(log)
            elif matchType=='[not_matchArrs_beFree]':
                not_matchArrs_beFree.append(log)
            elif matchType=='[errorArrs]':
                errorArrs.append(log)

    # 印出所有狀態list資訊
    no = 1
    print '[unknownArrs 數量/總數量]=%s/%s'%(len(unknownArrs),total)
    for txt in unknownArrs:
        print "[%s]"%(no),txt
        no+=1

    no = 1
    print '[matchArrs 數量/總數量]=%s/%s'%(len(matchArrs),total)
    '''
    for txt in matchArrs:
        print "[%s]"%(no),txt
        no+=1
    '''

    no = 1
    print '[not_matchArrs_beReserved 數量/總數量]=%s/%s'%(len(not_matchArrs_beReserved),total)
    for txt in not_matchArrs_beReserved:
        print "[%s]"%(no),txt
        no+=1

    no = 1
    print '[not_matchArrs_beFree 數量/總數量]=%s/%s'%(len(not_matchArrs_beFree),total)
    for txt in not_matchArrs_beFree:
        print "[%s]"%(no),txt
        no+=1

    no = 1
    print '[errorArrs 數量/總數量]=%s/%s'%(len(errorArrs),total)
    for txt in errorArrs:
        print "[%s]"%(no),txt
        no+=1


# 結束CNR連線
cnr_shell.sendline('exit')
cnr_shell.close()

# 結束oracle
oracon.se_close()
sys.exit()
