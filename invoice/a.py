#!/usr/bin/env python
import os,sys,time,re
import cossdb,pymssql
from oraclass import ORA

oracti = ORA('icare@cti')
if not oracti.db:
    print 'Error: Unable to connect to [ICARE@CTI]'
    sys.exit(0)
else:
    print 'YES'


a = '  123  '
a = 'qwer78944@yahoo.com.tw                            '
print '>'+a.lower().strip()+'<'
