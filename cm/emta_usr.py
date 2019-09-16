#!/usr/bin/env python
# -*- coding: utf-8 -*-
from oraclass import ORA
import time
import telnetlib,string,sys
import socket,array


#print "RETCODE = -1 帳號申請中，暫無法提供Soft Switch資訊。"
#sys.exit()

mac=string.lower(sys.argv[1])
tid=sys.argv[2]
suss_flag = 0
supp_mapping = {}

def login_mml(tn):
  #tn.write('lgi:op="ProvChipin",PWD="chipin123";\n')
  tn.write('lgi:op="tfmcnisprov",PWD="34erdfcv";\n')
  rst = tn.read_until('END',20)
  rett=0
  if string.find(rst,"RETCODE = 0")>0:
    rett=1
  else:
    rett=rst
  return rett

def gocmd_MML(tn,cmdstr):
  tn.write(cmdstr + "\n")
  rst=tn.read_until('END',20)
  rst = rst.replace("\r","")
  return rst

def sendMML(tln,smml):
  retstr = gocmd_MML(tln, smml)
  if string.find(retstr,"RETCODE = 0")<=0:
      retstr1 = "ERROR"+retstr
  else:
      retstr1 = retstr
  return retstr1

def match_supp(tk, idx):
  global suss_flag
  tok = tk.split('=')
  token = tok[1].replace(" ","")
  try:
      suppstr = supp_mapping[token]
  except:
      suppstr = token
  if idx==0:
      print "SUSS="+suppstr ,
      suss_flag = 1
  elif idx==1:
      print ','+suppstr,
  elif idx==2:
      if suss_flag!=0:
          print ""
          suss_flag = 0

def match_token(tk):
  global suss_flag
  tok = tk.split('=')
  if tk.find("Equipment ID")>=0:
      print "EID="+tok[1]
  elif tk.find("Local DN set")>=0:
      print "LAC="+tok[1]
  elif tk.find("Subscriber number")>=0:
      print "DN="+tok[1]
  elif tk.find("FCCU module number")>=0:
      print "MN="+tok[1]
  elif tk.find("Number state")>=0:
      print "State="+tok[1]
  elif tk.find("Subscriber status")>=0:
      print "Status="+tok[1]
  elif tk.find("Port type")>=0:
      print "Ptype="+tok[1]
  elif tk.find("Call source code")>=0:
      print "CSC="+tok[1]
  elif tk.find("Codec prefer")>=0:
      print "Codec="+tok[1]
  elif tk.find("Supplementary service")>=0:
      match_supp(tk, 0)
  elif tk.find("Extended supplementary service")>=0:
      match_supp(tk, 1)
  elif tk.find("Call-out password")>=0:
      match_supp(tk, 2)
      print "Call-out-pw="+tok[1]
  elif tk.find("Super do not disturb password")>=0:
      match_supp(tk, 2)
      print "super-not-disturb-pw="+tok[1]
  elif suss_flag!=0:
      match_supp(tk, 1)

querySql = "SELECT tmp, chn_name FROM voip_supp_mapping@wqs"
oracon = ORA('CMMS@TFM_NMSDB')
if oracon.cexist():
   rs = oracon.execall(querySql)
   if rs is not None and len(rs) > 0:
       for a_row in rs:
           supp_mapping[a_row[0]] = a_row[1]
           
mmtln = telnetlib.Telnet("10.32.10.211",6000)
login_ok = -1
login_ok = login_mml(mmtln)
print login_ok

oracon.se_close()
