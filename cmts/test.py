import os,sys,time
import cossdb,pymssql
from oraclass import ORA

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

con = pymssql.connect(host='TFMCossMS_HUGE',user=cossdb.account,password=cossdb.passwd,database='cossdb')

cur = con.cursor()

qry = "select top 1 subsname,custstatus from ms0200 with(nolock) where subsid='471301'"
cur.execute(qry)
workarr = cur.fetchall()
for wrk in workarr:
    subsname = wrk[0]
    custstatus = wrk[1]
    print subsname
    print custstatus


