#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
import cossdb,pymssql
from oraclass import ORA
from pysnmpclass import snmpclass

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

oracon_oems = ORA('OEMS@KBRO_NMSDB')
oraupdsql = "update kpi_coss_bomb set stopyn='Y' where name='NODE+LINK'"
oracon_oems.execone(oraupdsql)
oracon_oems.commit()
oraqrysql = '''
    SELECT name,node_day,node_hour,link_day,link_hour,offline_rate,operator,stopyn
      FROM kpi_coss_bomb
     WHERE name IN('Nature','NODE+LINK','NODE')
'''
rs = oracon_oems.execall(oraqrysql)
kpiBomb = {}
if  rs!=None and len(rs) > 0:
    for row in rs:
        name = row[0]
        kpiBomb[name] = {}
        kpiBomb[name]['stopyn'] = row[7]
        if  name=='Nature':
            kpiBomb[name]['operator'] = row[6]      if(row[6]) else ''
            kpiBomb[name]['nodeDays'] = int(row[1]) if(row[1]) else default_nodeDays
            kpiBomb[name]['nodeHour'] = int(row[2]) if(row[2]) else default_nodeHour
        elif name=='NODE+LINK':
            kpiBomb[name]['nodeDays'] = int(row[1]) if(row[1]) else default_nodeDays
            kpiBomb[name]['nodeHour'] = int(row[2]) if(row[2]) else default_nodeHour
            kpiBomb[name]['linkDays'] = int(row[3]) if(row[3]) else default_linkDays
            kpiBomb[name]['linkHour'] = int(row[4]) if(row[4]) else default_linkHour
            kpiBomb[name]['OffRate']  = int(row[5]) if(row[5]) else default_OffRate
        elif name=='NODE':
            kpiBomb[name]['nodeDays'] = int(row[1]) if(row[1]) else default_nodeDays
            kpiBomb[name]['nodeHour'] = int(row[2]) if(row[2]) else default_nodeHour
        elif name=='Offline':
            kpiBomb[name]['operator'] = row[6]      if(row[6]) else ''
print 'Alarm condition:',kpiBomb
