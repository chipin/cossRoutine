#!/usr/bin/env python
# -*- coding: big5 -*-
import sys, time, string, locale
from suds.client import Client

url = 'http://172.16.13.30/TWM_AXIS/axis2/services/ForwardAlarm?wsdl'

print sys.getdefaultencoding()

reload(sys)

sys.setdefaultencoding('utf-8')
print sys.getdefaultencoding()

sys.setdefaultencoding('ascii')
print sys.getdefaultencoding()

encoded = "<alarm>\n<objectName> 我_G_NeiHu-1_CLI7K01_module-3_card-12_E1_port-11 </objectName>\n" + \
            "<alarmName> interface_down </alarmName>\n" + \
            "<severity> critical </severity>\n" + \
            "<probableCause> process failure </probableCause>\n" + \
            "<description> Fault condition has been detected. Check the failure cause of the link. </description>\n" + \
            "<eventDateTime> 2009/04/10 12:30:44 </eventDateTime>\n" + \
            "<alarmNumber> 2896 </alarmNumber>\n" + \
            "<system> ATM15K </system>\n" + \
            "<networkElement> CLI7K01 </networkElement>\n" + \
            "<module> module-3 </module>\n" + \
            "<neGroup> ATM </neGroup>\n</alarm>"

print encoded
encoded = encoded.decode('big5')
encoded = encoded.encode('utf-8')
#print encoded

#client = Client(url, location=url, timeout=10, headers={'Content-Type':'text/xml; charset=utf-8'})
#client = Client(url, location=url, timeout=10, headers={'Content-Type':'text/xml; charset=big5'})
#client = Client(url, location=url, timeout=10)
#print client

#result = client.service.ForwardAlarm(encoded)
#print result


#http://www.vimer.cn/2010/09/%E3%80%90%E6%80%BB%E7%BB%93%E3%80%91%E7%BE%8E%E5%8C%96bashpython%E7%9A%84soap-clientpython%E8%8E%B7%E5%8F%96%E7%B3%BB%E7%BB%9F%E7%BC%96%E7%A0%81%E5%87%BD%E6%95%B0.html
update cmmac_twm set errortime=sysdate,ceasetime=NULL,oems_id='240345',twm_status='OK',twm_xml='<alarm><objectName>SubsID: 4877055</objectName><alarmName>CM Status: Offline</alarmName><severity>Critical</severity><probableCause>N/A</probableCause><description>SO:新頻道, SubsID:4877055, MAC:0050BFCE5BC8, NODE:CL030, LINK:CL030-01, ADDR:彰化縣鹿港鎮民權路110號, STATUS:Offline</description><eventDateTime>2012/04/17 00:43:47</eventDateTime><alarmNumber>OEMSID: 240345</alarmNumber><system>MSO: 凱擘</system><networkElement>SO: 新頻道</networkElement><module>CM</module><neGroup>CM</neGroup></alarm>' where companyno='420' and subsid='4877055'
