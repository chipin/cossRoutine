#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
# CMMAC: xxxSTB   CPEMAC: xxxSTBdefault
# CMMAC: xxxTV10M CPEMAC: xxxTVSTB
# CMMAC: xxxCPzz  CPEMAC: xxxMTA-yy
import time,sys,os,re
import requests,base64,json,re
from oraclass import ORA
from pprint import pprint
import pexpect

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'
'''程式執行流程
1.程式輸入 cnrid
  /pnr_rest_api.py KP_CPNR1_001
  pnrID = KP_CPNR1_001
2.到 cnr_pnr table 找尋 cnr info(帳號和密碼)
  SELECT companyno,cnr_id,cnr_id2,ip,ip2,apiuser,apipwd FROM cnr_pnr WHERE stopyn='N' AND (cnr_id='%s' OR cnr_id2='%s') " % (pnrID,pnrID)
  
3.companyno 要符合以下代號，使可繼續
  companyno not in ('101','210','220','230','250') => exit
  
4.到 cnr_queue_pnr table 找尋 cnr_id = KP_CPNR1_001 
  且 company符合('101','210','220','230','250') =>目前僅開放220,230
  執行其所有command
  SELECT sid,command,cmmac,policy,ip,cpemac,companyno,subsid FROM 
  (                                                                
      SELECT sid,command,cmmac,policy,ip,cpemac,companyno,subsid,  
        CASE                                                       
        WHEN command='active' AND policy LIKE '%%TV%%'  THEN 1     
        WHEN command='active' AND policy LIKE '%%STB%%' THEN 2     
        WHEN command IN ('querymac','querybw') THEN 3 ELSE 1       
         END seq                                                   
        FROM %s                                                    
       WHERE cnr_id = '%s'                                         
         AND status='INIT'                                         
         AND companyno IN ('220','230')    
         AND command IN ('active','modify','delete','addfixip','addfixip2','delfixip','deactiveip','activeip','querymac','querybw','fixpublic','fixprivate','ddos','delddos') 
         AND sysdate >= book_date                                  
       ORDER BY seq,book_date,sid                                  
  )WHERE rownum <= 30 
  % (pnrTable_DB,pnrID)

'''
# 函式-insert db
def upt_db(status,msg,sid,sql_schema):
    global oracon,upt_msg,pnrTable_DB

    if  sql_schema=='none':
        msg = re.sub("'",'',str(msg))
        upd_status_sql = "UPDATE %s SET status='%s',status_date=sysdate,result='%s' WHERE sid = %d" % (pnrTable_DB,status,msg,sid)
    else:
        upd_status_sql = sql_schema
    try:
      oracon.execone(upd_status_sql) # 執行不回傳，用execone
      oracon.commit()
    except Exception,msg:
      upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'upt_db(%s,%s,%s,%s)'%(status,msg,sid,sql_schema),'[contents=UPDATE DB ERROR]'
      #upt_msg['schema'] = upd_status_sql

# 函式-request
def get_request(method,cnrip,pnrType,data,apiuser,apipwd,sid):
    global upt_msg
    api_URL = "http://" + cnrip + ":8080/web-services/rest/resource/" + pnrType
    b64Val = base64.b64encode(apiuser + ":" + apipwd)
    headers = {"Authorization": "Basic %s" % b64Val,"accept":"application/json"}
    headers.update({"Content-type":"application/json"}) # headers["Content-type"]="application/json"
    try:
        if  method=="get" :
            r=requests.get(api_URL,headers=headers)
        elif method=="post": 
            r=requests.post(api_URL,headers=headers,data=json.dumps(data))
        elif method=="put": 
            r=requests.put(api_URL,headers=headers,data=json.dumps(data))
        elif method=="del":
            r=requests.delete(api_URL,headers=headers,data=json.dumps(data))
        elif method=="querymac":
            r=requests.get(api_URL,headers=headers)
        elif method=="querybw":
            r=requests.get(api_URL,headers=headers)
        elif method=="Reservation": 
            r=requests.post(api_URL,headers=headers,data=json.dumps(data))
        # api Result
        if  r.status_code==200 or r.status_code==201:
            # api Result for get data
            if  method=="get" :
                return r.json()
            # api Result for querymac  
            if  method=="querymac":
                rst =  json.loads(r.content) # query by ip => 10.95.0.88 有relayAgentRemoteId,clientMacAddr資料
                if  'relayAgentRemoteId' in rst:
                    rst_cmmac,rst_cpemac = rst['relayAgentRemoteId'],rst['clientMacAddr']
                    rst_cmmac = rst_cmmac.replace(":","")
                    rst_cpemac = rst_cpemac.replace(":","").split(',')[2]
                    upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 1,"get_request","[url=%s][http_code=%s][cmmac=%s][cpemac=%s]"%(api_URL,r.status_code,rst_cmmac,rst_cpemac)
                    sql_schema = "UPDATE %s SET status='%s',cmmac=upper('%s'),cpemac=upper('%s'),status_date=sysdate,result='%s' WHERE sid = %d" % (pnrTable_DB,'OK',rst_cmmac,rst_cpemac,'cnr api ok by querymac',sid)
                    upt_db('OK','','',sql_schema)
                    return True
                else:
                    upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,"get_request","[url=%s][http_code=%s][contents=relayAgentRemoteId,clientMacAddr is not found]"%(api_URL,r.status_code)
                    upt_db('ERROR',str(upt_msg),sid,'none')
                    return False
            # api Result for querybw
            if  method=='querybw':
                rst =  json.loads(r.content) # query by mac => 788DF7316B00
                if  'clientClassName' in rst:
                    policy = rst['clientClassName']
                    upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 1,"get_request","[url=%s][http_code=%s][policy=%s]"%(api_URL,r.status_code,policy)
                    sql_schema = "UPDATE %s SET status='%s',policy='%s',status_date=sysdate,result='%s' WHERE sid = %d" % (pnrTable_DB,'OK',policy,'cnr api ok by querybw',sid)
                    upt_db('OK','','',sql_schema)
                    return True
                else:
                    upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,"get_request","get_request","[url=%s][http_code=%s][contents=clientClassName is not found]"%(api_URL,r.status_code)
                    upt_db('ERROR',str(upt_msg),sid,'none')
                    return False
            # api Result for Reservation
            if  method=="Reservation":
                    return True                                        
            # api Result 一般
            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 1,"get_request","[url=%s][http_code=%s]"%(api_URL,r.status_code)
            upt_db('OK','cnr api ok',sid,'none')
            return True
        else:
            text = re.sub("'",'',r.text)
            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,"get_request","[url=%s][http_code=%s][contents=%s]"%(api_URL,r.status_code,text)
            # 解決cpemac重覆綁定問題
            if  method=="Reservation": 
                match_str = "EX_CONFLICT_EXISTS - Reservation"
                if  text.find(match_str)>=0:
                    pnrType = 'Reservation?lookupKey=^%s$'%(data['lookupKey'])
                    getData = get_request("get",cnrip,pnrType,"",apiuser,apipwd,sid)
                    # 若有查詢到資料
                    if  getData:
                        return getData[0]['ipaddr']
            upt_db('ERROR',str(upt_msg),sid,'none')
            return False
    except Exception, msg:
        upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'get_request','[url=%s][data=%s][contents=Exception:%s]'%(api_URL,str(data),msg)
        upt_db('ERROR',str(upt_msg),sid,'none')
        return False

# 函式-cnr：connect
def conn(cnrip):
    cnr_shell = None
    nrcmd = '/opt/nwreg3/local/usrbin/nrcmd -C ' + cnrip + ' -N provgw -P pv#1176'
    try:
        # nrcmd = '/opt/nwreg3/local/usrbin/nrcmd -C 10.222.2.104 -N provgw -P pv#1176'
        cnr_shell = pexpect.spawn(nrcmd, timeout=15)
        cnr_shell.expect('nrcmd>', timeout=15)
        return cnr_shell
    except Exception, e:
        if  cnr_shell is not None:
            cnr_shell.close(True)
        upt_msg['rtn'],upt_msg['fn'] = 0,'conn(cnrip=%s)'%(cnrip)
        upt_msg['info'] = '[contents=Exception,Connect Error][nrcmd=%s]'%(nrcmd)
        return False
        
# 函式-get scope ->範例：123.193.237.166
def get_scope(ip):
    global oracon,upt_msg
    matchIP = re.match(r"^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})$", ip)
    ipnum = int(matchIP.group(1))*pow(256,3) + int(matchIP.group(2))*pow(256,2) + int(matchIP.group(3))*pow(256,1) + int(matchIP.group(4))
    get_scope_sql = "select scope from cnr_scope_iprange where %d between ip_bgv and ip_endv order by updtime desc" % (ipnum)
    get_scope = oracon.execall(get_scope_sql)
    if  get_scope is None:
        upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'get_scope(ip=%s)'%(ip),'[content=scope is not found]'
        #upt_msg['schema'] = get_scope_sql
        return False
    else:    
        scope_txt = get_scope[0][0] 
        scope = re.match(r"^(.+)B[0-6|8-9][0-9]$",scope_txt) # ex. ANTK24S500B03 -> ANTK24S500
        if  scope is None:
            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'get_scope(ip=%s)'%(ip),'[content=scope re.match not found,range is BXX][select scope=%s]'%(scope_txt)
            return False
        else:
            return scope.group(1)

# 函式-轉換mac格式：777df7777b99 -> 01:06:77:7d:f7:77:7b:99
def mac_fmt_conv(mac=''):
    mac_fmt = ''
    try:
        ma = re.match(r"^([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$", mac)
        if  ma is not None:
            mac_fmt = '01:06:' + ma.group(1) + ':' + ma.group(2) + ':' + ma.group(3) + ':' + ma.group(4) + ':' + ma.group(5) + ':' + ma.group(6)
            return mac_fmt.lower()
        else:
            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'mac_fmt_conv(mac=%s)'%(mac),'[contents=mac_fmt_conv re.match Error]'
            return False
    except Exception, e:
        upt_msg['rtn'],upt_msg['fn'] = 0,'mac_fmt_conv(mac=%s)'%(mac)
        upt_msg['info'] = '[contents=Exception mac_fmt_conv Error]'
        return False

# 函式-轉換mac格式：777df7777b99 -> 1,6,77:7d:f7:77:7b:99
def mac_fmt_conv_2(mac=''):
    mac_fmt = ''
    try:
        ma = re.match(r"^([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$", mac)
        if  ma is not None:
            mac_fmt = '1,6,' + ma.group(1) + ':' + ma.group(2) + ':' + ma.group(3) + ':' + ma.group(4) + ':' + ma.group(5) + ':' + ma.group(6)
            return mac_fmt.lower()
        else:
            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'mac_fmt_conv(mac=%s)'%(mac),'[contents=mac_fmt_conv re.match Error]'
            return False
    except Exception, e:
        upt_msg['rtn'],upt_msg['fn'] = 0,'mac_fmt_conv_2(mac=%s)'%(mac)
        upt_msg['info'] = '[contents=Exception mac_fmt_conv_2 Error]'
        return False
        
# 函式-cnr：新增固定ip、開啟及關閉固定ip(addfixip2,activeip,deactiveip)
def runComand(cnrip,cmd,cpemac,ip,oracon,sid,apiuser,apipwd):
    global upt_msg
    result_str = ''
    cnr_shell = None
    cnr_shell = conn(cnrip)
    if  cnr_shell is None:
        upt_db('ERROR',str(upt_msg),sid,'none')
        return False
    if  cmd=="addfixip2":
        if  cpemac is None or ip is None:
            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'runComand(cnrip=%s,cmd=%s,cpemac=%s,ip=%s,sid=%s)'%(cnrip,cmd,cpemac,ip,sid),'[content=require paramter (cpemac,ip)]'
            upt_db('ERROR',str(upt_msg),sid,'none')
            return False
        # 由ip找尋scope，再由scope找尋新scope陣列
        scope = get_scope(ip)
        # api 只接收 01:06:xx:xx:xx:xx:xx:xx 格式
        if  scope is False or cpemac is False:
            upt_db('ERROR',str(upt_msg),sid,'none')
            return False
        getScope_sql = "select scope from cnr_scope_iprange where regexp_like(scope,'^%sB[0-6|8-9][0-9]$') order by companyno,scope" % (scope)
        getScopeArray_rst = oracon.execall(getScope_sql)
        if  len(getScopeArray_rst)<=0:
            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'runComand(cnrip=%s,cmd=%s,cpemac=%s,ip=%s,sid=%s)'%(cnrip,cmd,cpemac,ip,sid),'[contents=addfixip2 select cnr_scope_iprange no found scope]'
            #upt_msg['schema'] = getScope_sql
            upt_db('ERROR',str(upt_msg),sid,'none')
            return False
        cnr_shell.sendline('force-lock')
        cnr_shell.expect('nrcmd>', timeout=60)
        cnr_shell.sendline('session set default-format=script')
        cnr_shell.expect('nrcmd>', timeout=60)
        # 由各新scope找尋有效的新ip
        newip = newscope = ''
        for getScopeArray in getScopeArray_rst:
            newscope,result_str = getScopeArray[0],''
            cnr_shell.sendline('scope ' + newscope + ' listleases')
            cnr_shell.expect('nrcmd>', timeout=60)
            result_str = cnr_shell.before
            if  result_str is not None and len(result_str) > 0:
                lineArray = result_str.splitlines()
                for line in lineArray:
                    if  line.find("reserved") >= 0 or line.find("deactivated") >= 0 or line.find("leased") >= 0: # 保留, 關閉, 發放
                        continue
                    else:
                        getIP = re.match(r"^([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}): ", line)
                        if  getIP is not None:
                            newip = getIP.group(1)
                            break
            if  newscope is not None and getIP is not None:
                break
        cnr_shell.sendline('session set default-format=user')
        cnr_shell.expect('nrcmd>', timeout=60)    
        #將新ip及scope，註冊 by pnr restful api
        if newip == '':
            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'runComand(cnrip=%s,cmd=%s,cpemac=%s,ip=%s,sid=%s)'%(cnrip,cmd,cpemac,ip,sid),'[newscope=%s][content=newip is no found]'%(newscope)
            #upt_msg['schema'] = getScope_sql
            upt_db('ERROR',str(upt_msg),sid,'none')
            return False
        else:
            isUsePnr = 1
            if  isUsePnr:
                # pnr
                pnrType = "Reservation"
                cpemac = mac_fmt_conv(cpemac)
                data = {}
                data.update( {"ipaddr":newip,"scope":newscope,"lookupKey":cpemac,"lookupKeyType":"9"} )
                upt_msg['For Reservation'] = "[ip=%s][cpemac=%s][scope=%s][newscope=%s][newip=%s]"%(ip,cpemac,scope,newscope,newip)
                rst = get_request("Reservation",cnrip,pnrType,data,apiuser,apipwd,sid)
                # 結束cmd連線
                cnr_shell.sendline('exit')
                cnr_shell.close()
            else:
                # cnr
                result_str = ''
                cnr_shell.sendline('scope ' + newscope + ' addReservation ' + newip + ' ' + cpemac)
                cnr_shell.expect('nrcmd>', timeout=60)
                result_str = cnr_shell.before
                result_str = result_str.replace(" ","")
                result_str = result_str.replace("'","")
                result_str = result_str.replace(chr(13),"")
                result_str = result_str.strip()
                if  result_str.find("100Ok") >= 0:
                    cnr_shell.sendline('lease ' + newip + ' send-reservation')
                    cnr_shell.expect('nrcmd>', timeout=60)
                    cnr_shell.sendline('save')
                    cnr_shell.expect('nrcmd>', timeout=60)
                    cnr_shell.sendline('dhcp reload')
                    cnr_shell.expect('nrcmd>', timeout=60)
                    cnr_shell.sendline('lease ' + newip + ' force-available')
                    cnr_shell.expect('nrcmd>', timeout=60)
                    cnr_shell.sendline('save')
                    cnr_shell.expect('nrcmd>', timeout=60)
                    cnr_shell.sendline('dhcp reload')
                    cnr_shell.expect('nrcmd>', timeout=60)
                    cnr_shell_txt = ",".join(cnr_shell.before.splitlines())
                    rst = 1
                else:
                    # cpemac綁定123.193.232.69，重覆執行二次時，會發生此錯誤訊息 或 cpemac已綁定IP-69，在同scope再次綁定新IP-241時，會發生此錯誤訊息
                    if  result_str.find("320EX_CONFLICT_EXISTS") >= 0:
                        # 查詢申請ip的 macaddr ，是否等於mac(要先轉成小寫才能比對)
                        cnr_shell.sendline('lease ' + ip + ' get reservation-lookup-key')
                        cnr_shell.expect('nrcmd>', timeout=60)
                        txt = cnr_shell.before
                        txt = txt.replace(" ","")
                        txt = txt.replace("'","")
                        txt = txt.replace(chr(13),"")
                        txt = txt.strip()
                        if  txt.find("100Ok") >= 0:
                            matchMac = mac.lower()
                            if  txt.find(matchMac) >= 0:
                                # 若等於，則將原ip，回寫到policy內
                                rst = 1
                                newip = ip
                            else:
                                failComand = '[macaddr(%s) not equal mac(%s)]'%(txt,matchMac)
                                upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'runComand(cnrip=%s,cmd=%s,cpemac=%s,ip=%s,sid=%s)'%(cnrip,cmd,cpemac,ip,sid),'[contents=cnr addReservation fail][cmd=%s]'%(failComand)
                                rst = 0
                        else:
                            failComand = '[lease ' + ip + ' get reservation-lookup-key => error:' + txt + ']'
                            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'runComand(cnrip=%s,cmd=%s,cpemac=%s,ip=%s,sid=%s)'%(cnrip,cmd,cpemac,ip,sid),'[contents=cnr addReservation fail][cmd=%s]'%(failComand)
                            rst = 0
                    else:
                        failComand = 'scope ' + newscope + ' addReservation ' + newip + ' ' + cpemac
                        upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'runComand(cnrip=%s,cmd=%s,cpemac=%s,ip=%s,sid=%s)'%(cnrip,cmd,cpemac,ip,sid),'[contents=cnr addReservation fail][cmd=%s]'%(failComand)
                        rst = 0
                # 結束cmd連線
                cnr_shell.sendline('exit')
                cnr_shell.close()
            # pnr,cnr addReservation 執行結果    
            if  rst==ip:
                # 解決cpemac重覆綁定問題
                sql_schema = "UPDATE %s SET status='%s',policy='%s',status_date=sysdate,result='%s' WHERE sid = %d" % (pnrTable_DB,'OK',ip,'[解決cpemac重覆綁定問題]cnr api ok by add Reservation',sid)
                upt_db('OK','','',sql_schema)
                return True
            elif  rst:
                sql_schema = "UPDATE %s SET status='%s',policy='%s',status_date=sysdate,result='%s' WHERE sid = %d" % (pnrTable_DB,'OK',newip,'cnr api ok by add Reservation',sid)
                upt_db('OK','','',sql_schema)
                return True
            else:
                upt_db('ERROR',str(upt_msg),sid,'none')
                return False                
    elif cmd=="activeip" or cmd=="deactiveip":
        if  ip is None:
            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'runComand(cnrip=%s,cmd=%s,cpemac=%s,ip=%s,sid=%s)'%(cnrip,cmd,cpemac,ip,sid),'[contents=cmd-activeip,deactiveip require paramter ip]'
            upt_db('ERROR',str(upt_msg),sid,'none')
            return False
        if  cmd=="activeip":
            cnr_shell.sendline('lease ' + ip + ' activate')
        else:
            cnr_shell.sendline('lease ' + ip + ' deactivate')
        cnr_shell.expect('nrcmd>', timeout=60)
        result_str = cnr_shell.before
        result_str = result_str.replace(" ","")
        result_str = result_str.replace("'","")
        result_str = result_str.replace(chr(13),"")
        result_str = result_str.strip()
        if  result_str.find("100Ok") >= 0:
            cnr_shell_txt = ",".join(cnr_shell.before.splitlines())
            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 1,"runComand","[content=cnr OK][cmd=%s]"%(cmd)
            upt_db('OK','cnr command ok',sid,'none')
            # 結束CNR連線
            cnr_shell.sendline('exit')
            cnr_shell.close()
            return True
        else:
            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,"runComand(cnrip=%s,cmd=%s,cpemac=%s,ip=%s,sid=%s)"%(cnrip,cmd,cpemac,ip,sid),"[contents=%s]"%(cnr_shell.before)
            upt_db('ERROR',str(upt_msg),sid,'none')
            # 結束CNR連線
            cnr_shell.sendline('exit')
            cnr_shell.close()
            return False
    else: 
        upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,"runComand(cnrip=%s,cmd=%s,cpemac=%s,ip=%s,sid=%s)"%(cnrip,cmd,cpemac,ip,sid),'[contents=Command must be (addfixip2,activeip,deactiveip)]'
        upt_db('ERROR',str(upt_msg),sid,'none')
        return False
        
def main(pnrID):
    global oracon,upt_msg,pnrTable_DB
    print '# fn-main start[cnrID=%s]'%(pnrID)
    sys.stdout.flush()
    # 訊息
    upt_msg = {'rtn':'','fn':'','info':'','parameters':'','schema':''}

    # db 連接
    oracon = ORA('nms@cnis')
    if  oracon.db is None:
        upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,"main","[contents=DB Connect Faile]"
        print upt_msg
        sys.stdout.flush()
        exit(0)
        
    # 取得 pnr info(ip:master,ip2:slave)
    pnr_info_sql = "SELECT companyno,cnr_id,cnr_id2,ip,ip2,apiuser,apipwd FROM cnr_pnr WHERE stopyn='N' AND companyno IN ('220','230','250') AND (cnr_id='%s' OR cnr_id2='%s') " % (pnrID,pnrID)
    rst = oracon.execall(pnr_info_sql)
    if  len(rst)==0:
        upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,"main","[contents=No PNR INFO][pnrID=%s]"%(pnrID)
        #upt_msg['schema'] = pnr_info_sql
        print upt_msg
        sys.stdout.flush()
        oracon.se_close()
        exit(0);
    companyno,cnr_id,cnr_id2,ip1,ip2,apiuser,apipwd = rst[0][0],rst[0][1],rst[0][2],rst[0][3],rst[0][4],rst[0][5],rst[0][6]
    if  companyno not in ('101','210','220','230','250'):
        upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,"main[CompanyNO=%s]"%(companyno),"[contents=CompanyNO must be in 101,210,220,230,250]"
        print upt_msg
        sys.stdout.flush()
        oracon.se_close()
        exit(0);
    if  ip1 is None or ip2 is None:
        upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,"main[ip=%s][ip2=%s]" %(ip1,ip2),"[contents= Master,Slave IP is required]"
        print upt_msg
        sys.stdout.flush()
        oracon.se_close()
        exit(0);
        
    # 查詢 pnr data
    pnr_data_sql =                                                   \
    "SELECT sid,command,cmmac,policy,ip,cpemac,companyno,subsid FROM \
    (                                                                \
        SELECT sid,command,cmmac,policy,ip,cpemac,companyno,subsid,  \
          CASE                                                       \
          WHEN command='active' AND policy LIKE '%%TV%%'  THEN 1     \
          WHEN command='active' AND policy LIKE '%%STB%%' THEN 2     \
          WHEN command IN ('querymac','querybw') THEN 3 ELSE 1       \
           END seq                                                   \
          FROM %s                                                    \
         WHERE cnr_id = '%s'                                         \
           AND status='INIT'                                         \
           AND companyno IN ('220','230','250')                            \
           AND command IN ('active','modify','delete','addfixip','addfixip2','delfixip','deactiveip','activeip','querymac','querybw','fixpublic','fixprivate','ddos','delddos') \
           AND sysdate >= book_date                                  \
         ORDER BY seq,book_date,sid                                  \
    )WHERE rownum <= 30                                              \
    " % (pnrTable_DB,pnrID)
   
    while 1:
        upt_msg = {'rtn':'','fn':'','info':'','parameters':'','schema':''}
        pnr_data_list = oracon.execall(pnr_data_sql)
        if  len(pnr_data_list) ==0:
            upt_msg['rtn'],upt_msg['info'] = 0,"[contents=Query %s no data please wait 60 seconds]"%(pnrTable_DB)
            #upt_msg['schema'] = pnr_data_sql
            print upt_msg
            sys.stdout.flush()
            time.sleep(60)
            
        else:
            # 執行PNR api or command
            for pnr_data in pnr_data_list:
                sid,cmd,cmmac,policy,ipaddr,cpemac,companyno,subsid = int(pnr_data[0]),pnr_data[1],pnr_data[2],pnr_data[3],pnr_data[4],pnr_data[5],pnr_data[6],pnr_data[7]
                if  cmmac is not None:
                    cmmac  = mac_fmt_conv_2(cmmac)       # 1,6,xx:xx:xx:xx:xx:xx
                if  cpemac is not None:
                    cpemacType1 = mac_fmt_conv(cpemac)   # 01:06:xx:xx:xx:xx:xx:xx (for addfixip)
                    cpemacType2 = mac_fmt_conv_2(cpemac) # 1,6,xx:xx:xx:xx:xx:xx
                # run master,slave by ip1,ip2
                for i in range(2):
                    if  i ==0:
                        cnrip = ip1
                    else:
                        # 若二者ip相同，則不執行
                        if  ip1==ip2:
                            break
                        else:
                            cnrip = ip2
                    # run start
                    upt_msg['parameters'] = "[sid=%s][cmd=%s][cmmac=%s][policy=%s][ipaddr=%s][cpemac=%s][companyno=%s][subsid=%s]" %(sid,cmd,cmmac,policy,ipaddr,cpemac,companyno,subsid)
                    r = False
                    # command mapping request
                    data = {}
                    if  cmd == 'active':
                        # 註冊方案 ：舊 pnrType = "ClientClass";data.update( {"name":cmmac,"policyName":policy} )
                        pnrType = "ClientEntry"
                        param= [{}]
                        param[0].update({"name":cmmac,"clientClassName":policy})
                        r = get_request("put",cnrip,pnrType,param,apiuser,apipwd,sid)
                    elif cmd == 'modify':
                        # 修改方案
                        pnrType = "ClientEntry"
                        param= [{}]
                        param[0].update({"name":cmmac,"clientClassName":policy})
                        r = get_request("put",cnrip,pnrType,param,apiuser,apipwd,sid)
                    elif cmd == 'delete':
                        # 刪除方案
                        pnrType = "ClientEntry/" + cmmac
                        r = get_request("del",cnrip,pnrType,"",apiuser,apipwd,sid)
                    elif cmd == 'addfixip':
                        # 取得： scopename
                        pnrType = "Lease?address=^%s$"%(ipaddr)
                        getData = get_request("get",cnrip,pnrType,'',apiuser,apipwd,sid)
                        try:
                            # 若scopeName存在，則新增 add Reservation
                            getScopename = getData[0]['scopeName']
                            pnrType = "Reservation"
                            param= [{}]
                            param[0].update({"ipaddr":ipaddr,"scope":getScopename,"lookupKey":cpemacType1,"lookupKeyType":"9"})
                            r = get_request("put",cnrip,pnrType,param,apiuser,apipwd,sid)
                        except:
                            # 若scopeName欄位不存在
                            upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,"get_request","[cmd=%s][pnrType=%s][contents=scopeName is not found]"%(cmd,pnrType)
                            r = False
                    elif cmd == 'addfixip2':
                        # 新增：add Reservation
                        r = runComand(cnrip,cmd,cpemac,ipaddr,oracon,sid,apiuser,apipwd)
                    elif cmd == 'activeip':
                        # ip-開啟
                        r = runComand(cnrip,cmd,"",ipaddr,oracon,sid,apiuser,apipwd)
                    elif cmd == 'deactiveip':
                        # ip-關閉
                        r = runComand(cnrip,cmd,"",ipaddr,oracon,sid,apiuser,apipwd)
                    elif cmd == 'delfixip':
                        # 刪除：del Reservation
                        if  ipaddr is None:
                            upt_msg['rtn'],upt_msg['info'] = 0,"[contents=delfixip require paramter ip]"
                            upt_db('ERROR',str(upt_msg),sid,'none')
                        else:
                            pnrType = "Reservation/" + ipaddr
                            r = get_request("del",cnrip,pnrType,"",apiuser,apipwd,sid)
                    elif cmd == 'querymac':
                        # querymac 查詢CMIP/CPEIP的CMMAC/CPEMAC
                        if  ipaddr is None:
                            upt_msg['rtn'],upt_msg['info'] = 0,"[contents=querymac require paramter ip]"
                            upt_db('ERROR',str(upt_msg),sid,'none')
                        else:
                            pnrType = "Lease/" + ipaddr
                            r = get_request("querymac",cnrip,pnrType,"",apiuser,apipwd,sid)
                    elif cmd == 'querybw': 
                        # querybw 查詢CMMAC的PROFILE
                        if  cmmac is None:
                            upt_msg['rtn'],upt_msg['info'] = 0,"[contents=querybw require paramter cmmac]"
                            upt_db('ERROR',str(upt_msg),sid,'none')
                        else:
                            pnrType = "ClientEntry/" + cmmac
                            r = get_request("querybw",cnrip,pnrType,"",apiuser,apipwd,sid)
                    elif cmd == 'fixpublic' or cmd == 'fixprivate':
                        # Scope-PUB 開啟及關閉：ClientEntry 修改 client mac set selection-criteria=Scope-PUB'
                        if  cmmac is None:
                            upt_msg['rtn'],upt_msg['info'] = 0,"[contents=fixpublic,fixprivate require paramter cmmac]"
                            upt_db('ERROR',str(upt_msg),sid,'none')
                        else:
                            # 得先取得 clientClassName即policy(因為update動作是覆蓋，而db的command fixpublic,fixprivate無policy資訊)
                            pnrType = "ClientEntry?name=^%s$"%(cmmac)
                            getData = get_request("get",cnrip,pnrType,"",apiuser,apipwd,sid)
                            policy  = getData[0]['clientClassName']
                            # 執行 pnr 異動
                            param= [{}]
                            param[0].update({"name":cmmac,"clientClassName":policy})
                            if  cmd == 'fixpublic':
                                param[0].update({ "selectionCriteria":{ "stringItem":['Scope-PUB'] } })
                            pnrType = "ClientEntry"
                            r = get_request("put",cnrip,pnrType,param,apiuser,apipwd,sid)
                    elif cmd == 'ddos' or cmd == 'delddos':
                        # ddos 開啟及關閉：ClientEntry 修改 client mac set selection-criteria=Scope-PUB'
                        if  cpemac is None:
                            upt_msg['rtn'],upt_msg['info'] = 0,"[contents=ddos,delddos require paramter cpemac]"
                            upt_db('ERROR',str(upt_msg),sid,'none')
                        else:
                            param= [{}]
                            try:
                                # 得先取得 clientClassName即policy(因為update動作是覆蓋，而db的command ddos,delddos無policy資訊)
                                pnrType = "ClientEntry?name=^%s$"%(cpemacType2)
                                getData = get_request("get",cnrip,pnrType,"",apiuser,apipwd,sid)
                                policy  = getData[0]['clientClassName']
                                param[0].update({"name":cpemacType2,"clientClassName":policy})
                            except:
                                param[0].update({"name":cpemacType2})
                            # 執行 pnr 異動
                            if  cmd == 'ddos':
                                param[0].update({ "selectionCriteria":{ "stringItem":['Scope-ddos'] } })
                            pnrType = "ClientEntry"
                            r = get_request("put",cnrip,pnrType,param,apiuser,apipwd,sid)
                    else:
                        upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,'for[cmd=%s]','[contents=Command must be (active,modify,delete,addfixip,addfixip2,delfixip,deactiveip,activeip,querymac,querybw,fixpublic,fixprivate,ddos,delddos)]'%(cmd)
                    # print Result(command)
                    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                    if  r:
                        print "[%s][OK][sid=%s]"%(nowdate,sid)
                    else:    
                        print "[%s][Error][sid=%s]"%(nowdate,sid)
                        print upt_msg
                    print '****************************************'
                    sys.stdout.flush()

print '##############################################'
print '# 主程式開始'
print '##############################################'
apiuser = apipwd = oracon = None
pnrTable_DB = 'cnr_queue_pnr'
upt_msg = {'rtn':'','fn':'','info':'','parameters':'','schema':''}

# 輸入 cmd PNR_ID(ex.NTP_CNR1_002)
if  len(sys.argv) < 2:
    upt_msg['rtn'],upt_msg['fn'],upt_msg['info'] = 0,"main","[contents=Please input CNR_ID]"
    print upt_msg
    sys.stdout.flush()
    exit(0)
pnrID = sys.argv[1].upper()
try:
    main(pnrID)
except KeyboardInterrupt, e:
    # Ctrl-C
    raise e
except SystemExit, e:
    # sys.exit()
    raise e
except Exception, e:
    nowdate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    msg = re.sub("'",'',str(e))
    print '[%s] Except-05:%s '%(nowdate,msg)
    print upt_msg
    sys.stdout.flush()
    sys.exit()
    
'''測試流程
# 執行  /ap/home/coss/bin/cnr
# 執行  ./pnr_rest_api.sh start 或 pnr_rest_api.py NTP_CNR1_001
  跑迴圈執行 EJ0_CCNR_001 YMS_CNR1_001 NTP_CNR1_001 NTP_CNR1_002 KP_CNR1_001 UC_CNR1_001
              pnr_rest_api.py EJ0_CCNR_001 start 或 pnr_rest_api.py ntp_cnr1_002 start
# 測試資料表：cnr_queue_pnr_tri
# 測試網頁： https://v2.kbro.com.tw/test/davis_test/pnr/pnr_query.php
# 頻道
  永佳樂-101	192.168.136.44 、 192.168.136.45 CNRID => EJ0_CCNR_001,YJL-CNR-01
  陽明山-210	 10.222.16.96  、  10.222.16.97  CNRID => YMS_CPNR_001,YMS_CPNR_002
  新台北-220	 10.222.24.96  、	 10.222.24.97  CNRID => NTP_CNR1_001,NTP-CNR-01,NTP_CNR1_002,NTP-CNR-02 
  金頻道-230	 10.222.32.96  、	 10.222.32.97  CNRID => KP_CNR1_001,KP-CNR-01 
  全聯  -250   10.222.56.96  、  10.222.56.97  CNRID => UC_CNR1_001,UC-CNR-01 

# 頻道開啟
  --DB
    INSERT INTO cnr_pnr SELECT * FROM cnr  WHERE companyno='230'
    UPDATE cnr_pnr SET ip='10.222.32.96',ip2='10.222.32.97' WHERE companyno = '230';  
  --程式309行：新增頻道代碼
    2017/03/01 目前只先執行 220,230 所有頻道=> AND companyno IN ('101','210','220','230','250')
    391行 AND companyno IN ('220','230')
    427行 AND companyno IN ('220','230')
  --SH重啟
    ./pnr_rest_api.sh restart
    ps -ef |grep 'pnr'
  --觀察
    SELECT * FROM cnr_queue_pnr where companyno='230' and status='OK';
    /ap/home/coss/log/cnr/pnr_rest_api_KP_CNR1_001.log
'''
'''連接CNR
   --230金頻道(71)：
     /opt/nwreg3/local/usrbin/nrcmd -C 10.222.32.96  -N provgw -P pv#1176
   --查詢
      client 1,6,00:05:ca:46:bd:9c
   --新增selection-criteria
      client 1,6,00:05:ca:46:bd:9c create selection-criteria=Scope-ddos
   --修改selection-criteria
      client 1,6,00:05:ca:46:bd:9c set selection-criteria=Scope-ddos
   --刪除selection-criteria
      client 1,6,00:05:ca:46:bd:9c unset selection-criteria
'''
'''測試
//新建方案
  update cnr_queue_pnr_tri set command = 'active',cmmac='777df7777b99',policy='ANTCM100M10M-test888',companyno=220,create_date=SYSDATE,book_date=SYSDATE,result='',status='INIT' where sid = '1';
  --測試網頁：
    http://10.222.2.104:8080/web-services/rest/resource/ClientEntry?name=777df7777b99
    備註：若已經有資料，則command，會有 contents=Exception:can't set attribute 錯誤訊息，表示該方案已存在
  
//修改方案
  update cnr_queue_pnr_tri set command = 'modify',cmmac='777df7777b99',policy='ANTCM100M10M-test11a',companyno=220,create_date=SYSDATE,book_date=SYSDATE,result='',status='INIT' where sid = '2';
  --測試網頁：
    http://10.222.2.104:8080/web-services/rest/resource/ClientEntry?name=777df7777b99
  
//刪除方案
  update cnr_queue_pnr_tri set command = 'delete',cmmac='777df7777b99',policy='ANTCM100M10M-test11a',companyno=220,create_date=SYSDATE,book_date=SYSDATE,result='',status='INIT' where sid = '2';
  --測試網頁：應查無資料
    http://10.222.2.104:8080/web-services/rest/resource/ClientEntry?name=777df7777b99
  
//新增：add Reservation
  --先找尋ip
    http://10.222.2.104:8080/web-services/rest/resource/Lease?scopeName=B[1-9]
    [address] => 123.193.190.4
    [flags] => failover-updated
    [scopeName] => ANTK26S500B10
  --測試該scope是否有其他
    http://10.222.2.104:8080/web-services/rest/resource/Scope?name=ANTK26S500B
    [0] = [name] => ANTK26S500B01
    [1] = [name] => ANTK26S500B02
    [2] = [name] => ANTK26S500B03
  給一組新的cpemc
  update cnr_queue_pnr_tri set command = 'addfixip2',ip='123.193.190.4',cpemac='777df7777b66',policy='',companyno=220,create_date=SYSDATE,book_date=SYSDATE,result='',status='INIT' where sid = '1';
  --會找尋到
    For Reservation: [ip=123.193.190.4][cpemac=1,6,77:7d:f7:77:7b:66][scope=ANTK26S500][newscope=ANTK26S500B01][newip=123.194.184.5]  
  --測試網頁：會查詢到新增資料
    http://10.222.2.104:8080/web-services/rest/resource/Reservation?ipaddr=^123.194.184.5$

//ip-開啟
  update cnr_queue_pnr_tri set command = 'activeip',ip='10.95.0.88',cmmac='',policy='',companyno=220,create_date=SYSDATE,book_date=SYSDATE,result='',status='INIT' where sid = '1';
  --測試網頁：狀態會變更
    http://10.222.2.104:8080/web-services/rest/resource/Lease?address=10.95.0.88
    [flags] => reserved

//ip 關閉
  update cnr_queue_pnr_tri set command = 'deactiveip',ip='10.95.0.88',cmmac='',policy='',companyno=220,create_date=SYSDATE,book_date=SYSDATE,result='',status='INIT' where sid = '1';
  --測試網頁：狀態會變更
    [flags] => reserved,deactivated
    
//刪除 del Reservation
  update cnr_queue_pnr_tri set command = 'delfixip',ip='123.194.184.5',cmmac='',policy='',companyno=220,create_date=SYSDATE,book_date=SYSDATE,result='',status='INIT' where sid = '2';
  --測試網頁：應無法查到保留ip的資料
    http://10.222.2.104:8080/web-services/rest/resource/Reservation?ipaddr=^123.194.184.5$
  
//querymac 查詢CMIP/CPEIP的CMMAC/CPEMAC
  update cnr_queue_pnr_tri set command = 'querymac',ip='10.95.0.88',cmmac='',policy='',companyno=220,create_date=SYSDATE,book_date=SYSDATE,result='',status='INIT' where sid = '1';
  --測試網頁：
    http://10.222.2.104:8080/web-services/rest/resource/Lease?address=10.95.0.88
    [relayAgentRemoteId] => 00:06:e0:ac:f1:15:49:d8

//querybw 查詢 CMMAC 的 PROFILE
  update cnr_queue_pnr_tri set command = 'querybw',cmmac='777df7777b99',policy='',companyno=220,create_date=SYSDATE,book_date=SYSDATE,result='',status='INIT' where sid = '2';
  --測試網頁：
    http://10.222.2.104:8080/web-services/rest/resource/ClientEntry?name=777df7777b99
    [clientClassName] => ANTCM100M10M-test11a

//Scope-PUB 開啟
  update cnr_queue_pnr_tri set command = 'fixpublic',cmmac='777df7777b99',policy='ANTCM100M10M-test888',companyno=220,create_date=SYSDATE,book_date=SYSDATE,result='',status='INIT' where sid = '2';
  --測試網頁：
     http://10.222.2.104:8080/web-services/rest/resource/ClientEntry?name=777df7777b99
     [selectionCriteria] => stdClass Object([stringItem] => Array([0] => Scope-PUB))

//Scope-PUB 關閉
  update cnr_queue_pnr_tri set command = 'fixprivate',cmmac='777df7777b99',policy='ANTCM100M10M-test888',companyno=220,create_date=SYSDATE,book_date=SYSDATE,result='',status='INIT' where sid = '2';
  --測試網頁：
     http://10.222.2.104:8080/web-services/rest/resource/ClientEntry?name=777df7777b99
     selectionCriteria 刪除欄位
     
//訊息範本
  {
      "rtn"    : "1",
      "fn"     : "get_request(x=x,z=z)",
      "info"   : "[contents=xx][contents=Exception]",
      "params" : "[return params=xx]",
      "schema" : "",
      "other"  : "xx"
  }    
'''    