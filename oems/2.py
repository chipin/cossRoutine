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

oracon_nms = ORA('NMS@CNIS')

agent = snmpclass(version='v1',ptimeout=3,pretries=3,debug=0)
kpi_link_offline = 50

p_total_cm = p_online_cm = 0
oraqrysql = "select subsid,cmmac,ip,idx,cmts_ip,snmp_ro from v_cnis_cmmac_intf where companyno='420' \
and subsid in ('13003559','4578126','4578127','13003560','13035440','13097272','4799301','4824789','4824790','4992879','4992880','13003414','13003562','4669982','4669983', \
'4709930','4709934','4838751','4985597','13003561','13003568','13060910','13098904','4749677','4790661','4892157', \
'4904249','4904250','4912128','4917106','4920330','4932563','4946900','4952115','4957148','4957150','13003412', \
'13003415','13003565','13003567','13005816','13058102','13096958','13108415','4500961','4501176','4597844', \
'4732528','4747058','4749090','4818130','4849030','4849956','4853846','4856643','4856644','4896105','4896106','4921944','4939008','4959410','13002906', \
'13003411','13003413','13003422','13009303','13011830','13016780','13024680','13047704','13058105','13058107','13058109','13078454','13085393','13085478','13107099')"
print oraqrysql
rs = oracon_nms.execall(oraqrysql)
if rs != None and len(rs) > 0:
    for a_row in rs:
        p_subsid = int(a_row[0])
        p_cmmac = a_row[1]
        p_cmip = a_row[2]
        p_cmidx = int(a_row[3])
        p_cmtsip = a_row[4]
        p_snmpro = a_row[5]
        p_cmoid = '.1.3.6.1.2.1.10.127.1.3.3.1.9.' + str(p_cmidx)

        rets = agent.snmpget([p_cmtsip, '-c', p_snmpro, p_cmoid])
        print p_subsid,p_cmmac,p_cmip,rets
        if rets is not None and rets[0][1]!='':
            p_online = int(rets[0][1])
            if p_online == 6:
                p_online_cm = p_online_cm+1
        p_total_cm = p_total_cm+1

if p_total_cm > 0 and p_online_cm > 0:
    p_online_cm = float(p_online_cm)
    p_total_cm = float(p_total_cm)
    p_offline = round(100-(p_online_cm*100/p_total_cm),2)

    print p_offline,kpi_link_offline

    if p_offline >= kpi_link_offline:
        print "離線率 %s%% 已達KPI %s%% => ALARM" % (p_offline, kpi_link_offline)
    else:
        print "離線率 %s%% 未達KPI %s%%  => PASS" % (p_offline, kpi_link_offline)
