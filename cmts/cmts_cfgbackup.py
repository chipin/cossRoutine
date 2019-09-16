#!/usr/local/bin/python
# -*- coding: BIG5 -*-
# Written by Swallow 2011.05.19
import os,sys,time
import shutil
from telnetlib import Telnet
from oraclass import ORA

tftp_server = '123.193.111.90'
tftp_home   = '/tftpboot/'

print 'Startime: ' + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()) + "\n"

# 先從DB撈出所有的資料, 減少連結DB, 放至Array + Dictionary中
CMTS = []

try:
  oracon = ORA('nms_cm/nms_cm@nmsdb')
  rs = oracon.execall("select SO,upper(CMTS_ID) as CMTS_ID,upper(TYPE) as TYPE,IP,passwd1,passwd2 from cmts where ip is not null and mflag = 0 order by so,cmts_id")
  if rs != None and len(rs) > 0:
    for row in rs:
      data = {}
      data = {'so':row[0], 'cmts_id':row[1], 'type':row[2], 'ip':row[3], 'pwd1':row[4], 'pwd2':row[5]}
      CMTS.append(data)
  oracon.se_close()
except:
  print "Except ORA"


# Telnet + TFTP backup running-config
for data in CMTS:
  print "SO: " + data['so'] + ", CMTS_ID: " + data['cmts_id'] + ", TYPE: " + data['type'] + ", IP: " + data['ip'] + ", Time: " + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())

  # Create DIR
  if (os.path.isdir(tftp_home + data['so']) != True):
    os.mkdir(tftp_home + data['so'])
    print 'mkdir: ' + tftp_home + data['so']
  if (os.path.isdir(tftp_home + data['so'] + '/' + data['cmts_id']) != True):
    os.mkdir(tftp_home + data['so'] + '/' + data['cmts_id'])
    print 'mkdir: ' + tftp_home + data['so'] + '/' + data['cmts_id']

  filename = data['cmts_id'] + '_' + time.strftime("%Y%m%d",time.localtime()) + '.cfg'
  print 'file:  ' + filename

  if (data['type'].find('UBR') > -1):
    try:
      tn = Telnet()
      tn.open(data['ip'], 23)
      tn.read_until('Password:', 10)
      tn.write(data['pwd1'] + "\n")
      tn.read_until('>', 10)
      tn.write('en' + "\n")
      tn.read_until('Password:', 10)
      tn.write(data['pwd2'] + "\n")
      tn.read_until('#', 10)

      if (data['so'] == '106'): # UBR-7246 or UBR10K iOS比較舊, 不能加all
        tn.write('copy running-config tftp://' + tftp_server + '/' + filename + "\n")
      else:
        tn.write('copy running-config tftp://' + tftp_server + '/' + filename + ' all' + "\n")
      tn.write("\n")
      tn.write("\n")
      tn.read_until('#', 60)

      tn.close()
    except:
      print 'Except Telnet'

  elif (data['type'].find('CUDA') > -1):
    try:
      tn = Telnet()
      tn.open(data['ip'], 23)
      tn.read_until('>', 10)
      tn.write('enable root' + "\n")
      tn.read_until('password:', 10)
      tn.write(data['pwd1'] + "\n")
      tn.read_until('#', 10)

      tn.write('copy running-config tftp://' + tftp_server + '/' + filename + "\n")
      tn.read_until('#', 60)

      tn.close()
    except:
      print 'Except Telnet'

  elif (data['type'].find('CASA') > -1):
    try:
      tn = Telnet()
      tn.open(data['ip'], 23)
      tn.read_until('login:', 10)
      tn.write('root' + "\n")
      tn.read_until('Password:', 10)
      tn.write(data['pwd1'] + "\n")
      tn.read_until('>', 10)
      tn.write('en' + "\n")
      tn.read_until('Password:', 10)
      tn.write(data['pwd2'] + "\n")
      tn.read_until('#', 10)

      tn.write('copy nvram startup-config tftp ' + tftp_server + ' ' + filename + "\n")
      tn.read_until('#', 60)

      tn.close()
    except:
      print 'Except Telnet'

  else:
    print 'unknown model'

  time.sleep(1)
  if (os.path.isfile(tftp_home + filename) == True):
    if (os.path.getsize(tftp_home + filename) > 0):
      shutil.move(tftp_home + filename, tftp_home + data['so'] + '/' + data['cmts_id'])
      print 'Backup Success'
    else:
      print 'Backup Failure (!size)'
  else:
    print 'Backup Failure (!file)'

  print ""

print 'Endtime: ' + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
