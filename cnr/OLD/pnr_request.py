# -*- coding: utf-8 -*-
import time,sys,os,re
import requests,base64,json

# cmd 參數
if len(sys.argv) < 2:
    print 'please input get,post,pull,del parameter'
    exit(0)
else:
    get_rst_objs = []
    method = sys.argv[1]
    
# 函式-request
def get_method_get(method,api_URL,data):
    if method!="get" and method!="post" and method!="put" and method!="del":
        print '{"rst":"0","info":"method error"}'
        exit(0)
    b64Val = base64.b64encode("provgw:pv#1176")
    headers = {"Authorization": "Basic %s" % b64Val,"accept":"application/json"}
    headers.update({"Content-type":"application/json"}) # headers["Content-type"]="application/json"
    if method=="get" :
        r=requests.get(api_URL,headers=headers)
    elif method=="post": 
        r=requests.post(api_URL,headers=headers,data=json.dumps(data))
    elif method=="put": 
        r=requests.put(api_URL,headers=headers,data=json.dumps(data))
    elif method=="del":
        api_URL = api_URL + "/10.95.0.101"
        r=requests.delete(api_URL,headers=headers)
    return r
    
# 函式-nextPage
def get_nextPage(heads_link):
    global get_rst_objs
    ma = re.match('<(http:.+)>;.+rel="(.+)"',heads_link)
    if ma.group(2)=="next":
        result=get_method_get("get",ma.group(1),{})
        return result

# 初始
api_URL = "http://10.222.2.104:8080/web-services/rest/resource/Reservation"
if method=="post":
    data =                                     \
    {                                          \
        "ipaddr":"10.95.0.101",                \
        "lookupKey":"01:06:3c:97:0e:35:49:b0", \
        "scope":"Fixed-IP-B01",                \
        "lookupKeyType":"7",                   \
        "tenantId":"0",                        \
        "vpnId":"0"                            \
    }     
elif method=="put":
    data =                                     \
    [                                          \
     {                                         \
        "ipaddr":"10.95.0.101",                \
        "scope":"Fixed-IP-B01",                \
        "lookupKey":"01:06:3c:97:0e:35:49:aa", \
        "lookupKeyType":"3",                   \
     },{                                       \
        "ipaddr":"10.96.192.19",               \
        "scope":"ANTK24S500Bdefault",          \
        "lookupKeyType":"3",                   \
     }                                          
    ]                                          
    # temp = []
    # temp.append(data)
else:
    data = {}

# 執行
result = get_method_get(method,api_URL,data)

# 結果
print "===Result start==================================================="
rst = 1 if (result.status_code==200 or result.status_code==201) else 0
if rst and method=="get":
    get_rst_objs = json.loads(result.content)
    print len(get_rst_objs)
    print get_rst_objs
else:
    print result.content
print method,api_URL,rst,result.status_code
exit(0)        

'''
# 認證的其他寫法
  from requests.auth import HTTPBasicAuth
  r = requests.post(api_URL, auth=HTTPBasicAuth('user', 'pass'), data=payload)

# post注意事項
  新增時 ipaddr,lookupKey 不能和其他資料重覆，否則無法新增
# put注意事項
  1-objectOid,tenantId修改沒用，值不變
  2-ipaddr 和 scope 二者為搜尋條件
    scopte 不能修改
    ipaddr 單獨輸入(若未填scope，更新後會無該欄位，屆時del會無法刪除該筆ip)
  3-vpnId禁止修改
  4-僅能修改 lookupKey,lookupKeyType
# del注意事項
  若無法刪除，可能是更新時未填 scope，更新後會無該欄位，則 del 會無法刪除該筆ip)
'''