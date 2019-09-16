#!/usr/bin/env python
# -*- coding: big5 -*-
import sys,re
import os
import struct
import array
import time
import math
import string

#print len(unicode('台灣大寬頻123','big5'))
#print len('台灣大寬頻123'.decode('big5'))
#print len('台灣大寬頻123')


str='1台灣2111'
strlen = len(str.decode('big5'))
strcnt = int(strlen/2)
if strlen%2 > 0:
    strcnt = strcnt + 1
print str,strlen,strcnt

for i in range(0, strcnt):
    j = i * 2
    k = (i+1) * 2
    #aa = str.decode('big5')[j:k].encode('big5')
    aa = str.decode('big5')[i * 2:(i+1) * 2].encode('big5')

    header = "%%05%%00%%03%%C7%%%02d%%%02d" % (strcnt, i + 1)
    print header,aa

#for($m = 0; $m < count($smesg); $m++) {
#  $header = '%05%00%03%C7%' . sprintf("%02d", count($smesg)) . '%' . sprintf("%02d", $m+1); // Header
#  $msg = $msg . $header . urlencode(iconv('UTF-8', 'BIG-5', $smesg[$m]));
#}


xx="msgid=18067062,statuscode=0,statusstr=ParseOK,point=20"

#xx1 = xx.replace(chr(10),'*')
#print xx1
print xx

mat=''
ma = re.search(r"msgid=([0-9]+)", xx)
if ma is not None:
    mat = ma.group(1)
print mat

print xx
mat2 = 0
ma2 = re.search(r"point=([0-9]+)", xx)
if ma2 is not None:
    mat2 = ma2.group(1)
print mat2
