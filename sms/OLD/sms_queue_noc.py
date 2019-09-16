#!/usr/bin/env python
# -*- coding: Big5 -*-
import sys,time,string,urllib,httplib
from oraclass import ORA

http_response = None
http_server_c = None

sms_id = ''
sms_result = ''
sms_count = 0

def send_sms_ite2(to, msg):
        global http_server_c, http_response, sms_id, sms_count
        try:
            xmsg = string.replace(msg,'#','-')
            xmsg = xmsg.replace('<','(')
            xmsg = xmsg.replace('>',')')
            durl = 'http://tools.ite2.com.tw/scripts/fpcgi.dll?cateid=1&proid=0&user=kbro&pass=kbro&to=%s&text=%s' % (to,urllib.quote(xmsg))
            sys.stdout.flush()
            if http_server_c is None:
                http_server_c = httplib.HTTPConnection("tools.ite2.com.tw",80)
                http_server_c.connect()
            else:
                http_server_c.connect()
            http_server_c.request('GET',durl)
            xx = http_server_c.getresponse()
            http_response = xx.read()
            try:
                sms_count = 0
                result_tmp = http_response.split('<SEQ>')
                if len(result_tmp)==2:
                    sms_id = result_tmp[1].split('</SEQ>')[0]
                    sms_count = 1
                elif len(result_tmp)>2:
                    sms_count = len(result_tmp)-1
                    sms_id = result_tmp[1].split('</SEQ>')[0]
                else:
                    sms_id = '0'
            except Exception, detail:
                sms_id = '0'
            xx.close()
            http_server_c.close()
            http_server_c = None
            return 'OK'
        except Exception, detail:
            pass
            if http_server_c is not None:
                try:
                    http_server_c.close()
                    http_server_c = None
                except:
                    pass
                    http_server_c = None
            return str(detail)[0:127]

def send_sms_ite2_acc2(to, msg):
        global http_server_c, http_response, sms_id, sms_count
        try:
            xmsg = string.replace(msg,'#','-')
            xmsg = xmsg.replace('<','(')
            xmsg = xmsg.replace('>',')')
            xmsg = unicode(xmsg,"cp950").encode("utf-8")
            durl = 'http://ep1.ite2.com.tw/scripts/fpcgi.aspx?user=kbro&pass=kbro2010&to=%s&text=%s' % (to,urllib.quote(xmsg))
            sys.stdout.flush()
            if http_server_c is None:
                http_server_c = httplib.HTTPConnection("ep1.ite2.com.tw",80)
                http_server_c.connect()
            else:
                http_server_c.connect()
            http_server_c.request('GET',durl)
            xx = http_server_c.getresponse()
            http_response = xx.read()
            try:
                sms_count = 0
                try:
                    xerr = http_response.split('<ERR>')[1].split('</ERR>')[0]
                except:
                    xerr = 'sys'
                    pass
                if xerr=='0':
                    result_tmp = http_response.split('<SEQ>')
                    if len(result_tmp)==2:
                        sms_id = result_tmp[1].split('</SEQ>')[0]
                        sms_count = 1
                    elif len(result_tmp)>2:
                        sms_count = len(result_tmp)-1
                        sms_id = result_tmp[1].split('</SEQ>')[0]
                    else:
                        sms_id = '0'
                else:
                    return '[Error]: %s' % (xerr)
            except Exception, detail:
                sms_id = '0'
                pass
            xx.close()
            http_server_c.close()
            http_server_c = None
            return 'OK'
        except Exception, detail:
            pass
            if http_server_c is not None:
                try:
                    http_server_c.close()
                    http_server_c = None
                except:
                    pass
                    http_server_c = None
            return str(detail)[0:127]

def get_sms_ite2(msgid):
        global http_server_c, http_response, sms_result
        try:
            durl = 'http://tools.ite2.com.tw/scripts/fpcgi.dll?user=kbro&pass=kbro&seq_no=%s' % (msgid)
            sys.stdout.flush()
            if http_server_c is None:
                http_server_c = httplib.HTTPConnection("tools.ite2.com.tw",80)
                http_server_c.connect()
            else:
                http_server_c.connect()
            http_server_c.request('GET',durl)
            xx = http_server_c.getresponse()
            http_response = xx.read()
            print http_response
            try:
                sms_result = http_response.split('<RES>')[1].split('</RES>')[0]
            except Exception, detail:
                print detail
                sms_result = ''
            xx.close()
            http_server_c.close()
            http_server_c = None
            return sms_result
        except Exception, detail:
            print detail
            pass
            if http_server_c is not None:
                try:
                    http_server_c.close()
                    http_server_c = None
                except:
                    pass
                    http_server_c = None
            return ''

def get_sms_ite2_acc2(msgid):
        global http_server_c, http_response, sms_result
        try:
            durl = 'http://ep1.ite2.com.tw/scripts/fpcheck.aspx?user=kbro&pass=kbro2010&seq_no=%s' % (msgid)
            sys.stdout.flush()
            if http_server_c is None:
                http_server_c = httplib.HTTPConnection("ep1.ite2.com.tw",80)
                http_server_c.connect()
            else:
                http_server_c.connect()
            http_server_c.request('GET',durl)
            xx = http_server_c.getresponse()
            http_response = xx.read()
            print http_response
            try:
                sms_result = http_response.split('<RES>')[1].split('</RES>')[0]
            except Exception, detail:
                sms_result = ''
                pass
            xx.close()
            http_server_c.close()
            http_server_c = None
            return sms_result
        except Exception, detail:
            print detail
            pass
            if http_server_c is not None:
                try:
                    http_server_c.close()
                    http_server_c = None
                except:
                    pass
                    http_server_c = None
            return ''

querySQL = "select sid,sender,target,msg,sys,eq_type from oss_sms where operator='ITE2' and status='INIT' and sysdate >= sendtime and sendtime >= sysdate-2 and sys in ('NOC','IT') order by sid"
resultSQL = "select sid,msgid,sys,eq_type from oss_sms where operator='ITE2' and status='OK' and sys in ('NOC','IT') and sent not in ('OK','ok') and status_date < sysdate -2/24 and real_sendtime > sysdate -4 and rownum<=100 order by sid"
updateSql = "UPDATE oss_sms SET status=upper(:1),status_date=sysdate,real_sendtime=sysdate,result=:2,msgid=:3,cnt=:4 WHERE sid=:5"
update_resultSql = "UPDATE oss_sms SET sent=upper(:1),status_date=sysdate WHERE sid=:2"

loop = 1
oracon = None
while 1:
    try:
        oracon = ORA('coss/coss@KBRO_NMSDB')
        if oracon is None:
            print "[Oracle Info]: Can't open database"+chr(10)
            time.sleep(10);
            continue
        try:
            rst = oracon.execall(querySQL)
        except:
            print "[Oracle Info]: Can't execute SQL"+chr(10)
            oracon.se_close()
            oracon = None
            time.sleep(10);
            continue
        if rst is not None and len(rst)>0:
            for aw in rst:
                tme = time.strftime("%Y/%m/%d %H-%M-%S", time.localtime())
                sid = aw[0]
                sender = aw[1]
                target = aw[2]
                msg = aw[3]
                sysname = aw[4]
                eq_type = aw[5]
                if eq_type=='N':
                    result = send_sms_ite2_acc2(target, msg)
                else:
                    result = send_sms_ite2(target, msg)
                if result=='OK':
                    update_param=(['OK', http_response, sms_id, sms_count, sid],)
                else:
                    update_param=(['ERROR', result, '0', 0, sid],)
                print sid,result,http_response
                oracon.updateone(updateSql, update_param)
                oracon.commit()
                sys.stdout.flush()
        else:
            print 'Getting result...'
            sys.stdout.flush()
            try:
                rst = oracon.execall(resultSQL)
            except:
                print "[Oracle Info]: Can't execute SQL"+chr(10)
                oracon.se_close()
                oracon = None
                time.sleep(10);
                continue
            if rst is not None and len(rst)>0:
                for aw in rst:
                    sid = aw[0]
                    msgid = aw[1]
                    sysname = aw[2]
                    eq_type = aw[3]
                    print sid, msgid,
                    sms_result = ''
                    if eq_type=='N':
                        sms_result = get_sms_ite2_acc2(msgid)
                    else:
                        sms_result = get_sms_ite2(msgid)
                    print sms_result
                    update_param=([sms_result, sid],)
                    oracon.updateone(update_resultSql, update_param)
                    oracon.commit()
                    sys.stdout.flush()
        oracon.se_close()
        oracon = None
        print 'sleep 5 seconds'
        sys.stdout.flush()
        time.sleep(5)
        loop = loop+1
    except Exception, detail:
        print "Exception: %s" % (detail)
        if oracon is not None:
            oracon.se_close()
            oracon = None
        continue
if http_server_c is not None:
    http_server_c.close()
sys.exit()
