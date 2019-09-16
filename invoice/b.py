#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys,time,re
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

email = 'a1@t1.t1x11--'

if re.match(r"^.{2,}@[^.]{2,}\.[^.]{2,}", email) is not None:
  print 'YES'
else:
  print 'NO'
