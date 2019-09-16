#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

oracon = ORA('nms@cnis')
if not oracon.db:
    sys.exit(0)

rs = oracon.execone("update cmts set mflag=1 where stopyn='N'")
rs = oracon.execone("update ip_ne set mflag=1 where stopyn='N'")
rs = oracon.execone("update dtv_ne set mflag=1 where stopyn='N'")
oracon.commit()

if oracon.db:
    oracon.se_close()
