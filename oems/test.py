#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time
import threading
import binascii
from oraclass import ORA
from pysnmpclass import snmpclass

db_sid = (int)((time.time()/3600)%4800)
print 'time:',time.time()
print 'dbsid',db_sid

target_sid = (int)((time.time()/3600)%168)
print 'target',target_sid

mac='68B6FCE65DB0'
mac_b = binascii.unhexlify(mac)
mac1 = ord(mac_b[0])
mac2 = ord(mac_b[1])
mac3 = ord(mac_b[2])
mac4 = ord(mac_b[3])
mac5 = ord(mac_b[4])
mac6 = ord(mac_b[5])
print mac1,mac2,mac3,mac4,mac5,mac6
